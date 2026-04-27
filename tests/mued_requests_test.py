import unittest

from ..tools import validate
from ..tools.validate import MuEdReqBodyValidators, ValidationError


class TestMuEdRequestValidation(unittest.TestCase):

    def test_empty_request_body(self):
        body = {}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, MuEdReqBodyValidators.EVALUATION)

        self.assertEqual(
            e.exception.message,
            "Failed to validate body against the evaluation schema.",
        )

    def test_missing_submission(self):
        body = {"task": {"title": "test task"}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, MuEdReqBodyValidators.EVALUATION)

        self.assertIn("submission", e.exception.error_thrown)  # type: ignore

    def test_submission_missing_type(self):
        body = {"submission": {"content": {"text": "hello"}}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, MuEdReqBodyValidators.EVALUATION)

        self.assertIn("type", e.exception.error_thrown)  # type: ignore

    def test_invalid_submission_type(self):
        body = {"submission": {"type": "INVALID", "content": {}}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, MuEdReqBodyValidators.EVALUATION)

        self.assertIn("INVALID", e.exception.error_thrown)  # type: ignore

    def test_extra_fields_allowed(self):
        # EvaluateRequest allows additional properties — unknown fields should not raise
        body = {"submission": {"type": "TEXT", "content": {}}, "unknown_field": "value"}
        validate.body(body, MuEdReqBodyValidators.EVALUATION)

    def test_valid_minimal_request(self):
        body = {"submission": {"type": "TEXT", "content": {}}}
        validate.body(body, MuEdReqBodyValidators.EVALUATION)

    def test_valid_other_submission_type(self):
        body = {"submission": {"type": "OTHER", "content": {"content": "some text"}}}
        validate.body(body, MuEdReqBodyValidators.EVALUATION)

    def test_valid_request_with_task(self):
        body = {
            "submission": {
                "type": "TEXT",
                "content": {"text": "Explain polymorphism."},
            },
            "task": {
                "title": "OOP Concepts",
                "referenceSolution": {"text": "Polymorphism allows..."},
            },
        }
        validate.body(body, MuEdReqBodyValidators.EVALUATION)

    def test_valid_request_with_all_optional_fields(self):
        body = {
            "submission": {
                "type": "TEXT",
                "format": "plain",
                "content": {"text": "hello"},
            },
            "task": {
                "title": "Test Task",
                "referenceSolution": {"text": "answer"},
                "learningObjectives": ["Understand polymorphism"],
            },
            "criteria": [
                {"name": "Correctness", "context": "The solution is correct."}
            ],
            "configuration": {"key": "value"},
        }
        validate.body(body, MuEdReqBodyValidators.EVALUATION)


if __name__ == "__main__":
    unittest.main()