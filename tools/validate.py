import enum
import json
import os
from typing import Dict, List, TypedDict, Union

import dotenv
import jsonschema
import jsonschema.exceptions
import yaml

from .utils import Response

dotenv.load_dotenv()

_openapi_spec = None

# EvaluateResponse is not a named schema in the OpenAPI spec — the evaluate
# endpoint returns an inline array of Feedback items.
_EVALUATE_RESPONSE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["feedbackId"],
        "properties": {
            "feedbackId": {"type": "string"},
        },
        "additionalProperties": True,
    },
}


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


class LegacyReqBodyValidators(enum.Enum):
    """Enum for all legacy request body validators."""

    ORIGINAL = "legacy/request.json"
    EVALUATION = "legacy/request/eval.json"
    PREVIEW = "legacy/request/preview.json"


class LegacyResBodyValidators(enum.Enum):
    """Enum for all legacy response body validators."""

    ORIGINAL = "legacy/responsev2.json"
    EVALUATION = "legacy/response/eval.json"
    PREVIEW = "legacy/response/preview.json"
    HEALTHCHECK = "legacy/response/healthcheck.json"


class MuEdReqBodyValidators(enum.Enum):
    """Enum for muEd request body validators."""

    EVALUATION = "EvaluateRequest"


class MuEdResBodyValidators(enum.Enum):
    """Enum for muEd response body validators."""

    EVALUATION = "EvaluateResponse"
    HEALTHCHECK = "EvaluateHealthResponse"


BodyValidators = Union[
    LegacyReqBodyValidators,
    LegacyResBodyValidators,
    MuEdReqBodyValidators,
    MuEdResBodyValidators,
]


def _get_openapi_spec() -> dict:
    """Load and cache the muEd OpenAPI spec."""
    global _openapi_spec
    if _openapi_spec is None:
        schema_dir = os.getenv("SCHEMA_DIR")
        if schema_dir is not None:
            spec_path = os.path.join(schema_dir, "muEd", "openapi-v0_1_0.yml")
        else:
            spec_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "schemas", "muEd", "openapi-v0_1_0.yml",
            )
        with open(spec_path) as f:
            _openapi_spec = yaml.safe_load(f)
    return _openapi_spec


def load_validator(
    validator_enum: Union[LegacyReqBodyValidators, LegacyResBodyValidators],
) -> jsonschema.Draft7Validator:
    """Loads a json schema for body validations.

    Args:
        validator_enum (Union[LegacyReqBodyValidators, LegacyResBodyValidators]): The validator enum name.

    Raises:
        RuntimeError: Raised if the schema directory cannot be found.

    Returns:
        Draft7Validator: The validator to use.
    """
    schema_dir = os.getenv("SCHEMA_DIR")
    if schema_dir is None:
        raise RuntimeError("No schema path supplied.")

    schema_path = os.path.join(schema_dir, validator_enum.value)

    try:
        with open(schema_path, "r") as f:
            schema = json.load(f)
    except FileNotFoundError as e:
        raise RuntimeError(f"Could not find schema for {validator_enum}") from e

    return jsonschema.Draft7Validator(schema)


def _validate_legacy(
    body: Union[Dict, Response],
    validator_enum: Union[LegacyReqBodyValidators, LegacyResBodyValidators],
) -> None:
    try:
        validator = load_validator(validator_enum)
        validator.validate(body)
        return

    except jsonschema.exceptions.ValidationError as e:
        error_thrown: Union[str, SchemaErrorThrown] = SchemaErrorThrown(
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


def _validate_openapi(
    body: Union[Dict, List, Response],
    validator_enum: Union[MuEdReqBodyValidators, MuEdResBodyValidators],
) -> None:
    spec = _get_openapi_spec()
    resolver = jsonschema.RefResolver(base_uri="", referrer=spec)

    schema_name = validator_enum.value
    if schema_name == "EvaluateResponse":
        schema = _EVALUATE_RESPONSE_SCHEMA
    else:
        schema = spec["components"]["schemas"][schema_name]

    try:
        jsonschema.validate(body, schema, resolver=resolver)
        return

    except jsonschema.exceptions.ValidationError as e:
        error_thrown: str = e.message
    except Exception as e:
        error_thrown = str(e)

    raise ValidationError(
        "Failed to validate body against the "
        f"{validator_enum.name.lower()} schema.",
        error_thrown,
    )


def body(body: Union[Dict, List, Response], validator_enum: BodyValidators) -> None:
    """Validate the body of a request using the request-response schemas.

    Args:
        body (Union[Dict, List, Response]): The body object to validate.
        validator_enum (BodyValidators): The enum name of the validator to use.

    Raises:
        ValidationError: If the validation fails, or the validator could not
        be obtained.
    """
    if isinstance(validator_enum, (MuEdReqBodyValidators, MuEdResBodyValidators)):
        _validate_openapi(body, validator_enum)
    else:
        _validate_legacy(body, validator_enum)
