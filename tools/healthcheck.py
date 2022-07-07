import unittest
import time
import os
import sys
import re

from ..tests.requests import TestRequestValidation
from ..tests.responses import TestResponseValidation

from ...grading_tests import TestGradingFunction

"""
    Extension of the default TestResult class with timing information.
"""

class HealthcheckResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__path_re = re.compile(r"^[\.\/\w]+\.(\w+\.\w+)$")

        self.__successes_json = []
        self.__failures_json = []
        self.__errors_json = []

    def removePathFromId(self, path):
        path_match = self.__path_re.match(path)

        if path_match is None:
            return "Unknown"

        return path_match.group(1)

    def startTest(self, test):
        self._start_time = time.time()
        super().startTest(test)

    def addSuccess(self, test):
        elapsed_time_s = time.time() - self._start_time
        elapsed_time_us = round(1000000 * elapsed_time_s)
        
        self.__successes_json.append({
            "name": self.removePathFromId(test.id()), 
            "time": elapsed_time_us
        })

        super().addSuccess(test)

    def addFailure(self, test, err):
        self.__failures_json.append({
            "name": self.removePathFromId(test.id())
        })

        super().addFailure(test, err)

    def addError(self, test, err):
        self.__errors_json.append({
            "name": self.removePathFromId(test.id())
        })

        super().addError(test, err)

    def getSuccessesJSON(self):
        return self.__successes_json

    def getFailuresJSON(self):
        return self.__failures_json

    def getErrorsJSON(self):
        return self.__errors_json

"""
    Extension of the default TestRunner class that returns a JSON-encodable result
"""

class HealthcheckRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        return super().__init__(resultclass=HealthcheckResult, *args, **kwargs)
    
    def run(self, test):
        """
        Extension to the original run method that returns the results in a JSON-encodable format.
        ---
        This includes:
            - `tests_passed` (bool): Whether all tests were successful.
            - `successes` (list): A list of all passing tests, including the name and
                time taken to complete in microseconds.
            - `failures` (list): A list of all tests that failed, including the name and
                traceback of failures.
            - `errors` (list): A list of all tests that caused an error, including the
                name and traceback of failures.
        """
        result = super().run(test)

        results = {
            "tests_passed": result.wasSuccessful(),
            "successes": result.getSuccessesJSON(), 
            "failures": result.getFailuresJSON(), 
            "errors": result.getErrorsJSON()
        }

        return results

def healthcheck() -> dict:
    """
    Function used to return the results of the unittests in a JSON-encodable format.
    ---
    Therefore, this can be used as a healthcheck to make sure the algorithm is 
    running as expected, and isn't taking too long to complete due to, e.g., issues 
    with load balancing.
    """
    # Redirect stderr stream to a null stream so the unittests are not logged on the console.
    no_stream = open(os.devnull, 'w')
    sys.stderr = no_stream

    # Create a test loader and test runner instance
    loader = unittest.TestLoader()

    request_tests = loader.loadTestsFromTestCase(TestRequestValidation)
    response_tests = loader.loadTestsFromTestCase(TestResponseValidation)
    grading_tests = loader.loadTestsFromTestCase(TestGradingFunction)

    suite = unittest.TestSuite([
        request_tests, 
        response_tests, 
        grading_tests])
    
    runner = HealthcheckRunner(verbosity=0)

    result = runner.run(suite)

    # Reset stderr and close the null stream
    sys.stderr = sys.__stderr__
    no_stream.close()

    return result