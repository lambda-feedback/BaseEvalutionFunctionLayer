from evaluation_function_utils.errors import EvaluationException

from .tools import commands, docs, validate
from .tools.parse import ParseError
from .tools.utils import ErrorResponse, HandlerResponse, JsonType, Response
from .tools.validate import ResBodyValidators, ValidationError


def handle_command(event: JsonType, command: str) -> HandlerResponse:
    """Switch case for handling different command options.

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
        validator = ResBodyValidators.EVALUATION

    validate.body(response, validator)

    return response


def handler(event: JsonType, _: JsonType = {}) -> HandlerResponse:
    """Main function invoked by AWS Lambda to handle incoming requests.

    Args:
        event (JsonType): The AWS Lambda event received by the gateway.

    Returns:
        HandlerResponse: The response to return back to the requestor.
    """
    headers = event.get("headers", dict())
    command = headers.get("command", "eval")

    try:
        return handle_command(event, command)

    except ParseError as e:
        error = ErrorResponse(message=e.message, detail=e.error_thrown)

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
