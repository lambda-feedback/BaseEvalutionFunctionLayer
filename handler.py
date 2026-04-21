from evaluation_function_utils.errors import EvaluationException

from .tools import commands, docs, parse, validate
from .tools.parse import ParseError
from .tools.utils import ErrorResponse, HandlerResponse, JsonType, Response
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


def handle_muEd_command(event: JsonType, command: str) -> HandlerResponse:
    """Switch case for handling different command options using muEd schemas.

    Args:
        event (JsonType): The AWS Lambda event recieved by the handler.
        command (str): The name of the function to invoke.

    Returns:
        HandlerResponse: The response object returned by the handler.
    """
    if command == "eval":
        body = parse.body(event)
        validate.body(body, MuEdReqBodyValidators.EVALUATION)
        response = commands.evaluate_muEd(body)
        validate.body(response, MuEdResBodyValidators.EVALUATION)

    elif command == "healthcheck":
        response = commands.healthcheck()

    else:
        response = Response(
            error=ErrorResponse(message=f"Unknown command '{command}'.")
        )

    return response


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
