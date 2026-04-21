import os
import unittest
from pathlib import Path
from typing import Optional

from ..handler import handler
from ..tools import commands
from ..tools.utils import EvaluationFunctionType

_SCHEMAS_DIR = str(Path(__file__).parent.parent / "schemas")

evaluation_function: Optional[
    EvaluationFunctionType
] = lambda response, answer, params: {"is_correct": True, "feedback": "Well done."}


class TestMuEdHandlerFunction(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SCHEMA_DIR"] = _SCHEMAS_DIR
        commands.evaluation_function = evaluation_function
        return super().setUp()

    def tearDown(self) -> None:
        os.environ.pop("SCHEMA_DIR", None)
        commands.evaluation_function = None
        return super().tearDown()

    def test_evaluate_returns_feedback_list(self):
        event = {
            "path": "/evaluate",
            "body": {"submission": {"type": "TEXT", "content": {}}},
        }

        response = handler(event)

        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 1)
        self.assertIn("awardedPoints", response[0])

    def test_evaluate_feedback_message(self):
        event = {
            "path": "/evaluate",
            "body": {"submission": {"type": "TEXT", "content": {"text": "hello"}}},
        }

        response = handler(event)

        self.assertIsInstance(response, list)
        self.assertEqual(response[0]["message"], "Well done.")
        self.assertEqual(response[0]["awardedPoints"], True)

    def test_evaluate_with_task(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "TEXT", "content": {"text": "Polymorphism allows..."}},
                "task": {
                    "title": "OOP Concepts",
                    "referenceSolution": {"text": "Polymorphism allows objects..."},
                },
            },
        }

        response = handler(event)

        self.assertIsInstance(response, list)

    def test_evaluate_missing_submission_returns_error(self):
        event = {
            "path": "/evaluate",
            "body": {"task": {"title": "Some Task"}},
        }

        response = handler(event)

        self.assertIn("error", response)
        self.assertIn("submission", response["error"]["detail"])  # type: ignore

    def test_evaluate_invalid_submission_type_returns_error(self):
        event = {
            "path": "/evaluate",
            "body": {"submission": {"type": "INVALID"}},
        }

        response = handler(event)

        self.assertIn("error", response)

    def test_evaluate_bodyless_event_returns_error(self):
        event = {"path": "/evaluate", "random": "metadata"}

        response = handler(event)

        self.assertIn("error", response)
        self.assertEqual(
            response["error"]["message"],  # type: ignore
            "No data supplied in request body.",
        )

    def test_healthcheck(self):
        event = {"path": "/health"}

        response = handler(event)

        self.assertEqual(response.get("command"), "healthcheck")
        self.assertIn("result", response)

    def test_unknown_path_falls_back_to_legacy(self):
        event = {
            "path": "/unknown",
            "body": {"response": "hello", "answer": "world!"},
            "headers": {"command": "eval"},
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "eval")
        self.assertIn("result", response)


class TestMuEdEvaluateExtraction(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SCHEMA_DIR"] = _SCHEMAS_DIR
        self.captured: dict = {}
        captured = self.captured

        def capturing_eval(response, answer, params):
            captured["response"] = response
            captured["answer"] = answer
            captured["params"] = params
            return {"is_correct": True, "feedback": "Captured."}

        commands.evaluation_function = capturing_eval
        return super().setUp()

    def tearDown(self) -> None:
        os.environ.pop("SCHEMA_DIR", None)
        commands.evaluation_function = None
        return super().tearDown()

    def test_math_submission_extracts_expression(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "task": {"title": "T", "referenceSolution": {"expression": "x+1"}},
            },
        }
        result = handler(event)
        self.assertEqual(self.captured["response"], "x+1")
        self.assertEqual(self.captured["answer"], "x+1")
        self.assertEqual(result[0]["awardedPoints"], True)  # type: ignore

    def test_text_submission_extracts_text(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "TEXT", "content": {"text": "hello"}},
                "task": {"title": "T", "referenceSolution": {"text": "hello"}},
            },
        }
        result = handler(event)
        self.assertEqual(self.captured["response"], "hello")
        self.assertEqual(self.captured["answer"], "hello")
        self.assertEqual(result[0]["awardedPoints"], True)  # type: ignore

    def test_configuration_params_forwarded(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "configuration": {"params": {"strict_syntax": False}},
            },
        }
        result = handler(event)
        self.assertEqual(self.captured["params"], {"strict_syntax": False})
        self.assertEqual(result[0]["awardedPoints"], True)  # type: ignore

    def test_no_task_answer_is_none(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
            },
        }
        result = handler(event)
        self.assertIsNone(self.captured["answer"])
        self.assertEqual(result[0]["awardedPoints"], True)  # type: ignore


