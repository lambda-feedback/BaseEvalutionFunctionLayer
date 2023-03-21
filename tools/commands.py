from typing import Any, Dict, List, NamedTuple, Optional, Tuple, TypedDict

from evaluation_function_utils.errors import EvaluationException

from ..evaluate import evaluation_function  # type: ignore
from . import healthcheck as health
from . import parse, validate
from .utils import JsonType, Response
from .validate import ReqBodyValidators

try:
    from ..preview import preview_function  # type: ignore
except ImportError:

    def preview_function(response: Any, params: Any) -> Dict:
        """Placeholder preview function if not already defined."""
        return {"preview": response}


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


def preview(event: JsonType) -> Response:
    """Run the preview command for the evaluation function.

    Note:
        The body of the event is validated against the preview schema
        before running the preview function.

    Args:
        event (JsonType): The dictionary received by the gateway. Must
        include a body field which may be a JSON string or a dictionary.

    Returns:
        Response: The result given the response and params in the body.
    """
    body = parse.body(event)

    validate.body(body, ReqBodyValidators.PREVIEW)

    params = body.get("params", {})
    result = preview_function(body["response"], params)

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

    Returns:
        Response: The result given the response and params in the body.
    """
    body = parse.body(event)
    validate.body(body, ReqBodyValidators.EVALUATION)

    params = body.get("params", {})
    result = evaluation_function(body["response"], body["answer"], params)

    if "cases" in params and len(params["cases"]) > 0:
        match, warnings = get_case_feedback(
            body["response"], params, params["cases"]
        )

        if warnings:
            result["warnings"] = warnings

        if match is not None:
            result["feedback"] = match["feedback"]
            result["match"] = match["id"]

            # Override is_correct provided by the
            # original block by the case 'mark'
            if "mark" in match:
                result["is_correct"] = bool(int(match["mark"]))

    return Response(command="eval", result=result)


def get_case_feedback(
    response: Any, params: Dict, cases: List[Dict]
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
    matches, feedback, warnings = evaluate_all_cases(response, params, cases)

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


def evaluate_all_cases(
    response: Any, params: Dict, cases: List[Dict]
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
    response: Any, params: Dict, case: Dict, index: int
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

    try:
        result = evaluation_function(
            response, case["answer"], {**params, **case_params}
        )

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
