import warnings
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, TypedDict

from evaluation_function_utils.errors import EvaluationException

from . import healthcheck as health
from . import parse, validate
from .utils import (
    EvaluationFunctionType,
    JsonType,
    PreviewFunctionType,
    Response,
)
from .validate import ReqBodyValidators

try:
    from ..evaluation import evaluation_function  # type: ignore

except ImportError:
    evaluation_function: Optional[EvaluationFunctionType] = None

    warnings.warn(
        "Evaluation function module could not be imported. "
        "`commands.evaluate()` will raise an exception."
    )

try:
    from ..preview import preview_function  # type: ignore

except ImportError:

    def preview_function(response: Any, params: Any) -> Dict:
        """Placeholder preview function if not already defined.

        This is for backwards compatibility. Eventually, this
        should be also set to None if an ImportError is raised.
        """
        return {"preview": response}

    warnings.warn(
        "Preview function could not be imported. "
        "Please update this evaluation function to use the latest version of "
        "the template, which should include a preview function and tests."
    )


class CaseWarning(TypedDict, total=False):
    """Dictionary for reporting issues when testing cases"""

    case: int
    message: str
    detail: str


class CaseResult(NamedTuple):
    """Tuple used to compile results from all cases."""

    is_correct: bool = False
    feedback: str = ""
    warning: Optional[CaseWarning] = None


def healthcheck() -> Response:
    """Run the healthcheck command for the evaluation function.

    Returns:
        Response: The body of the response returned by the handler.
    """
    result = health.healthcheck()
    return Response(command="healthcheck", result=result)


def preview(
    event: JsonType, fnc: Optional[PreviewFunctionType] = None
) -> Response:
    """Run the preview command for the evaluation function.

    Note:
        The body of the event is validated against the preview schema
        before running the preview function.

    Args:
        event (JsonType): The dictionary received by the gateway. Must
        include a body field which may be a JSON string or a dictionary.
        fnc (Optional[PreviewFunctionType]): A function to override the
        current preview function (for testing). Defaults to None.

    Returns:
        Response: The result given the response and params in the body.
    """
    body = parse.body(event)

    validate.body(body, ReqBodyValidators.PREVIEW)

    params = body.get("params", {})
    fnc = fnc or preview_function

    result = fnc(body["response"], params)

    return Response(command="preview", result=result)


def evaluate(event: JsonType) -> Response:
    """Run the evaluation command for the evaluation function.

    Note:
        The body of the event is validated against the eval schema
        before running the evaluation function.

        If cases are included in the params, this function checks for
        matching answers and returns the specified feedback.

    Args:
        event (JsonType): The dictionary received by the gateway. Must
        include a body field which may be a JSON string or a dictionary.
        fnc (Optional[EvaluationFunctionType]): A function to override the
        current evaluation function (for testing). Defaults to None.

    Returns:
        Response: The result given the response and params in the body.
    """
    body = parse.body(event)
    validate.body(body, ReqBodyValidators.EVALUATION)

    params = body.get("params", {})

    if evaluation_function is None:
        raise EvaluationException("Evaluation function is not defined.")

    result = evaluation_function(body["response"], body["answer"], params)

    if result["is_correct"] is False and "cases" in params and len(params["cases"]) > 0:
        match, warnings = get_case_feedback(
            body["response"], params, params["cases"]
        )

        if warnings:
            result["warnings"] = warnings

        if match is not None:
            result["feedback"] = match["feedback"]
            result["matched_case"] = match["id"]

            # Override is_correct provided by the
            # original block by the case 'mark'
            if "mark" in match:
                result["is_correct"] = bool(int(match["mark"]))

    return Response(command="eval", result=result)


