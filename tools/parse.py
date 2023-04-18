import json
from typing import Dict, Literal, Optional, TypedDict, Union

from .utils import JsonType


class DecodeErrorDetail(TypedDict):
    message: str
    location: Dict[Literal["line", "column"], int]


class ParseError(Exception):
    """Custom exception for all parsing issues."""

    def __init__(
        self,
        message: str,
        error_thrown: Optional[Union[str, DecodeErrorDetail]] = None,
        *args,
    ) -> None:
        super().__init__(*args)
        self.message = message
        self.error_thrown = error_thrown


def body(event: JsonType) -> JsonType:
    """Get the body of a AWS Lambda event as a dictionary.

    Args:
        event (JsonType): The AWS Lambda event recieved by the handler.

    Raises:
        ParseError: Raised if the body doesn't exist, or the body couldn't be
        decoded.

    Returns:
        JsonType: The body of the event.
    """
    body = event.get("body")

    if body is None:
        raise ParseError("No data supplied in request body.")
    elif type(body) is dict:
        return body

    # If it does, convert the body into a dictionary.
    try:
        return json.loads(body)
    # Catch Decode errors and return the problems back to the requester.
    except json.JSONDecodeError as e:
        error_thrown = DecodeErrorDetail(
            message=e.msg, location={"line": e.lineno, "column": e.colno}
        )
    except Exception as e:
        error_thrown = str(e)

    raise ParseError("Request body is not valid JSON.", error_thrown)
