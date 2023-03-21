from __future__ import annotations

from typing import Any, Dict, Literal, TypedDict, Union

from typing_extensions import NotRequired

JsonType = Dict
SupportedCommands = Literal["eval", "grade", "preview", "healthcheck"]


class ErrorResponse(TypedDict):
    message: str
    detail: NotRequired[Any]


class Response(TypedDict, total=False):
    command: SupportedCommands
    result: Union[Dict, TypedDict]
    error: Union[Dict, ErrorResponse]


class DocsResponse(TypedDict):
    headers: Dict
    statusCode: int
    body: str
    isBase64Encoded: bool


HandlerResponse = Union[Response, DocsResponse]
