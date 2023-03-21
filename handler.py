from evaluation_function_utils.errors import EvaluationException

from .tools import commands, docs, validate
from .tools.parse import ParseError
from .tools.utils import ErrorResponse, HandlerResponse, JsonType, Response
from .tools.validate import ResBodyValidators, ValidationError


def handle_command(event: JsonType, command: str) -> HandlerResponse:
    if command in ("docs-dev", "docs"):
        return docs.send_dev_docs()

    elif command == "docs-user":
        return docs.send_user_docs()

    elif command in ("eval", "grade"):
        response = commands.evaluate(event)
        validator = ResBodyValidators.EVALUATION

    elif command == "preview":
        response = commands.preview(event)
        validator = ResBodyValidators.PREVIEW

    elif command == "healthcheck":
        response = commands.healthcheck()
        validator = ResBodyValidators.HEALTHCHECK
    else:
        response = Response(
            error=ErrorResponse(message=f"Unknown command '{command}'.")
        )
        validator = ResBodyValidators.GENERIC

    validate.body(response, validator)

    return response


def handler(event: JsonType, context: JsonType = {}) -> HandlerResponse:
    """
    Main function invoked by AWS Lambda to handle incoming requests.
    ---
    This function invokes the handler function for that particular command
    and returns
    the result. It also performs validation on the response body to make sure
    it follows
    the schema set out in the request-response-schema repo.
    """
    headers = event.get("headers", dict())
    command = headers.get("command", "eval")

    try:
        return handle_command(event, command)

    except ParseError as e:
        error = ErrorResponse(message=e.message, detail=e.error_thrown)

    except ValidationError as e:
        error = ErrorResponse(message=e.message, detail=e.error_thrown)

    except EvaluationException as e:
        error = e.error_dict

    except Exception as e:
        error = ErrorResponse(
            message="An exception was raised while "
            "executing the preview function.",
            detail=(str(e) if str(e) != "" else repr(e)),
        )

    return Response(error=error)
