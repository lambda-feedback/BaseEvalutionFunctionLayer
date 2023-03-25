import inspect
import unittest

import jsonschema

from . import docs, validate


class SmokeTests(unittest.TestCase):
    """Tests to check that all functions, files and tests are defined
    in the evaluation function by the user.

    Base Evaluation Function tests are no longer applied in the healthcheck,
    instead we only check that the necessary functions, classes and files
    are defined (here) and the user-defined tests pass.

    Base Evaluation Function tests are only applied when pushing to Docker.

    This test case also checks that all schemas are working appropriately.
    """

    def test_import_evaluation_function(self):
        from .. import evaluation  # type: ignore

        self.assertTrue(inspect.ismodule(evaluation))
        self.assertIsNotNone(evaluation.evaluation_function)

    @unittest.skip("Ignored until all functions are updated with preview.")
    def test_import_preview_function(self):
        from .. import preview  # type: ignore

        self.assertTrue(inspect.ismodule(preview))
        self.assertIsNotNone(preview.preview_function)

    def test_import_evaluation_tests(self):
        from .. import evaluation_tests  # type: ignore

        self.assertTrue(inspect.ismodule(evaluation_tests))
        self.assertIsNotNone(evaluation_tests.TestEvaluationFunction)

    @unittest.skip("Ignored until all functions are updated with preview.")
    def test_import_preview_tests(self):
        from .. import preview_tests  # type: ignore

        self.assertTrue(inspect.ismodule(preview_tests))
        self.assertIsNotNone(preview_tests.TestPreviewFunction)

    def test_load_dev_docs(self):
        result = docs.dev()

        self.assertEqual(result["statusCode"], 200)
        self.assertDictEqual(
            result["headers"], {"Content-Type": "application/octet-stream"}
        )
        self.assertTrue(result["isBase64Encoded"])

    def test_load_user_docs(self):
        result = docs.user()

        self.assertEqual(result["statusCode"], 200)
        self.assertDictEqual(
            result["headers"], {"Content-Type": "application/octet-stream"}
        )
        self.assertTrue(result["isBase64Encoded"])

    def test_load_eval_req_schema(self):
        schema = validate.load_validator_from_url(
            validate.ReqBodyValidators.EVALUATION
        )

        self.assertIsInstance(schema, jsonschema.Draft7Validator)

    def test_load_preview_req_schema(self):
        schema = validate.load_validator_from_url(
            validate.ReqBodyValidators.PREVIEW
        )

        self.assertIsInstance(schema, jsonschema.Draft7Validator)

    def test_load_eval_res_schema(self):
        schema = validate.load_validator_from_url(
            validate.ResBodyValidators.EVALUATION
        )

        self.assertIsInstance(schema, jsonschema.Draft7Validator)

    def test_load_preview_res_schema(self):
        schema = validate.load_validator_from_url(
            validate.ResBodyValidators.PREVIEW
        )

        self.assertIsInstance(schema, jsonschema.Draft7Validator)

    def test_load_health_res_schema(self):
        schema = validate.load_validator_from_url(
            validate.ResBodyValidators.HEALTHCHECK
        )

        self.assertIsInstance(schema, jsonschema.Draft7Validator)
