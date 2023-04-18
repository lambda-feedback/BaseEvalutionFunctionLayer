import unittest

from ..tools import validate
from ..tools.validate import ResBodyValidators, ValidationError


class TestResponseValidation(unittest.TestCase):
    def test_empty_response_body(self):
        body = {}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.message),
            "Failed to validate body against the evaluation schema.",
        )

    def test_extra_fields(self):
        body = {
            "command": "eval",
            "result": {"is_correct": True},
            "hello": "world",
        }

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "Additional properties are not allowed ('hello' was unexpected)",
        )

    def test_bad_eval_command(self):
        body = {"command": "not_eval", "result": {}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "'eval' was expected",
        )

    def test_bad_command_wrong_type(self):
        body = {"command": "not_preview", "result": {}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.PREVIEW)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "'preview' was expected",
        )

    def test_bad_result_wrong_type(self):
        body = {"command": "eval", "result": "an object"}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "'an object' is not of type 'object'",
        )

    def test_bad_result_missing_tests_passed_when_checking_health(self):
        body = {
            "command": "healthcheck",
            "result": {"successes": [], "failures": [], "errors": []},
        }

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.HEALTHCHECK)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "'tests_passed' is a required property",
        )

    def test_bad_error_wrong_type(self):
        body = {"error": "an object"}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "'an object' is not of type 'object'",
        )

    def test_bad_error_missing_message(self):
        body = {"error": {"error_thrown": {"message": "something specific"}}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "'message' is a required property",
        )

    def test_missing_command(self):
        body = {"result": {"is_correct": True}}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "'command' is a required property",
        )

    def test_missing_result(self):
        body = {"command": "eval"}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "'error' is a required property",
        )

    def test_missing_command_with_error(self):
        body = {
            "result": {"is_correct": True},
            "error": {"message": "Some useful information."},
        }

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "'command' is a required property",
        )

    def test_additional_properties(self):
        body = {
            "command": "eval",
            "result": {"is_correct": True},
            "hello": "world",
        }

        with self.assertRaises(ValidationError) as e:
            validate.body(body, ResBodyValidators.EVALUATION)

        self.assertEqual(
            str(e.exception.error_thrown["message"]),  # type: ignore
            "Additional properties are not allowed ('hello' was unexpected)",
        )

    def test_valid_response_missing_command_and_result_with_error(self):
        body = {"error": {"message": "Something went wrong."}}
        validate.body(body, ResBodyValidators.EVALUATION)

    def test_valid_response_with_eval_command(self):
        body = {"command": "eval", "result": {"is_correct": True}}
        validate.body(body, ResBodyValidators.EVALUATION)

    def test_valid_response_with_preview_command(self):
        body = {"command": "preview", "result": {"preview": "anything"}}
        validate.body(body, ResBodyValidators.PREVIEW)

    def test_valid_response_with_healthcheck_command(self):
        body = {
            "command": "healthcheck",
            "result": {
                "tests_passed": True,
                "successes": [{"name": "test_example", "time": 123}],
                "failures": [],
                "errors": [],
            },
        }

        validate.body(body, ResBodyValidators.HEALTHCHECK)


if __name__ == "__main__":
    unittest.main()
