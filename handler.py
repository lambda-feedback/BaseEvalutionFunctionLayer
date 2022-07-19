from .evaluation import evaluation_function

from .tools import docs, parse
from .tools.healthcheck import healthcheck
from .tools import validate as v

from evaluation_function_utils.errors import EvaluationException
"""
    Command Handler Functions.
"""


def handle_unknown_command(command):
    """ 
    Function to create the response when the command is unknown.
    ---
    This function does not handle any of the request body so it is neither parsed or
    validated against a schema. Instead, a simple message is returned telling the 
    requestor that the command isn't allowed.
    """
    return {"error": {"message": f"Unknown command '{command}'."}}


def handle_healthcheck_command():
    """
    Function to create the response when commanded to perform a healthcheck.
    ---
    This function does not handle any of the request body so it is neither parsed or
    validated against a schema.
    """
    return {"command": "healthcheck", "result": healthcheck()}


def handle_eval_command(event):
    """
    Function to create the response when commanded to evaluate an answer.
    ---
    This function attempts to parse the request body, performs schema validation and
    attempts to run the evaluation function on the given parameters.

    If any of these fail, a message is returned and an error field is passed if more
    information can be provided.
    """
    body, parse_error = parse.parse_body(event)

    if parse_error:
        return {"error": parse_error}

    request_error = v.validate_request(body)

    if request_error:
        return {"error": request_error}

    try:
        response = body["response"]
        answer = body["answer"]

        params = body.get("params", dict())

        return {
            "command": "eval",
            "result": evaluation_function(response, answer, params)
        }

    # Catch the custom EvaluationException (from evaluation_function_utils) first
    except EvaluationException as e:
        return {"error": e.error_dict}

    except Exception as e:
        return {
            "error": {
                "message":
                "An exception was raised while executing the evaluation function.",
                "detail": str(e) if str(e) != "" else repr(e)
            }
        }


"""
    Main Handler Function
"""


def handler(event, context={}):
    """
    Main function invoked by AWS Lambda to handle incoming requests.
    ---
    This function invokes the handler function for that particular command and returns
    the result. It also performs validation on the response body to make sure it follows
    the schema set out in the request-response-schema repo.
    """
    headers = event.get("headers", dict())
    command = headers.get("command", "eval")

    if command == "healthcheck":
        response = handle_healthcheck_command()

    elif command == "eval" or command == "grade":  # Remove once all funcs update to V2
        response = handle_eval_command(event)

    elif command == "docs":
        # No need to validate docs (the function does error handling)
        return docs.send_docs_file()

    else:
        response = handle_unknown_command(command)

    response_error = v.validate_response(response)

    if response_error:
        return {"error": response_error}

    return response
