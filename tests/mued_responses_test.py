import unittest

from ..tools import validate
from ..tools.validate import MuEdResBodyValidators, ValidationError


class TestMuEdResponseValidation(unittest.TestCase):

    def test_non_list_response(self):
        body = {}

        with self.assertRaises(ValidationError) as e:
            validate.body(body, MuEdResBodyValidators.EVALUATION)

        self.assertEqual(
            e.exception.message,
            "Failed to validate body against the evaluation schema.",
        )

    def test_valid_empty_list(self):
        body = []
        validate.body(body, MuEdResBodyValidators.EVALUATION)

    def test_valid_minimal_feedback(self):
        body = [{"message": "Good attempt."}]
        validate.body(body, MuEdResBodyValidators.EVALUATION)

    def test_extra_fields_allowed(self):
        # Feedback uses extra='allow' — unknown fields should not raise
        body = [{"unknown_field": "value"}]
        validate.body(body, MuEdResBodyValidators.EVALUATION)

    def test_valid_full_feedback(self):
        body = [
            {
                "title": "Correctness",
                "message": "Your answer is correct.",
                "suggestedAction": "Review the concept further.",
                "criterion": {"name": "Correctness", "context": "Is the answer correct?"},
                "target": {"artefactType": "TEXT"},
            }
        ]
        validate.body(body, MuEdResBodyValidators.EVALUATION)

    def test_multiple_feedback_items(self):
        body = [
            {"message": "Well structured."},
            {"message": "Good use of examples."},
        ]
        validate.body(body, MuEdResBodyValidators.EVALUATION)


if __name__ == "__main__":
    unittest.main()