import json

from typing import Tuple

def load_body(body_text: str) -> Tuple[dict, dict]:
    """
    Function to convert JSON-encoded string of the request body into a dictionary.
    ---
    Returns a tuple, first element of which is the body, second of which is a 
    JSON-encodable dictionary containing errors and helpful messages which can be used
    as a response.

    If the body could not be loaded, an empty dictionary is returned.
    """

    # Attempt to load the body text
    try:
        return json.loads(body_text), None
    # Catch Decode errors and return the problems back to the requester.
    except json.JSONDecodeError as e:
        return None, {
            "message": "Request body is not valid JSON.",
            "error_thrown": {
                "message": e.msg,
                "location": {
                    "line": e.lineno,
                    "column": e.colno
                }
            }
        }
    
    # Catch type error problems incase the body is not a string (for testing purposes).
    except TypeError:
        return None, {
            "message": "Request body is not text."
        }

def parse_body(event: dict) -> Tuple[dict, dict]:
    """
    Function to parse the request body into a dictionary from an AWS Event object.
    ---
    Returns a tuple, first element of which is the body, second of which is a 
    JSON-encodable dictionary containing errors and helpful messages which can be used
    as a response.

    If the body could not be loaded, an empty dictionary is returned.
    """
    # Check if body exits in the event
    if "body" not in event:
        return None, {
            "message": "No grading data supplied in request body."
        }

    # Don't convert if already a dict (for testing purposes)
    if type(event["body"]) == dict:
        return event["body"], None

    # If it does, convert the body into a dictionary.
    return load_body(event["body"])
