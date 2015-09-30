import logging
import unittest
import mocker

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)


class TestArgumentParsing(unittest.TestCase):

    def test_process_dict_arg(self):
        # Valid dict
        test_in = r"{ 'a':'hello', 'b': 123, 'c':True }"
        expected = {'a': 'hello', 'b': 123, 'c': True}
        test_out = mocker.process_dict_arg(test_in)
        self.assertEqual(expected, test_out, "Should be a valid dict.")
        # Unexpected indentation
        test_in = r"   { 'a':'hello',    'b': 123,    'c':True }   "
        expected = {'a': 'hello', 'b': 123, 'c': True}
        test_out = mocker.process_dict_arg(test_in)
        self.assertEqual(expected, test_out, "Should handle whitespace.")
        # Escape characters
        test_in = "{ 'a':'he\\ll\ao\\\\World\S' }"
        expected = {'a': 'he\\ll\ao\\World\\S'}
        test_out = mocker.process_dict_arg(test_in)
        self.assertEqual(expected, test_out, "Should handle escape characters.")
        # empty str
        test_in = ""
        with self.assertRaises(ValueError, msg="Should raise ValueError for empty str."):
            mocker.process_dict_arg(test_in)
        # List
        test_in = "[{'a':'hello'}]"
        with self.assertRaises(ValueError, msg="Should raise ValueError for non dict args."):
            mocker.process_dict_arg(test_in)
        # incorrect syntax
        test_in = "[{'a':'hello'}"
        with self.assertRaises(ValueError, msg="Should raise ValueError for incorrect syntax."):
            mocker.process_dict_arg(test_in)

if __name__ == '__main__':
    unittest.main()
