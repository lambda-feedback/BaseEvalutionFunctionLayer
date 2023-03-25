import unittest
from typing import Optional

from ..handler import handler
from ..tools import commands
from ..tools.utils import EvaluationFunctionType

evaluation_function: Optional[
    EvaluationFunctionType
] = lambda response, answer, params: {"is_correct": True}


class TestHandlerFunction(unittest.TestCase):
    def setUp(self) -> None:
        commands.evaluation_function = evaluation_function
        return super().setUp()

    def tearDown(self) -> None:
        commands.evaluation_function = None
        return super().tearDown()

    def test_handle_bodyless_event(self):
        event = {"random": "metadata", "without": "a body"}

        response = handler(event)

        self.assertIn("error", response)
        error = response.get("error")

        self.assertEqual(
            error["message"],  # type: ignore
            "No data supplied in request body.",
        )

    def test_non_json_body(self):
        event = {"random": "metadata", "body": "{}}}{{{[][] this is not json."}

        response = handler(event)

        self.assertIn("error", response)
        error = response.get("error")

        self.assertEqual(
            error["message"], "Request body is not valid JSON."  # type: ignore
        )

    def test_eval(self):
        event = {
            "random": "metadata",
            "body": {"response": "hello", "answer": "world!", "params": {}},
            "headers": {"command": "eval"},
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "eval")
        self.assertIn("result", response)

    def test_eval_no_params(self):
        event = {
            "random": "metadata",
            "body": {"response": "hello", "answer": "world!"},
            "headers": {"command": "eval"},
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "eval")
        self.assertIn("result", response)

    def test_handler_evals_by_default(self):
        event = {
            "random": "metadata",
            "body": {"response": "hello", "answer": "world!"},
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "eval")

    def test_preview(self):
        event = {
            "random": "metadata",
            "body": {"response": "hello", "params": {}},
            "headers": {"command": "preview"},
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "preview")
        self.assertIn("result", response)

    def test_preview_no_params(self):
        event = {
            "random": "metadata",
            "body": {"response": "hello"},
            "headers": {"command": "preview"},
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "preview")
        self.assertIn("result", response)

    def test_healthcheck(self):
        event = {
            "random": "metadata",
            "body": "{}",
            "headers": {"command": "healthcheck"},
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "healthcheck")
        self.assertIn("result", response)

    def test_invalid_command(self):
        event = {
            "random": "metadata",
            "body": "{}",
            "headers": {"command": "not a command"},
        }

        response = handler(event)
        error = response.get("error")

        self.assertEqual(
            error["message"],  # type: ignore
            "Unknown command 'not a command'.",
        )


if __name__ == "__main__":
    unittest.main()
