import os
import re
import sys
import time
import unittest
from typing import Any, List, TypedDict

from typing_extensions import NotRequired

from ..tests.requests import TestRequestValidation
from ..tests.responses import TestResponseValidation

try:
    from ..evaluation_tests import TestEvaluationFunction  # type: ignore
except ImportError:
    TestEvaluationFunction = None

try:
    from ..preview_tests import TestPreviewFunction  # type: ignore
except ImportError:
    TestPreviewFunction = None

"""
    Extension of the default TestResult class with timing information.
"""


class JsonTestResult(TypedDict):
    name: str
    time: NotRequired[int]


JsonTestResults = List[JsonTestResult]


class HealthcheckJsonTestResult(TypedDict):
    tests_passed: bool
    successes: JsonTestResults
    failures: JsonTestResults
    errors: JsonTestResults


class HealthcheckResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.__path_re = re.compile(r"^[\.\/\w]+\.(\w+\.\w+)$")

        self.__successes_json: JsonTestResults = []
        self.__failures_json: JsonTestResults = []
        self.__errors_json: JsonTestResults = []

    def removePathFromId(self, path: str) -> str:
        path_match = self.__path_re.match(path)

        if path_match is None:
            return "Unknown"

        return path_match.group(1)

    def startTest(self, test: unittest.TestCase) -> None:
        self._start_time = time.time()
        super().startTest(test)

    def addSuccess(self, test: unittest.TestCase) -> None:
        elapsed = time.time() - self._start_time

        self.__successes_json.append(
            JsonTestResult(
                name=self.removePathFromId(test.id()),
                time=round(1e6 * elapsed),
            )
        )

        super().addSuccess(test)

    def addFailure(self, test: unittest.TestCase, err: Any) -> None:
        self.__failures_json.append(
            JsonTestResult(name=self.removePathFromId(test.id()))
        )

        super().addFailure(test, err)

    def addError(self, test: unittest.TestCase, err: Any) -> None:
        self.__errors_json.append(
            JsonTestResult(name=self.removePathFromId(test.id()))
        )

        super().addError(test, err)

    def getSuccessesJSON(self) -> JsonTestResults:
        return self.__successes_json

    def getFailuresJSON(self) -> JsonTestResults:
        return self.__failures_json

    def getErrorsJSON(self) -> JsonTestResults:
        return self.__errors_json


"""
    Extension of the default TestRunner class that returns a JSON-encodable
      result
"""


class HealthcheckRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs) -> None:
        return super().__init__(resultclass=HealthcheckResult, *args, **kwargs)

    def run(self, test) -> HealthcheckJsonTestResult:
        """
        Extension to the original run method that returns the results in a
          JSON-encodable format.
        ---
        This includes:
            - `tests_passed` (bool): Whether all tests were successful.
            - `successes` (list): A list of all passing tests, including
            the name and
                time taken to complete in microseconds.
            - `failures` (list): A list of all tests that failed, including
              the name and
                traceback of failures.
            - `errors` (list): A list of all tests that caused an error,
            including the
                name and traceback of failures.
        """
        result: HealthcheckResult = super().run(test)  # type: ignore

        return HealthcheckJsonTestResult(
            tests_passed=result.wasSuccessful(),
            successes=result.getSuccessesJSON(),
            failures=result.getFailuresJSON(),
            errors=result.getErrorsJSON(),
        )


def healthcheck() -> HealthcheckJsonTestResult:
    """
    Function used to return the results of the unittests in a JSON-encodable
      format.
    ---
    Therefore, this can be used as a healthcheck to make sure the algorithm is
    running as expected, and isn't taking too long to complete due to, e.g.,
      issues
    with load balancing.
    """
    # Redirect stderr stream to a null stream so the unittests are not logged
    #  on the console.
    no_stream = open(os.devnull, "w")
    sys.stderr = no_stream

    # Create a test loader and test runner instance
    loader = unittest.TestLoader()

    cases = (
        TestRequestValidation,
        TestResponseValidation,
        TestEvaluationFunction,
        TestPreviewFunction,
    )

    tests = [loader.loadTestsFromTestCase(c) for c in cases if c is not None]

    suite = unittest.TestSuite(tests)
    runner = HealthcheckRunner(verbosity=0)

    result = runner.run(suite)

    # Reset stderr and close the null stream
    sys.stderr = sys.__stderr__
    no_stream.close()

    return result