def get_case_feedback(
    response: Any,
    params: Dict,
    cases: List[Dict],
) -> Tuple[Optional[Dict], List[CaseWarning]]:
    """Get the feedback case that matches an answer.

    Args:
        response (Any): The student response.
        params (Dict): The evaluation function params.
        cases (List[Dict]): The list of potential cases to check against.
        Must contain a feedback and answer field. May optionally contain
        a mark field to override the is_correct response from the
        evaluation function.

    Returns:
        Tuple[Optional[Dict], List[CaseWarning]]: The case that matched the
        student's response (null if no match was found) and a list of
        issues encountered when evaluating each case against the student's
        response.
    """
    # NOTE: Previous behaviour, where all cases are evaluated but only the feedback
    # for the first case is returned can be restored by changing the line below to:
    # matches, feedback, warnings = evaluate_all_cases(response, params, cases)
    matches, feedback, warnings = find_first_matching_case(response, params, cases)

    if not matches:
        return None, warnings

    match_id = matches[0]

    match = cases[match_id]
    match["id"] = match_id

    match_params = match.get("params", {})

    if match_params.get("override_eval_feedback", False):
        match_feedback = match.get("feedback", "")
        all_feedback = (match_feedback, feedback[0])
        match["feedback"] = "<br />".join(all_feedback)

    if len(matches) > 1:
        ids = ", ".join(map(str, matches))
        warning = CaseWarning(
            message=f"Cases {ids} were matched. "
            "Only the first one's feedback was returned"
        )

        warnings.append(warning)

    return match, warnings

def find_first_matching_case(
    response: Any,
    params: Dict,
    cases: List[Dict],
) -> Tuple[List[int], List[str], List[CaseWarning]]:
    """Evaluates cases until it finds matching one.

    Args:
        response (Any): The student's response.
        params (Dict): The params of the evaluation function.
        cases (List[Dict]): A list of cases to check against.

    Returns:
        Tuple[List[int], List[str], List[CaseWarning]]: Returns a list of
        indices of cases that match a student's response, a list of feedback
        strings from each case, and a list of issues encountered when
        evaluating cases against the student's response.
    """
    matches, feedback, warnings = [], [], []

    for index, case in enumerate(cases):
        result = evaluate_case(response, params, case, index)

        if result.warning is not None:
            warnings.append(result.warning)

        if result.is_correct:
            matches.append(index)
            feedback.append(result.feedback)
            break

    return matches, feedback, warnings

def evaluate_all_cases(
    response: Any,
    params: Dict,
    cases: List[Dict],
) -> Tuple[List[int], List[str], List[CaseWarning]]:
    """Loops through all cases and compiles the results.

    Args:
        response (Any): The student's response.
        params (Dict): The params of the evaluation function.
        cases (List[Dict]): A list of cases to check against.

    Returns:
        Tuple[List[int], List[str], List[CaseWarning]]: Returns a list of
        indices of cases that match a student's response, a list of feedback
        strings from each case, and a list of issues encountered when
        evaluating cases against the student's response.
    """
    matches, feedback, warnings = [], [], []

    for index, case in enumerate(cases):
        result = evaluate_case(response, params, case, index)

        if result.warning is not None:
            warnings.append(result.warning)

        if result.is_correct:
            matches.append(index)
            feedback.append(result.feedback)

    return matches, feedback, warnings


def evaluate_case(
    response: Any,
    params: Dict,
    case: Dict,
    index: int,
) -> CaseResult:
    """Evaluate a single case against a student's response.

    Args:
        response (Any): The student's response.
        params (Dict): The params of the evaluation function.
        case (Dict): The case to evaluate. Must contain a feedback and answer
        field. May optionally contain a mark field to override the is_correct
        result.
        index (int): The index of the case in the list of cases (as an id).

    Returns:
        CaseResult: The result of the case, including whether evaluated as
        correct, the feedback associated and the warning encountered
        (if any, else None).
    """
    if "answer" not in case or "feedback" not in case:
        warning = CaseWarning(
            case=index, message="Missing answer/feedback field"
        )

        return CaseResult(warning=warning)

    # Merge current evaluation params with any specified in case
    case_params = case.get("params", {})
    combined_params = {**params, **case_params}

    try:
        result = evaluation_function(
            response, case["answer"], combined_params
        )  # type: ignore

        return CaseResult(
            is_correct=result["is_correct"],
            feedback=result.get("feedback", ""),
        )

    # Catch exceptions and save as a warning.
    except EvaluationException as e:
        warning = CaseWarning(case=index, **e.error_dict)

    except Exception as e:
        warning = CaseWarning(
            case=index,
            message="An exception was raised while "
            "executing the evaluation function.",
            detail=(str(e) if str(e) != "" else repr(e)),
        )

    return CaseResult(warning=warning)
