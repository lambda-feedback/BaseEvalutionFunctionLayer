import base64
import unittest

from ..tools import docs


class TestDocsModule(unittest.TestCase):
    def test_handling_available_doc(self):
        result = docs.send_file("tests/test_file.md")

        self.assertEqual(result["statusCode"], 200)
        self.assertDictEqual(
            result["headers"], {"Content-Type": "application/octet-stream"}
        )
        self.assertTrue(result["isBase64Encoded"])

        self.assertEqual(
            result["body"], base64.encodebytes(b"# Test file\n").decode()
        )

    def test_handling_missing_doc(self):
        result = docs.send_file("tests/non-existent-doc.md")

        self.assertEqual(result["statusCode"], 200)
        self.assertDictEqual(
            result["headers"], {"Content-Type": "application/octet-stream"}
        )
        self.assertFalse(result["isBase64Encoded"])

        self.assertEqual(
            result["body"],
            "tests/non-existent-doc.md missing from evaluation function files",
        )

    """Can't test available dev docs without the layer above."""

    def test_handling_missing_user_docs(self):
        result = docs.user()

        self.assertEqual(result["statusCode"], 200)
        self.assertDictEqual(
            result["headers"], {"Content-Type": "application/octet-stream"}
        )
        self.assertFalse(result["isBase64Encoded"])

        self.assertEqual(
            result["body"],
            "app/docs/user.md missing from evaluation function files",
        )

    def test_handling_missing_dev_docs(self):
        result = docs.dev()

        self.assertEqual(result["statusCode"], 200)
        self.assertDictEqual(
            result["headers"], {"Content-Type": "application/octet-stream"}
        )
        self.assertFalse(result["isBase64Encoded"])

        self.assertEqual(
            result["body"],
            "app/docs/dev.md missing from evaluation function files",
        )


if __name__ == "__main__":
    unittest.main()
