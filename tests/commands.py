import unittest
from typing import Any

from ..tools import commands, parse, validate
from ..tools.utils import JsonType


def evaluation_function(
    response: Any, answer: Any, params: JsonType
) -> JsonType:
    if params.get("raise", False):
        raise ValueError("raised")

    force_true = params.get("force", False)

    return {"is_correct": (response == answer) or force_true}


class TestCommandsModule(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

    def setUp(self) -> None:
        commands.evaluation_function = evaluation_function
        return super().setUp()

    def tearDown(self) -> None:
        commands.evaluation_function = None
        return super().tearDown()

    def test_valid_eval_command(self):
        event = {
            "body": {"response": "hello", "answer": "world", "params": {}}
        }
        response = commands.evaluate(event)

        self.assertIn("result", response)
        self.assertIn("is_correct", response["result"])  # type: ignore

    def test_invalid_eval_args_raises_parse_error(self):
        event = {"headers": "any", "other": "params"}

        with self.assertRaises(parse.ParseError) as e:
            commands.evaluate(event)

        self.assertEqual(
            e.exception.message, "No data supplied in request body."
        )

    def test_invalid_eval_schema_raises_validation_error(self):
        event = {"body": {"response": "hello", "params": {}}}

        with self.assertRaises(validate.ValidationError) as e:
            commands.evaluate(event)

        self.assertEqual(
            e.exception.message,
            "Failed to validate body against the evaluation schema.",
        )

    def test_single_feedback_case(self):
        event = {
            "body": {
                "response": "hello",
                "answer": "hello",
                "params": {
                    "cases": [
                        {
                            "answer": "other",
                            "feedback": "should be 'other'.",
                            "mark": 0,
                        }
                    ]
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertTrue(result["is_correct"])
        self.assertNotIn("matched_case", result)
        self.assertNotIn("feedback", result)

    def test_single_feedback_case_match(self):
        event = {
            "body": {
                "response": "hello",
                "answer": "world",
                "params": {
                    "cases": [
                        {
                            "answer": "hello",
                            "feedback": "should be 'hello'.",
                        }
                    ]
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["matched_case"], 0)
        self.assertEqual(result["feedback"], "should be 'hello'.")

    def test_case_warning_data_structure(self):
        event = {
            "body": {
                "response": "hello",
                "answer": "world",
                "params": {
                    "cases": [
                        {
                            "feedback": "should be 'hello'.",
                        }
                    ]
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertIn("warnings", result)
        warning = result["warnings"].pop()  # type: ignore

        self.assertDictEqual(
            warning,
            {"case": 0, "message": "Missing answer/feedback field"},
        )

    def test_multiple_feedback_cases_single_match(self):
        event = {
            "body": {
                "response": "yes",
                "answer": "world",
                "params": {
                    "cases": [
                        {
                            "answer": "hello",
                            "feedback": "should be 'hello'.",
                        },
                        {
                            "answer": "yes",
                            "feedback": "should be 'yes'.",
                        },
                        {
                            "answer": "no",
                            "feedback": "should be 'no'.",
                        },
                    ]
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["matched_case"], 1)
        self.assertEqual(result["feedback"], "should be 'yes'.")

    def test_multiple_feedback_cases_multiple_matches(self):
        event = {
            "body": {
                "response": "yes",
                "answer": "world",
                "params": {
                    "cases": [
                        {
                            "answer": "hello",
                            "feedback": "should be 'hello'.",
                            "params": {"force": True},
                        },
                        {
                            "answer": "yes",
                            "feedback": "should be 'yes'.",
                        },
                        {
                            "answer": "no",
                            "feedback": "should be 'no'.",
                        },
                    ]
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["matched_case"], 0)
        self.assertEqual(result["feedback"], "should be 'hello'.")

    def test_case_params_overwrite_eval_params(self):
        event = {
            "body": {
                "response": "hello",
                "answer": "world",
                "params": {
                    "force": True,
                    "cases": [
                        {
                            "answer": "yes",
                            "feedback": "should be 'yes'.",
                            "params": {"force": False},
                        }
                    ],
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertTrue(result["is_correct"])
        self.assertNotIn("matched_case", result)
        self.assertNotIn("feedback", result)

    def test_invalid_case_entry_doesnt_raise_exception(self):
        event = {
            "body": {
                "response": "hello",
                "answer": "world",
                "params": {
                    "cases": [
                        {
                            "answer": "hello",
                            "feedback": "should be 'hello'.",
                            "params": {"raise": True},
                        }
                    ]
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertIn("warnings", result)
        warning = result["warnings"].pop()  # type: ignore

        self.assertDictEqual(
            warning,
            {
                "case": 0,
                "message": "An exception was raised while executing "
                "the evaluation function.",
                "detail": "raised",
            },
        )

    def test_multiple_matched_cases_are_combined_and_warned(self):
        event = {
            "body": {
                "response": "yes",
                "answer": "world",
                "params": {
                    "cases": [
                        {
                            "answer": "hello",
                            "feedback": "should be 'hello'.",
                            "params": {"force": True},
                        },
                        {
                            "answer": "yes",
                            "feedback": "should be 'yes'.",
                        },
                        {
                            "answer": "no",
                            "feedback": "should be 'no'.",
                        },
                    ]
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertIn("warnings", result)
        warning = result["warnings"].pop()  # type: ignore

        self.assertDictEqual(
            warning,
            {
                "message": "Cases 0, 1 were matched. "
                "Only the first one's feedback was returned",
            },
        )

    def test_overriding_eval_feedback_to_correct_case(self):
        event = {
            "body": {
                "response": "hello",
                "answer": "world",
                "params": {
                    "cases": [
                        {
                            "answer": "hello",
                            "feedback": "should be 'hello'.",
                            "mark": 1,
                        }
                    ]
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertTrue(result["is_correct"])
        self.assertEqual(result["matched_case"], 0)
        self.assertEqual(result["feedback"], "should be 'hello'.")

    def test_overriding_eval_feedback_to_incorrect_case(self):
        event = {
            "body": {
                "response": "hello",
                "answer": "hello",
                "params": {
                    "cases": [
                        {
                            "answer": "hello",
                            "feedback": "should be 'hello'.",
                            "mark": 0,
                        }
                    ]
                },
            }
        }

        response = commands.evaluate(event)
        result = response["result"]  # type: ignore

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["matched_case"], 0)
        self.assertEqual(result["feedback"], "should be 'hello'.")

    def test_valid_preview_command(self):
        event = {"body": {"response": "hello"}}

        response = commands.preview(event)
        result = response["result"]  # type: ignore

        self.assertEqual(result["preview"]["latex"], "hello")

    def test_invalid_preview_args_raises_parse_error(self):
        event = {"headers": "any", "other": "params"}

        with self.assertRaises(parse.ParseError) as e:
            commands.preview(event)

        self.assertEqual(
            e.exception.message, "No data supplied in request body."
        )

    def test_invalid_preview_schema_raises_validation_error(self):
        event = {"body": {"response": "hello", "answer": "hello"}}

        with self.assertRaises(validate.ValidationError) as e:
            commands.preview(event)

        self.assertEqual(
            e.exception.message,
            "Failed to validate body against the preview schema.",
        )

    def test_healthcheck(self):
        response = commands.healthcheck()

        self.assertIn("result", response)
        result = response["result"]  # type: ignore

        self.assertIn("tests_passed", result)


if __name__ == "__main__":
    unittest.main()
