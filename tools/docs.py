import base64
import os

from .utils import DocsResponse


def send_file(filepath: str) -> DocsResponse:
    """Create a response object for receiving a file.

    Args:
        filepath (str): The path of the file to send.

    Returns:
        DocsResponse: The response object the handler should return.
    """
    if not os.path.isfile(filepath):
        return DocsResponse(
            statusCode=200,
            body=f"{filepath} missing from evaluation function files",
            headers={"Content-Type": "application/octet-stream"},
            isBase64Encoded=False,
        )

    with open(filepath, "rb") as file:
        docs_file = file.read()

    docs_encoded = base64.encodebytes(docs_file)

    return DocsResponse(
        statusCode=200,
        body=docs_encoded.decode(),
        headers={"Content-Type": "application/octet-stream"},
        isBase64Encoded=True,
    )


def user() -> DocsResponse:
    """Return the user (teacher) documentation for this function."""
    return send_file("app/docs/user.md")


def dev() -> DocsResponse:
    """Return the developer (teacher) documentation for this function."""
    return send_file("app/docs/dev.md")
