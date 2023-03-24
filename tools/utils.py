from __future__ import annotations

from typing import Any, Callable, Dict, Literal, TypedDict, Union

from typing_extensions import NotRequired

JsonType = Dict[str, Any]
SupportedCommands = Literal["eval", "grade", "preview", "healthcheck"]

EvaluationFunctionType = Callable[[Any, Any, JsonType], JsonType]
PreviewFunctionType = Callable[[Any, JsonType], JsonType]


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
