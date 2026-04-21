import json
from evaluation_function_utils.errors import EvaluationException

from .tools import commands, docs, parse, validate
from .tools.parse import ParseError
from typing import Any, Optional

from .tools.utils import DocsResponse, ErrorResponse, HandlerResponse, JsonType, Response
from .tools.validate import (
    LegacyReqBodyValidators,
    LegacyResBodyValidators,
    MuEdReqBodyValidators,
    MuEdResBodyValidators,
    ValidationError,
)


def handle_legacy_command(event: JsonType, command: str) -> HandlerResponse:
    """Switch case for handling different command options using legacy schemas.

    Args:
        event (JsonType): The AWS Lambda event recieved by the handler.
        command (str): The name of the function to invoke.

    Returns:
        HandlerResponse: The response object returned by the handler.
    """
    # No validation of the doc commands.
    if command in ("docs-dev", "docs"):
        return docs.dev()

    elif command == "docs-user":
        return docs.user()

    body = parse.body(event)
    response: Response
    validator: LegacyResBodyValidators

    if command in ("eval", "grade"):
        validate.body(body, LegacyReqBodyValidators.EVALUATION)
        response = commands.evaluate(body)
        validator = LegacyResBodyValidators.EVALUATION

    elif command == "preview":
        validate.body(body, LegacyReqBodyValidators.PREVIEW)
        response = commands.preview(body)
        validator = LegacyResBodyValidators.PREVIEW

    elif command == "healthcheck":
        response = commands.healthcheck()
        validator = LegacyResBodyValidators.HEALTHCHECK

    else:
        response = Response(
            error=ErrorResponse(message=f"Unknown command '{command}'.")
        )
        validator = LegacyResBodyValidators.EVALUATION

    validate.body(response, validator)

    return response


def wrap_muEd_response(body: Any, event: JsonType, status_code: int = 200) -> DocsResponse:
    """Wrap a muEd response body in Lambda proxy format with X-Api-Version header.

    Args:
        body: The response body to serialise.
        event (JsonType): The incoming event (used to resolve the served version).
        status_code (int): The HTTP status code. Defaults to 200.

    Returns:
        DocsResponse: Proxy-format response with X-Api-Version header set.
    """
    requested = (event.get("headers") or {}).get("X-Api-Version")
    if requested and requested in commands.SUPPORTED_MUED_VERSIONS:
        version = requested
    else:
        version = commands.SUPPORTED_MUED_VERSIONS[-1]
    return DocsResponse(
        statusCode=status_code,
        headers={"X-Api-Version": version},
        body=json.dumps(body),
        isBase64Encoded=False,
    )


def check_muEd_version(event: JsonType) -> Optional[HandlerResponse]:
    """Check the X-Api-Version header against supported muEd versions.

    Args:
        event (JsonType): The AWS Lambda event received by the handler.

    Returns:
        Optional[HandlerResponse]: A version-not-supported error response if
        the requested version is unsupported, otherwise None.
    """
    version = (event.get("headers") or {}).get("X-Api-Version")
    if version and version not in commands.SUPPORTED_MUED_VERSIONS:
        return {
            "title": "API version not supported",
            "message": (
                f"The requested API version '{version}' is not supported. "
                f"Supported versions are: {commands.SUPPORTED_MUED_VERSIONS}."
            ),
            "code": "VERSION_NOT_SUPPORTED",
            "details": {
                "requestedVersion": version,
                "supportedVersions": commands.SUPPORTED_MUED_VERSIONS,
            },
        }
    return None


def handle_muEd_command(event: JsonType, command: str) -> HandlerResponse:
    """Switch case for handling different command options using muEd schemas.

    Args:
        event (JsonType): The AWS Lambda event recieved by the handler.
        command (str): The name of the function to invoke.

    Returns:
        HandlerResponse: The response object returned by the handler.
    """
    try:
        version_error = check_muEd_version(event)
        if version_error:
            return wrap_muEd_response(version_error, event, 406)

        if command == "eval":
            body = parse.body(event)
            validate.body(body, MuEdReqBodyValidators.EVALUATION)
            response = commands.evaluate_muEd(body)
            validate.body(response, MuEdResBodyValidators.EVALUATION)

        elif command == "healthcheck":
            response = commands.healthcheck_muEd()
            validate.body(response, MuEdResBodyValidators.HEALTHCHECK)

        else:
            error = {
                "title": "Not implemented",
                "message": f"Unknown command '{command}'.",
                "code": "NOT_IMPLEMENTED",
            }
            return wrap_muEd_response(error, event, 501)

        return wrap_muEd_response(response, event)

    except (ParseError, ValidationError) as e:
        error = {
            "title": "Bad request",
            "message": e.message,
            "code": "VALIDATION_ERROR",
            "details": {"error": str(e.error_thrown)} if e.error_thrown else None,
        }
        return wrap_muEd_response(error, event, 400)

    except EvaluationException as e:
        detail = str(e) if str(e) else repr(e)
        error = {"title": "Internal server error", "message": detail, "code": "INTERNAL_ERROR"}
        return wrap_muEd_response(error, event, 500)

    except Exception as e:
        detail = str(e) if str(e) else repr(e)
        error = {"title": "Internal server error", "message": detail, "code": "INTERNAL_ERROR"}
        return wrap_muEd_response(error, event, 500)


def handler(event: JsonType, _=None) -> HandlerResponse:
    """Main function invoked by AWS Lambda to handle incoming requests.

    Args:
        event (JsonType): The AWS Lambda event received by the gateway.
        _ (JsonType): The AWS Lambda context object (unused).

    Returns:
        HandlerResponse: The response to return back to the requestor.
    """
    if _ is None:
        _ = {}

    # Normalise path: prefer rawPath (HTTP API v2) over path (REST API v1).
    # API Gateway v1 includes the full resource prefix in `path`
    # (e.g. /compareExpressions-staging/evaluate), so we match on suffix.
    # API Gateway v2 uses `rawPath` at the top level; `path` may be absent.
    raw_path = event.get("rawPath") or event.get("path", "/")
    if raw_path.endswith("/evaluate/health"):
        path = "/evaluate/health"
    elif raw_path.endswith("/evaluate"):
        path = "/evaluate"
    else:
        path = raw_path

    try:
        if path == "/evaluate":
            return handle_muEd_command(event, "eval")

        elif path == "/evaluate/health":
            return handle_muEd_command(event, "healthcheck")

        else:
            headers = event.get("headers", dict())
            command = headers.get("command", "eval")
            return handle_legacy_command(event, command)

    except (ParseError, ValidationError) as e:
        error = ErrorResponse(message=e.message, detail=e.error_thrown)

    except EvaluationException as e:
        error = e.error_dict

    # Catch-all for any unexpected errors.
    except Exception as e:
        error = ErrorResponse(
            message="An exception was raised while "
            "executing the evaluation function.",
            detail=(str(e) if str(e) != "" else repr(e)),
        )

    return Response(error=error)
