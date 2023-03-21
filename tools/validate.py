import enum
import functools
import os
from typing import Dict, List, TypedDict, Union

import jsonschema
import jsonschema.exceptions
import requests


class SchemaErrorThrown(TypedDict):
    message: str
    schema_path: List[Union[str, int]]
    instance_path: List[Union[str, int]]


class ValidationError(Exception):
    def __init__(
        self, message: str, error_thrown: Union[str, SchemaErrorThrown], *args
    ) -> None:
        super().__init__(*args)

        self.message = message
        self.error_thrown = error_thrown


class ReqBodyValidators(enum.Enum):
    GENERIC = "request.json"
    EVALUATION = "request/eval.json"
    PREVIEW = "request/preview.json"


class ResBodyValidators(enum.Enum):
    GENERIC = "responsev2.json"
    EVALUATION = "response/eval.json"
    PREVIEW = "response/preview.json"
    HEALTHCHECK = "response/healthcheck.json"


BodyValidators = Union[ReqBodyValidators, ResBodyValidators]


@functools.lru_cache
def load_validator_from_url(validator_name: BodyValidators):
    """
    Function to create a validator by pulling the schema from a url.
    ---
    This function makes a get request to the URL and converts the body
    to a JSON schema.
    This is then loaded into jsonschema validator and returned.
    """
    schemas_url = os.environ.get("SCHEMAS_URL")

    if schemas_url is None:
        raise ValueError("Schema URL is not defined in base layer.")

    schema_url = os.path.join(schemas_url, validator_name.value)

    schema = requests.get(schema_url).json()
    return jsonschema.Draft7Validator(schema)


def body(body: Union[Dict, TypedDict], validator_name: BodyValidators) -> None:
    try:
        validator = load_validator_from_url(validator_name)
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
        f"Failed to validate against {validator_name}.", error_thrown
    )
