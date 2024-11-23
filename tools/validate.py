import enum
import functools
import os
from typing import Dict, List, TypedDict, Union

import dotenv
import jsonschema
import jsonschema.exceptions
import json

dotenv.load_dotenv()


class SchemaErrorThrown(TypedDict):
    """Detail object returned in the error response for schema exceptions."""

    message: str
    schema_path: List[Union[str, int]]
    instance_path: List[Union[str, int]]


class ValidationError(Exception):
    """Generic exception for all validation issues."""

    def __init__(
        self, message: str, error_thrown: Union[str, SchemaErrorThrown], *args
    ) -> None:
        super().__init__(*args)

        self.message = message
        self.error_thrown = error_thrown


"""Enumeration objects for picking which schema to validate against."""


class ReqBodyValidators(enum.Enum):
    """Enum for all request body validators."""

    ORIGINAL = "request.json"
    EVALUATION = "request/eval.json"
    PREVIEW = "request/preview.json"


class ResBodyValidators(enum.Enum):
    """Enum for all response body validators."""

    ORIGINAL = "responsev2.json"
    EVALUATION = "response/eval.json"
    PREVIEW = "response/preview.json"
    HEALTHCHECK = "response/healthcheck.json"


BodyValidators = Union[ReqBodyValidators, ResBodyValidators]

def load_validator(
    validator_enum: BodyValidators,
) -> jsonschema.Draft7Validator:
    """Loads a json schema for body validations.

    Args:
        validator_enum (BodyValidators): The validator enum name.

    Raises:
        ValueError: Raised if the schema repo URL cannot be found.

    Returns:
        Draft7Validator: The validator to use.
    """
    schema_dir = os.getenv("SCHEMA_DIR")
    if schema_dir is None:
        raise RuntimeError("No schema path suplied.")

    schema_path = os.path.join(schema_dir,validator_enum.value)

    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
    except FileNotFoundError as e:
        raise RuntimeError(f"Could not find schema for {validator_enum}") from e

    return jsonschema.Draft7Validator(schema)


def body(body: Dict, validator_enum: BodyValidators) -> None:
    """Validate the body of a request using the request-respone-schemas.

    Args:
        body (Dict): The body object to validate.
        validator_enum (BodyValidators): The enum name of the validator to use.

    Raises:
        ValidationError: If the validation fails, or the validator could not
        be obtained.
    """
    try:
        validator = load_validator(validator_enum)
        validator.validate(body)

        return

    except jsonschema.exceptions.ValidationError as e:
        error_thrown = SchemaErrorThrown(
            message=e.message,
            schema_path=list(e.absolute_schema_path),
            instance_path=list(e.absolute_path),
        )
    except Exception as e:
        error_thrown = str(e)

    raise ValidationError(
        "Failed to validate body against the "
        f"{validator_enum.name.lower()} schema.",
        error_thrown,
    )
