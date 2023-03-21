import unittest

from ..tools import parse


class TestParseModule(unittest.TestCase):
    def test_valid_json_string(self):
        result = parse.body({"body": '{"hello": "world", "answer": 1}'})
        self.assertDictEqual(result, {"hello": "world", "answer": 1})

    def test_valid_dictionary(self):
        result = parse.body({"body": {"hello": "world", "answer": 1}})
        self.assertDictEqual(result, {"hello": "world", "answer": 1})

    def test_null_object_raises_parse_error(self):
        with self.assertRaises(parse.ParseError) as e:
            parse.body({"body": None})

        self.assertEqual(
            e.exception.message, "No data supplied in request body."
        )

    def test_invalid_json_string_raises_parse_error(self):
        with self.assertRaises(parse.ParseError) as e:
            parse.body({"body": '{"hello": "world", "answer": 1} }'})

        self.assertEqual(
            e.exception.message, "Request body is not valid JSON."
        )

    def test_decode_detail_data_structure(self):
        with self.assertRaises(parse.ParseError) as e:
            parse.body({"body": '{"hello": "world", "answer": 1} }'})

        self.assertEqual(
            e.exception.message, "Request body is not valid JSON."
        )

        self.assertDictEqual(
            e.exception.error_thrown,  # type: ignore
            {"message": "Extra data", "location": {"line": 1, "column": 33}},
        )

    def test_generic_exception_returns_detail(self):
        with self.assertRaises(parse.ParseError) as e:
            parse.body({"body": lambda x: x**2})

        self.assertEqual(
            e.exception.message, "Request body is not valid JSON."
        )

        self.assertEqual(
            e.exception.error_thrown,
            "the JSON object must be str, bytes or bytearray, not function",
        )
