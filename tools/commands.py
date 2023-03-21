from typing import Any, Dict, List, NamedTuple, Optional, Tuple, TypedDict

from evaluation_function_utils.errors import EvaluationException

from . import healthcheck as health
from . import parse, validate
from .utils import JsonType, Response
from .validate import ReqBodyValidators

try:
    from ..evaluate import evaluation_function  # type: ignore
except ImportError:

    def evaluation_function(response: Any, answer: Any, params: Any) -> Dict:
        return {"is_correct": True}


try:
    from ..preview import preview_function  # type: ignore
except ImportError:

    def preview_function(response: Any, params: Any) -> Dict:
        return {"preview": response}


class CaseWarning(TypedDict, total=False):
    case: int
    message: str
    detail: str


class CaseResult(NamedTuple):
    is_correct: bool = False
    feedback: str = ""
    warning: Optional[CaseWarning] = None


def healthcheck() -> Response:
    result = health.healthcheck()
    return Response(command="healthcheck", result=result)


def preview(event: JsonType):
    """
    Function to create the response when commanded to preview an answer.
    ---
    This function attempts to parse the request body, performs schema
    validation and
    attempts to run the evaluation function on the given parameters.

    If any of these fail, a message is returned and an error field is
    passed if more
    information can be provided.
    """
    body = parse.body(event)

    validate.body(body, ReqBodyValidators.PREVIEW)

    params = body.get("params", {})
    result = preview_function(body["response"], params)

    return Response(command="preview", result=result)


def evaluate(event: JsonType) -> Response:
    """
    Function to create the response when commanded to evaluate an answer.
    ---
    This function attempts to parse the request body, performs schema
      validation and
    attempts to run the evaluation function on the given parameters.

    If any of these fail, a message is returned and an error field is
      passed if more
    information can be provided.
    """

    body = parse.body(event)
    validate.body(body, ReqBodyValidators.EVALUATION)

    params = body.get("params", {})
    result = evaluation_function(body["response"], body["answer"], params)

    if "cases" in params and len(params["cases"]) > 0:
        # Determine what feedback to provide based on cases
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

        # Add warnings out output if any were encountered

    return Response(command="eval", result=result)


def get_case_feedback(
    response: Any, params: Dict, cases: List[Dict]
) -> Tuple[Optional[Dict], List[CaseWarning]]:
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
    # Validate the case block has an answer and feedback
    if "answer" not in case or "feedback" not in case:
        warning = CaseWarning(
            case=index, message="Missing answer/feedback field"
        )

        return CaseResult(warning=warning)

    # Merge current evaluation params with any specified in case
    case_params = case.get("params", {})

    # Run the evaluation function based on this case's answer
    try:
        result = evaluation_function(
            response, case["answer"], {**params, **case_params}
        )

        return CaseResult(
            is_correct=result["is_correct"],
            feedback=result.get("feedback", ""),
        )

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
