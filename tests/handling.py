import unittest

from ..tools.handler import handler

class TestHandlerFunction(unittest.TestCase):

    def test_handle_bodyless_event(self):
        event = {
            "random": "metadata",
            "without": "a body"
        }

        response = handler(event)

        self.assertIn("error", response)
        error = response.get("error")

        self.assertEqual(
            error.get("message"), 
            "No grading data supplied in request body.")

    def test_non_json_body(self):
        event = {
            "random": "metadata",
            "body": "{}}}{{{[][] this is not json."
        }

        response = handler(event)

        self.assertIn("error", response)
        error = response.get("error")

        self.assertEqual(
            error.get("message"),
            "Request body is not valid JSON.")

    def test_grade(self):
        event = {
            "random": "metadata",
            "body": {
                "response": "hello",
                "answer": "world!",
                "params": {}
            },
            "headers": {
                "command": "grade"
            }
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "grade")
        self.assertIn("result", response)

    def test_grade_no_params(self):
        event = {
            "random": "metadata",
            "body": {
                "response": "hello",
                "answer": "world!"
            }
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "grade")
        self.assertIn("result", response)

    def test_healthcheck(self):
        event = {
            "random": "metadata",
            "body": "{}",
            "headers": {
                "command": "healthcheck"
            }
        }

        response = handler(event)

        self.assertEqual(response.get("command"), "healthcheck")
        self.assertIn("result", response)

        result = response.get("result")

        self.assertTrue(result.get("tests_passed"))

    def test_invalid_command(self):
        event = {
            "random": "metadata",
            "body": "{}",
            "headers": {
                "command": "not a command"
            }
        }

        response = handler(event)
        error = response.get("error")
    
        self.assertEqual(
            error.get("message"),
            "Unknown command 'not a command'.")

if __name__ == "__main__":
    unittest.main()