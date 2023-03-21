import unittest

from ..tools import validate
from ..tools.validate import ReqBodyValidators, ValidationError


class TestRequestValidation(unittest.TestCase):
    def test_empty_request_body(self):
        body = {}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.GENERIC)
            self.assertEqual(
                str(e),
                "Schema threw an error when validating the request body.",
            )

    def test_missing_response(self):
        body = {"answer": "example", "params": {}}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "'response' is a required property",
        )

    def test_null_response_for_eval(self):
        body = {"response": None, "answer": "example", "params": {}}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "None should not be valid under {'type': 'null'}",
        )

    def test_null_response_for_preview(self):
        body = {"response": None, "answer": "example", "params": {}}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "None should not be valid under {'type': 'null'}",
        )

    def test_missing_answer_in_eval(self):
        body = {"response": "example", "params": {}}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "'answer' is a required property",
        )

    def test_missing_answer_in_preview(self):
        body = {"response": "example", "params": {}}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "'answer' is a required property",
        )

    def test_including_answer_in_eval(self):
        body = {"response": "example", "params": {}}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "'answer' is a required property",
        )

    def test_including_answer_in_preview(self):
        body = {"response": "example", "params": {}}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "'answer' is a required property",
        )

    def test_null_answer(self):
        body = {"response": "example", "answer": None, "params": {}}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "None should not be valid under {'type': 'null'}",
        )

    def test_bad_params(self):
        body = {"response": "example", "answer": "example", "params": 2}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "2 is not of type 'object'",
        )

    def test_extra_fields(self):
        body = {
            "response": "example",
            "answer": "example",
            "params": {},
            "hello": "world",
        }

        validation_error = validate.body(body, ReqBodyValidators.GENERIC)
        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("error_thrown").get("message"),
            "Additional properties are not allowed ('hello' was unexpected)",
        )

    def test_valid_request_body(self):
        body = {"response": "", "answer": ""}
        validation_error = validate.body(body, ReqBodyValidators.GENERIC)
        self.assertEqual(validation_error, None)


if __name__ == "__main__":
    unittest.main()
