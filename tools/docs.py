import base64
import os

from .utils import DocsResponse


def send_generic_file(filepath: str) -> DocsResponse:
    """
    Fetch and return a file given by filepath
    """

    if not os.path.isfile(filepath):
        return DocsResponse(
            statusCode=200,
            body=f"{filepath} missing from evaluation function files",
            headers={"Content-Type": "application/octet-stream"},
            isBase64Encoded=False,
        )

    # Read file
    with open(filepath, "rb") as file:
        docs_file = file.read()

    docs_encoded = base64.encodestring(docs_file)

    return DocsResponse(
        statusCode=200,
        body=docs_encoded.decode(),
        headers={"Content-Type": "application/octet-stream"},
        isBase64Encoded=True,
    )


def send_user_docs() -> DocsResponse:
    """
    Return the user (teacher) documentation for this function
    """

    return send_generic_file("app/docs/user.md")


def send_dev_docs() -> DocsResponse:
    """
    Return the developer (teacher) documentation for this function
    """

    return send_generic_file("app/docs/dev.md")
