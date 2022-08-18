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

    response = body["response"]
    answer = body["answer"]
    params = body.get("params", dict())

    try:
        result = evaluation_function(response, answer, params)

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

    # Result already contains feedback generated inside the custom function
    if "feedback" in result:
        return {"command": "eval", "result": result}

    # If a list of "cases" wasn't provided, we don't have any other way to get feedback
    cases = params.get("cases", [])
    if len(cases) == 0:
        return {"command": "eval", "result": result}

    # Determine what feedback to provide based on cases
    feedback, warnings = feedback_from_cases(response, params, cases)
    if feedback:
        result["feedback"] = feedback

    # Add warnings out output if any were encountered
    if len(warnings) != 0:
        result["warnings"] = warnings

    return {"command": "eval", "result": result}


def feedback_from_cases(response, params, cases):
    """ 
    Attempt to find the correct feedback from a list of cases.
    Returns a "feedback" string, and optional list of warnings
    """

    # A list of "cases" was provided, try matching to each of them
    matches = []
    warnings = []
    for i, case in enumerate(cases):
        # Validate the case block has an answer and feedback
        if 'answer' not in case:
            warnings += [{"case": i, "message": "Missing answer field"}]
            continue

        if 'feedback' not in case:
            warnings += [{"case": i, "message": "Missing feedback field"}]
            continue

        # Merge current evaluation params with any specified in case
        case_params = case.get('params', {})

        # Run the evaluation function based on this case's answer
        try:
            res = evaluation_function(response, case.get('answer'), {
                **params,
                **case_params
            })

        except EvaluationException as e:
            warnings += [{"case": i, **e.error_dict}]
            continue

        except Exception as e:
            warnings += [{
                "case": i,
                "message":
                "An exception was raised while executing the evaluation function.",
                "detail": str(e) if str(e) != "" else repr(e)
            }]
            continue

        # Function should always return an 'is_correct' if no errors were raised
        if not 'is_correct' in res:
            warnings += [{
                "case": i,
                "message": "is_correct missing from function output"
            }]
            continue

        # This case matches the response, add it's index to the list of matches
        if res.get('is_correct') == True:
            matches += [i]

    if len(matches) == 0:
        return '', warnings

    if len(matches) == 1:
        # warnings += [{"case": matches[0]}]
        return cases[matches[0]]['feedback'], warnings

    else:
        s = ', '.join([str(m) for m in matches])
        warnings += [{
            "message":
            f"Cases {s} were matched. Only the first one's feedback was returned"
        }]
        return cases[matches[0]]['feedback'], warnings


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

    elif command == "docs-dev" or command == "docs":
        return docs.send_dev_docs()

    elif command == "docs-user":
        return docs.send_user_docs()

    else:
        response = handle_unknown_command(command)

    response_error = v.validate_response(response)

    if response_error:
        return {"error": response_error}

    return response
