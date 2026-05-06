import os
import unittest
from pathlib import Path
from typing import Any

from ..handler import handler
from ..tools import commands
from ..tools.utils import JsonType

_SCHEMAS_DIR = str(Path(__file__).parent.parent / "schemas")


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
        os.environ["SCHEMA_DIR"] = _SCHEMAS_DIR
        commands.evaluation_function = evaluation_function
        return super().setUp()

    def tearDown(self) -> None:
        os.environ.pop("SCHEMA_DIR", None)
        commands.evaluation_function = None
        return super().tearDown()

    def test_valid_eval_command(self):
        body = {"response": "hello", "answer": "world", "params": {}}
        response = commands.evaluate(body)

        self.assertIn("result", response)
        self.assertIn("is_correct", response["result"])  # type: ignore

    def test_eval_response_latex_and_simplified_are_none_when_not_returned(self):
        body = {"response": "hello", "answer": "world", "params": {}}
        response = commands.evaluate(body)

        self.assertNotIn("response_latex", response["result"])  # type: ignore
        self.assertNotIn("response_simplified", response["result"])  # type: ignore

    def test_eval_response_latex_and_simplified_passed_through_when_returned(self):
        commands.evaluation_function = lambda r, a, p: {
            "is_correct": True,
            "response_latex": r"x + 1",
            "response_simplified": "x + 1",
        }
        body = {"response": "x+1", "answer": "x+1", "params": {}}
        response = commands.evaluate(body)

        self.assertEqual(response["result"]["response_latex"], r"x + 1")  # type: ignore
        self.assertEqual(response["result"]["response_simplified"], "x + 1")  # type: ignore

    def test_invalid_eval_args_raises_parse_error(self):
        event = {"headers": {"command": "eval"}, "other": "params"}
        response = handler(event)
        self.assertIn("error", response)
        self.assertEqual(
            response["error"]["message"], "No data supplied in request body."  # type: ignore
        )

    def test_invalid_eval_schema_raises_validation_error(self):
        event = {"headers": {"command": "eval"}, "body": {"response": "hello", "params": {}}}
        response = handler(event)
        self.assertIn("error", response)
        self.assertEqual(
            response["error"]["message"],  # type: ignore
            "Failed to validate body against the evaluation schema.",
        )

    def test_single_feedback_case(self):
        body = {
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

        response = commands.evaluate(body)
        result = response["result"]  # type: ignore

        self.assertTrue(result["is_correct"])
        self.assertNotIn("matched_case", result)
        self.assertNotIn("feedback", result)

    def test_single_feedback_case_match(self):
        body = {
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

        response = commands.evaluate(body)
        result = response["result"]  # type: ignore

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["matched_case"], 0)
        self.assertEqual(result["feedback"], "should be 'hello'.")

    def test_case_warning_data_structure(self):
        body = {
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

        response = commands.evaluate(body)
        result = response["result"]  # type: ignore

        self.assertIn("warnings", result)
        warning = result["warnings"].pop()  # type: ignore

        self.assertDictEqual(
            warning,
            {"case": 0, "message": "Missing answer/feedback field"},
        )

    def test_multiple_feedback_cases_single_match(self):
        body = {
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

        response = commands.evaluate(body)
        result = response["result"]  # type: ignore

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["matched_case"], 1)
        self.assertEqual(result["feedback"], "should be 'yes'.")

    def test_multiple_feedback_cases_multiple_matches(self):
        body = {
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

        response = commands.evaluate(body)
        result = response["result"]  # type: ignore

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["matched_case"], 0)
        self.assertEqual(result["feedback"], "should be 'hello'.")

    def test_case_params_overwrite_eval_params(self):
        body = {
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

        response = commands.evaluate(body)
        result = response["result"]  # type: ignore

        self.assertTrue(result["is_correct"])
        self.assertNotIn("matched_case", result)
        self.assertNotIn("feedback", result)

    def test_invalid_case_entry_doesnt_raise_exception(self):
        body = {
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

        response = commands.evaluate(body)
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

    def test_first_matching_case_stops_evaluation(self):
        body = {
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

        response = commands.evaluate(body)
        result = response["result"]  # type: ignore

        self.assertNotIn("warnings", result)
        self.assertEqual(result["matched_case"], 0)
        self.assertEqual(result["feedback"], "should be 'hello'.")

    def test_overriding_eval_feedback_to_correct_case(self):
        body = {
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

        response = commands.evaluate(body)
        result = response["result"]  # type: ignore

        self.assertTrue(result["is_correct"])
        self.assertEqual(result["matched_case"], 0)
        self.assertEqual(result["feedback"], "should be 'hello'.")

    def test_overriding_eval_feedback_to_incorrect_case(self):
        body = {
            "response": "hello",
            "answer": "hola",
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

        response = commands.evaluate(body)
        result = response["result"]  # type: ignore

        self.assertFalse(result["is_correct"])
        self.assertEqual(result["matched_case"], 0)
        self.assertEqual(result["feedback"], "should be 'hello'.")

    def test_valid_preview_command(self):
        body = {"response": "hello"}

        response = commands.preview(body)
        result = response["result"]  # type: ignore

        self.assertEqual(result["preview"], "hello")

    def test_invalid_preview_args_raises_parse_error(self):
        event = {"headers": {"command": "preview"}, "other": "params"}
        response = handler(event)
        self.assertIn("error", response)
        self.assertEqual(
            response["error"]["message"], "No data supplied in request body."  # type: ignore
        )

    def test_invalid_preview_schema_raises_validation_error(self):
        event = {"headers": {"command": "preview"}, "body": {"response": "hello", "answer": "hello"}}
        response = handler(event)
        self.assertIn("error", response)
        self.assertEqual(
            response["error"]["message"],  # type: ignore
            "Failed to validate body against the preview schema.",
        )

    def test_healthcheck(self):
        response = commands.healthcheck()

        self.assertIn("result", response)
        result = response["result"]  # type: ignore

        self.assertIn("tests_passed", result)


if __name__ == "__main__":
    unittest.main()
