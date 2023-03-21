from __future__ import annotations

from typing import Any, Dict, Literal, TypedDict, Union

from typing_extensions import NotRequired

JsonType = Dict
SupportedCommands = Literal["eval", "grade", "preview", "healthcheck"]


class ErrorResponse(TypedDict):
    """Error object returned in the handler response."""

    message: str
    detail: NotRequired[Any]


class Response(TypedDict, total=False):
    """Response object returned by the handler for eval commands."""

    command: SupportedCommands
    result: Union[Dict, TypedDict]
    error: Union[Dict, ErrorResponse]


class DocsResponse(TypedDict):
    """Response object returned by the handler for doc commands."""

    headers: Dict
    statusCode: int
    body: str
    isBase64Encoded: bool


HandlerResponse = Union[Response, DocsResponse]
