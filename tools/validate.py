import os
import requests
import jsonschema

def load_validator_from_url(uri_env_name):
    """
    Function to create a validator by pulling the schema from a url.
    ---
    This function makes a get request to the URL and converts the body to a JSON schema.
    This is then loaded into jsonschema validator and returned.
    """
    schema_uri = os.environ.get(uri_env_name)
    schema = requests.get(schema_uri).json()

    return jsonschema.Draft7Validator(schema)

request_validator = load_validator_from_url("REQUEST_SCHEMA_URL")
response_validator = load_validator_from_url("RESPONSE_SCHEMA_URL")

#with open('/Users/louismanestar/OneDrive - Imperial College London/Jobs/Lambda Feedback/repos/lambda-feedback/request-response-schemas/request.json', 'r') as f:
#    request_schema = json.load(f)
#    request_validator = jsonschema.Draft7Validator(request_schema)

#with open('/Users/louismanestar/OneDrive - Imperial College London/Jobs/Lambda Feedback/repos/lambda-feedback/request-response-schemas/response.json', 'r') as f:
#    response_schema = json.load(f)
#    response_validator = jsonschema.Draft7Validator(response_schema)

def validate(validator, body):
    try:
        validator.validate(body)
    except jsonschema.exceptions.ValidationError as e:
        
        return {
            "message": e.message,
            "schema_path": list(e.absolute_schema_path),
            "instance_path": list(e.absolute_path)
        }
    
    return None

def validate_request(body):
    """    
    Function to return any errors in the request body based on its schema.
    ---
    If there are no issues with the request body, then None is returned. Otherwise, a
    JSON-encodable response containing the schema and errors will be returned. Each
    element in the list of errors is a dictionary containing the error message and the
    path to the rule in the schema that has thrown the error.
    """
    request_error = validate(request_validator, body)

    if request_error:
        return {
            "message": "Schema threw an error when validating the request body.",
            "error_thrown": request_error
        }

    return None

def validate_response(body):
    """    
    Function to return any errors in the response body based on its schema.
    ---
    If there are no issues with the response body, then None is returned. Otherwise, a
    JSON-encodable response containing the schema and errors will be returned. Each
    element in the list of errors is a dictionary containing the error message and the
    path to the rule in the schema that has thrown the error.
    """
    response_error = validate(response_validator, body)

    if response_error:
        return {
            "message": "Schema threw an error when validating the response body.",
            "error_thrown": response_error
        }

    return None
