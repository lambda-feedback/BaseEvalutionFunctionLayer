import os
import re
import sys
import time
import unittest
from typing import Any, List, TypedDict

from typing_extensions import NotRequired

from .smoke_tests import SmokeTests

try:
    from ..evaluation_tests import TestEvaluationFunction  # type: ignore
except ImportError:
    TestEvaluationFunction = None

try:
    from ..preview_tests import TestPreviewFunction  # type: ignore
except ImportError:
    TestPreviewFunction = None


class JsonTestResult(TypedDict):
    """JSON-serialisable result of a single unit test."""

    name: str
    time: NotRequired[int]


JsonTestResults = List[JsonTestResult]


class HealthcheckJsonTestResult(TypedDict):
    """The result object returned by the healthcheck command."""

    tests_passed: bool
    successes: JsonTestResults
    failures: JsonTestResults
    errors: JsonTestResults


class HealthcheckResult(unittest.TextTestResult):
    """Extension of the default TestResult class with timing information."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.__path_re = re.compile(r"^[\.\/\w]+\.(\w+\.\w+)$")

        self.__successes_json: JsonTestResults = []
        self.__failures_json: JsonTestResults = []
        self.__errors_json: JsonTestResults = []

    def removePathFromId(self, path: str) -> str:
        """Remove the full path of the unit test, keeping only its name."""
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


class HealthcheckRunner(unittest.TextTestRunner):
    """Extends the TestRunner class to returns a JSON-serialisable result."""

    def __init__(self, *args, **kwargs) -> None:
        return super().__init__(resultclass=HealthcheckResult, *args, **kwargs)

    def run(self, test) -> HealthcheckJsonTestResult:
        result: HealthcheckResult = super().run(test)  # type: ignore

        return HealthcheckJsonTestResult(
            tests_passed=result.wasSuccessful(),
            successes=result.getSuccessesJSON(),
            failures=result.getFailuresJSON(),
            errors=result.getErrorsJSON(),
        )


def healthcheck() -> HealthcheckJsonTestResult:
    """Get the result of a healthcheck by running all unit tests.

    Returns:
        HealthcheckJsonTestResult: The result object returned to the
        healthcheck command function.
    """
    # Redirect stderr stream to null to prevent logging unittest results
    no_stream = open(os.devnull, "w")
    # sys.stderr = no_stream

    # Create a test loader and test runner instance
    loader = unittest.TestLoader()

    cases = (
        SmokeTests,
        TestEvaluationFunction,
        TestPreviewFunction,
    )

    # Filter undefined test cases (i.e. evaluation and preview if deleted.)
    tests = [loader.loadTestsFromTestCase(c) for c in cases if c is not None]

    suite = unittest.TestSuite(tests)
    runner = HealthcheckRunner(verbosity=0)

    result = runner.run(suite)

    # Reset stderr and close the null stream
    sys.stderr = sys.__stderr__
    no_stream.close()

    return result
