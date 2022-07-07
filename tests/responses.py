import unittest

from ..tools.validate import validate_response

class TestResponseValidation(unittest.TestCase):

    def test_empty_response_body(self):
        body = {}

        validation_error = validate_response(body)

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            validation_error.get("message"),
            "Schema threw an error when validating the response body.")

    def test_extra_fields(self):
        body = {
            "command": "grade",
            "result": {
                "is_correct": True
            },
            "hello": "world"
        }    

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            error_thrown.get("message"),
            "Additional properties are not allowed ('hello' was unexpected)"
        )

    def test_bad_command_wrong_type(self):
        body = {
            "command": {"not": "a command"},
            "result": {}
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            error_thrown.get("message"),
            "{'not': 'a command'} is not of type 'string'") 

    def test_bad_command_unallowed_option(self):
        body = {
            "command": "not a command",
            "result": {}
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            error_thrown.get("message"),
            "'not a command' is not one of ['grade', 'healthcheck']") 

    def test_bad_result_wrong_type(self):
        body = {
            "command": "grade", 
            "result": "an object"
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            error_thrown.get("message"),
            "'an object' is not of type 'object'")

    def test_bad_result_missing_is_correct_when_grading(self):
        body = {
            "command": "grade", 
            "result": {
                "feedback": "some feedback"
            }
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            error_thrown.get("message"),
            "'is_correct' is a required property")
    
    def test_bad_result_missing_tests_passed_when_checking_health(self):
        body = {
            "command": "healthcheck", 
            "result": {
                "successes": [],
                "failures": [],
                "errors": []
            }
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            error_thrown.get("message"),
            "'tests_passed' is a required property")
    
    def test_bad_error_wrong_type(self):
        body = {
            "error": "an object"
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            error_thrown.get("message"),
            "'an object' is not of type 'object'")

    def test_bad_error_missing_message(self):
        body = {
            "error": {
                "error_thrown": {
                    "message": "something specific"
                }
            }
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            error_thrown.get("message"),
            "'message' is a required property")  
     
    def test_missing_command(self):
        body = {
            "result": {
                "is_correct": True
            }
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)

        self.assertEqual(
            error_thrown.get("message"),
            "'command' is a required property")  

    def test_missing_result(self):
        body = {
            "command": "grade"
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)
        
        self.assertEqual(
            error_thrown.get("message"),
            "'error' is a required property") 

    def test_missing_command_with_error(self):
        body = {
            "result": {
                "is_correct": True
            },
            "error": {
                "message": "Some useful information."
            }
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)
        
        self.assertEqual(
            error_thrown.get("message"),
            "'command' is a required property",
        ) 

    def test_missing_result_with_error(self):
        body = {
            "command": "grade",
            "result": {
                "is_correct": True
            },
            "hello": "world"
        }

        validation_error = validate_response(body)
        error_thrown = validation_error.get("error_thrown")

        self.assertNotEqual(validation_error, None)
        
        self.assertEqual(
            error_thrown.get("message"),
            "Additional properties are not allowed ('hello' was unexpected)",
        )

    def test_valid_response_missing_command_and_result_with_error(self):
        body = {
            "error": {
                "message": "Something went wrong."
            }
        }

        validation_error = validate_response(body)
        self.assertEqual(validation_error, None)
        
    def test_valid_response_with_grade_command(self):
        body = {
            "command": "grade",
            "result": {
                "is_correct": True
            }
        }

        validation_error = validate_response(body)
        self.assertEqual(validation_error, None)

    def test_valid_response_with_healthcheck_command(self):
        body = {
            "command": "healthcheck", 
            "result": {
                "tests_passed": True,
                "successes": [{"name": "test_example", "time": 123}],
                "failures": [],
                "errors": []
            }
        }

        validation_error = validate_response(body)
        self.assertEqual(validation_error, None)


if __name__ == "__main__":
    unittest.main()
