# Grading Function Request/Response Schema

## Introduction

This repo holds the schemas used for the grading function request and response bodies. This is used to check that: 

- All requests from the frontend have the correct JSON structure so they can be interpreted by a grading function.
- All grading function responses have the correct JSON structure so they can be interpeted by the frontend to show the correct answer and any feedback.

## Structure (v1)

### Request

The request body can have three fields:

- `response`, which contains the answers provided by the student. This can be anything: a string, boolean, number, array or object.
- `answer`, which contains the correct answer held in the problem set database. This can also be anything.
- `params`, which contains extra arguments for determining whether the student's answer is correct.

Only `response` and `answer` are required. Any extra fields will cause the validation to fail.

### Response

The response body can have three fields:

- `command`, which can only be either `"healthcheck"` or `"grade"`.

    `"healthcheck"` is used only by the backend to check the grading function is alive and working correctly. `"grade"` is used for carrying out a grading request.

- `result`, which contains the results from the healthcheck or grading request. If the results are from a grading request, this is the dictionary that is returned from `grading_function()`.

    - If the command is `grade`, then `results` must be an object and can have two fields:

        - `is_correct`, which must be a boolean.
        - `feedback`, which contains any feedback about the student's answer. This can be an object, array or string.

        Only `is_correct` is required.

    - If the command is `healthcheck`, then `results` must contain:

        - `tests_passed`, which must be a boolean.
        - `successes`, which contains the names of tests that passed and the time it took.
        - `failures`, which contains the names of tests that failed.
        - `errors`, which contains the names of tests that resulted in an error.

        All fields are required.

- `error`, which contains information about any error that was thrown from a request. This can have two fields:

    - `message`, i.e. a human-readable explanation of the cause. This must be a string.

    - `error_thrown`, which contains more details about the error, in particular if the validation, parsing or the grading function caused an error. This must be an object although its content isn't validated.

    Only `message` is required.

Both `command` and `result` are required, unless an error is thrown, in which only `error` can exist. Any extra fields will cause the validation to fail.

## Contact

For questions about these schemas or you would like to discuss possible changes, please [email Peter Johnson](mailto:peter.johnson@imperial.ac.uk).
