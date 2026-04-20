import json
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
        self._orig_eval = commands.evaluation_function
        commands.evaluation_function = evaluation_function
        return super().setUp()

    def tearDown(self) -> None:
        os.environ.pop("SCHEMA_DIR", None)
        commands.evaluation_function = self._orig_eval
        return super().tearDown()

    def test_evaluate_returns_feedback_list(self):
        event = {
            "path": "/evaluate",
            "body": {"submission": {"type": "TEXT", "content": {}}},
        }

        response = handler(event)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 1)
        self.assertIn("awardedPoints", body[0])

    def test_evaluate_feedback_message(self):
        event = {
            "path": "/evaluate",
            "body": {"submission": {"type": "TEXT", "content": {"text": "hello"}}},
        }

        response = handler(event)

        body = json.loads(response["body"])
        self.assertEqual(body[0]["message"], "Well done.")
        self.assertEqual(body[0]["awardedPoints"], True)

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

        body = json.loads(response["body"])
        self.assertIsInstance(body, list)

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
        event = {"path": "/evaluate/health"}

        response = handler(event)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["X-Api-Version"], "0.1.0")
        body = json.loads(response["body"])
        self.assertIn(body.get("status"), ("OK", "DEGRADED", "UNAVAILABLE"))
        capabilities = body.get("capabilities", {})
        self.assertIn("supportedAPIVersions", capabilities)
        self.assertIn("0.1.0", capabilities["supportedAPIVersions"])

    def test_supported_version_header_is_accepted(self):
        event = {
            "path": "/evaluate/health",
            "headers": {"X-Api-Version": "0.1.0"},
        }

        response = handler(event)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["headers"]["X-Api-Version"], "0.1.0")
        body = json.loads(response["body"])
        self.assertIn(body.get("status"), ("OK", "DEGRADED", "UNAVAILABLE"))

    def test_unsupported_version_header_returns_error(self):
        event = {
            "path": "/evaluate",
            "headers": {"X-Api-Version": "99.0.0"},
            "body": {"submission": {"type": "TEXT", "content": {}}},
        }

        response = handler(event)

        self.assertEqual(response["statusCode"], 406)
        self.assertEqual(response["headers"]["X-Api-Version"], "0.1.0")
        body = json.loads(response["body"])
        self.assertEqual(body.get("code"), "VERSION_NOT_SUPPORTED")
        self.assertIn("details", body)
        self.assertEqual(body["details"]["requestedVersion"], "99.0.0")
        self.assertIn("0.1.0", body["details"]["supportedVersions"])

    def test_absent_version_header_proceeds_normally(self):
        event = {"path": "/evaluate/health"}

        response = handler(event)

        self.assertEqual(response["headers"]["X-Api-Version"], "0.1.0")
        body = json.loads(response["body"])
        self.assertNotIn("code", body)

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
        self._orig_eval = commands.evaluation_function
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
        commands.evaluation_function = self._orig_eval
        return super().tearDown()

    def test_math_submission_extracts_expression(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "task": {"title": "T", "referenceSolution": {"expression": "x+1"}},
            },
        }
        result = json.loads(handler(event)["body"])
        self.assertEqual(self.captured["response"], "x+1")
        self.assertEqual(self.captured["answer"], "x+1")
        self.assertEqual(result[0]["awardedPoints"], True)

    def test_text_submission_extracts_text(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "TEXT", "content": {"text": "hello"}},
                "task": {"title": "T", "referenceSolution": {"text": "hello"}},
            },
        }
        result = json.loads(handler(event)["body"])
        self.assertEqual(self.captured["response"], "hello")
        self.assertEqual(self.captured["answer"], "hello")
        self.assertEqual(result[0]["awardedPoints"], True)

    def test_configuration_params_forwarded(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "configuration": {"params": {"strict_syntax": False}},
            },
        }
        result = json.loads(handler(event)["body"])
        self.assertEqual(self.captured["params"], {"strict_syntax": False})
        self.assertEqual(result[0]["awardedPoints"], True)

    def test_no_task_answer_is_none(self):
        event = {
            "path": "/evaluate",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
            },
        }
        result = json.loads(handler(event)["body"])
        self.assertIsNone(self.captured["answer"])
        self.assertEqual(result[0]["awardedPoints"], True)