class TestMuEdPreviewHandlerFunction(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SCHEMA_DIR"] = _SCHEMAS_DIR
        commands.preview_function = lambda response, params: {
            "preview": {"latex": f"\\text{{{response}}}", "sympy": response}
        }
        commands.evaluation_function = lambda response, answer, params: {
            "is_correct": True, "feedback": "Well done."
        }
        return super().setUp()

    def tearDown(self) -> None:
        os.environ.pop("SCHEMA_DIR", None)
        commands.preview_function = None
        commands.evaluation_function = None
        return super().tearDown()

    def test_preview_returns_feedback_list(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        response = handler(event)

        self.assertIsInstance(response, list)
        self.assertEqual(len(response), 1)

    def test_preview_feedback_id_is_preSubmissionFeedback(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        response = handler(event)

        self.assertNotIn("feedbackId", response[0])  # type: ignore

    def test_preview_contains_preSubmissionFeedback_field(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        response = handler(event)

        self.assertIn("preSubmissionFeedback", response[0])  # type: ignore

    def test_preview_preSubmissionFeedback_has_latex_and_sympy(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        response = handler(event)

        preview = response[0]["preSubmissionFeedback"]  # type: ignore
        self.assertIn("latex", preview)
        self.assertIn("sympy", preview)

    def test_preview_missing_submission_returns_error(self):
        event = {
            "path": "/evaluate",
            "body": {
                "configuration": {"params": {}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        response = handler(event)

        self.assertIn("error", response)

    def test_preview_bodyless_event_returns_error(self):
        event = {"path": "/evaluate", "random": "metadata"}

        response = handler(event)

        self.assertIn("error", response)
        self.assertEqual(
            response["error"]["message"],  # type: ignore
            "No data supplied in request body.",
        )

    def test_preview_invalid_submission_type_returns_error(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "INVALID", "content": {}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        response = handler(event)

        self.assertIn("error", response)

    def test_presubmission_disabled_runs_normal_evaluation(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "preSubmissionFeedback": {"enabled": False},
            },
        }

        response = handler(event)

        self.assertIsInstance(response, list)
        self.assertIn("awardedPoints", response[0])  # type: ignore
        self.assertNotIn("preSubmissionFeedback", response[0])  # type: ignore


class TestMuEdPreviewExtraction(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SCHEMA_DIR"] = _SCHEMAS_DIR
        self.captured: dict = {}
        captured = self.captured

        def capturing_preview(response, params):
            captured["response"] = response
            captured["params"] = params
            return {"preview": {"latex": "captured", "sympy": str(response)}}

        commands.preview_function = capturing_preview
        return super().setUp()

    def tearDown(self) -> None:
        os.environ.pop("SCHEMA_DIR", None)
        commands.preview_function = None
        return super().tearDown()

    def test_math_submission_extracts_expression(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        handler(event)

        self.assertEqual(self.captured["response"], "x+1")

    def test_text_submission_extracts_text(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "TEXT", "content": {"text": "hello"}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        handler(event)

        self.assertEqual(self.captured["response"], "hello")

    def test_configuration_params_forwarded(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "configuration": {"params": {"strict_syntax": False, "is_latex": True}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        handler(event)

        self.assertEqual(self.captured["params"], {"strict_syntax": False, "is_latex": True})

    def test_no_task_required(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "sin(x)"}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        response = handler(event)

        self.assertIsInstance(response, list)
        self.assertEqual(self.captured["response"], "sin(x)")

    def test_preview_result_propagated(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "preSubmissionFeedback": {"enabled": True},
            },
        }

        response = handler(event)

        self.assertEqual(response[0]["preSubmissionFeedback"]["latex"], "captured")  # type: ignore
        self.assertEqual(response[0]["preSubmissionFeedback"]["sympy"], "x+1")  # type: ignore


if __name__ == "__main__":
    unittest.main()