import unittest

from ..tools import validate
from ..tools.validate import ReqBodyValidators, ValidationError


class TestRequestValidation(unittest.TestCase):
    def test_empty_request_body(self):
        body = {}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.message),
            "Failed to validate body against the evaluation schema.",
        )

    def test_missing_response(self):
        body = {"answer": "example", "params": {}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.EVALUATION)

        self.assertEqual(
            e.exception.error_thrown["message"],  # type: ignore
            "'response' is a required property",
        )

    def test_null_response_for_eval(self):
        body = {"response": None, "answer": "example", "params": {}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.EVALUATION)

        self.assertEqual(
            e.exception.error_thrown["message"],  # type: ignore
            "None should not be valid under {'type': 'null'}",
        )

    def test_null_response_for_preview(self):
        body = {"response": None, "params": {}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.PREVIEW)

        self.assertEqual(
            e.exception.error_thrown["message"],  # type: ignore
            "None should not be valid under {'type': 'null'}",
        )

    def test_missing_answer_in_eval(self):
        body = {"response": "example", "params": {}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.EVALUATION)

        self.assertEqual(
            e.exception.error_thrown["message"],  # type: ignore
            "'answer' is a required property",
        )

    def test_missing_answer_in_preview(self):
        body = {"response": "example", "params": {}}
        validate.body(body, ReqBodyValidators.PREVIEW)

    def test_including_answer_in_eval(self):
        body = {"response": "example", "answer": "anything", "params": {}}
        validate.body(body, ReqBodyValidators.EVALUATION)

    def test_including_answer_in_preview(self):
        body = {"response": "example", "answer": "anything", "params": {}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.PREVIEW)

        self.assertEqual(
            e.exception.error_thrown["message"],  # type: ignore
            "Additional properties are not allowed ('answer' was unexpected)",
        )

    def test_null_answer(self):
        body = {"response": "example", "answer": None, "params": {}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.EVALUATION)

        self.assertEqual(
            e.exception.error_thrown["message"],  # type: ignore
            "None should not be valid under {'type': 'null'}",
        )

    def test_bad_params(self):
        body = {"response": "example", "answer": "example", "params": 2}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.EVALUATION)

        self.assertEqual(
            e.exception.error_thrown["message"],  # type: ignore
            "2 is not of type 'object'",
        )

    def test_extra_fields(self):
        body = {
            "response": "example",
            "answer": "example",
            "params": {},
            "hello": "world",
        }

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ReqBodyValidators.EVALUATION)

        self.assertEqual(
            e.exception.error_thrown["message"],  # type: ignore
            "Additional properties are not allowed ('hello' was unexpected)",
        )

    def test_valid_request_body(self):
        body = {"response": "", "answer": ""}
        validate.body(body, ReqBodyValidators.EVALUATION)


if __name__ == "__main__":
    unittest.main()
