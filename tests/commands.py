import unittest

from ..tools import commands  # noqa


class TestCommandsModule(unittest.TestCase):
    def test_valid_eval_command(self):
        ...

    def test_invalid_eval_args_raises_parse_error(self):
        ...

    def test_invalid_eval_schema_raises_validation_error(self):
        ...

    def test_single_feedback_case(self):
        ...

    def test_single_feedback_case_match(self):
        ...

    def test_case_warning_data_structure(self):
        ...

    def test_multiple_feedback_cases_single_match(self):
        ...

    def test_multiple_feedback_cases_multiple_matches(self):
        ...

    def test_invalid_case_entry_doesnt_raise_exception(self):
        ...

    def test_multiple_matched_cases_are_combined_and_warned(self):
        ...

    def test_overriding_eval_feedback_in_case(self):
        ...

    def test_overriding_is_correct_with_case_mark(self):
        ...

    def test_valid_preview_command(self):
        ...

    def test_invalid_preview_args_raises_parse_error(self):
        ...

    def test_invalid_preview_schema_raises_validation_error(self):
        ...

    def test_handle_healthcheck_command(self):
        ...


if __name__ == "__main__":
    unittest.main()