class TestMuEdPreviewHandlerFunction(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SCHEMA_DIR"] = _SCHEMAS_DIR
        self._orig_preview = commands.preview_function
        commands.preview_function = lambda response, params: {
            "preview": {"latex": f"\\text{{{response}}}", "sympy": response}
        }
        return super().setUp()

    def tearDown(self) -> None:
        os.environ.pop("SCHEMA_DIR", None)
        commands.preview_function = self._orig_preview
        return super().tearDown()

    def test_preview_returns_feedback_list(self):
        event = {
            "path": "/preview",
            "body": {"submission": {"type": "MATH", "content": {"expression": "x+1"}}},
        }

        response = handler(event)

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 1)

    def test_preview_feedback_id_is_preSubmissionFeedback(self):
        event = {
            "path": "/preview",
            "body": {"submission": {"type": "MATH", "content": {"expression": "x+1"}}},
        }

        body = json.loads(handler(event)["body"])

        self.assertNotIn("feedbackId", body[0])

    def test_preview_contains_preSubmissionFeedback_field(self):
        event = {
            "path": "/preview",
            "body": {"submission": {"type": "MATH", "content": {"expression": "x+1"}}},
        }

        body = json.loads(handler(event)["body"])

        self.assertIn("preSubmissionFeedback", body[0])

    def test_preview_preSubmissionFeedback_has_latex_and_sympy(self):
        event = {
            "path": "/preview",
            "body": {"submission": {"type": "MATH", "content": {"expression": "x+1"}}},
        }

        body = json.loads(handler(event)["body"])

        preview = body[0]["preSubmissionFeedback"]
        self.assertIn("latex", preview)
        self.assertIn("sympy", preview)

    def test_preview_missing_submission_returns_error(self):
        event = {
            "path": "/preview",
            "body": {"configuration": {"params": {}}},
        }

        response = handler(event)

        self.assertIn("error", response)

    def test_preview_bodyless_event_returns_error(self):
        event = {"path": "/preview", "random": "metadata"}

        response = handler(event)

        self.assertIn("error", response)
        self.assertEqual(
            response["error"]["message"],  # type: ignore
            "No data supplied in request body.",
        )

    def test_preview_invalid_submission_type_returns_error(self):
        event = {
            "path": "/preview",
            "body": {"submission": {"type": "INVALID", "content": {}}},
        }

        response = handler(event)

        self.assertIn("error", response)


class TestMuEdPreviewExtraction(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SCHEMA_DIR"] = _SCHEMAS_DIR
        self._orig_preview = commands.preview_function
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
        commands.preview_function = self._orig_preview
        return super().tearDown()

    def test_math_submission_extracts_expression(self):
        event = {
            "path": "/preview",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
            },
        }

        handler(event)

        self.assertEqual(self.captured["response"], "x+1")

    def test_text_submission_extracts_text(self):
        event = {
            "path": "/preview",
            "body": {
                "submission": {"type": "TEXT", "content": {"text": "hello"}},
            },
        }

        handler(event)

        self.assertEqual(self.captured["response"], "hello")

    def test_configuration_params_forwarded(self):
        event = {
            "path": "/preview",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
                "configuration": {"params": {"strict_syntax": False, "is_latex": True}},
            },
        }

        handler(event)

        self.assertEqual(self.captured["params"], {"strict_syntax": False, "is_latex": True})

    def test_no_task_required(self):
        event = {
            "path": "/preview",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "sin(x)"}},
            },
        }

        response = handler(event)

        body = json.loads(response["body"])
        self.assertIsInstance(body, list)
        self.assertEqual(self.captured["response"], "sin(x)")

    def test_preview_result_propagated(self):
        event = {
            "path": "/preview",
            "body": {
                "submission": {"type": "MATH", "content": {"expression": "x+1"}},
            },
        }

        body = json.loads(handler(event)["body"])

        self.assertEqual(body[0]["preSubmissionFeedback"]["latex"], "captured")
        self.assertEqual(body[0]["preSubmissionFeedback"]["sympy"], "x+1")


if __name__ == "__main__":
    unittest.main()
