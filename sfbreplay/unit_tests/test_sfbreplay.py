import logging
import unittest
import sfbreplay

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)


# class TestMockerConfiguration(unittest.TestCase):

#     def test_valid_xml(self):
#         msg = MockerConfiguration.fromstring(XML_1)
#         self.assertTrue(isinstance(msg, MockerConfiguration),
#                         msg="valid xml Should be an instance of MockerConfiguration.")

#     def test_invalid_mxl(self):
#         # Malformed Tag
#         test_input = "<test</test>"
#         with self.assertRaises(ET.XMLSyntaxError,
#                                msg="Should raise XMLSyntaxError for malformed tag."):
#             MockerConfiguration.fromstring(test_input)
#         # Empty string
#         test_input = ""
#         with self.assertRaises(ET.XMLSyntaxError,
#                                msg="Should raise XMLSyntaxError for empty input."):
#             MockerConfiguration.fromstring(test_input)
#         # non-xml content
#         test_input = "sdad<test></test>sdaf"
#         with self.assertRaises(ET.XMLSyntaxError,
#                                msg="Should raise XMLSyntaxError for non-xml content."):
#             MockerConfiguration.fromstring(test_input)


class TestArgumentParsing(unittest.TestCase):

    def test_process_dict_arg(self):
        # Valid dict
        test_in = r"{ 'a':'hello', 'b': 123, 'c':True }"
        expected = {'a': 'hello', 'b': 123, 'c': True}
        test_out = sfbreplay.process_dict_arg(test_in)
        self.assertEqual(expected, test_out, "Should be a valid dict.")
        # Unexpected indentation
        test_in = r"   { 'a':'hello',    'b': 123,    'c':True }   "
        expected = {'a': 'hello', 'b': 123, 'c': True}
        test_out = sfbreplay.process_dict_arg(test_in)
        self.assertEqual(expected, test_out, "Should handle whitespace.")
        # Escape characters
        test_in = "{ 'a':'he\\ll\ao\\\\World\S' }"
        expected = {'a': 'he\\ll\ao\\World\\S'}
        test_out = sfbreplay.process_dict_arg(test_in)
        self.assertEqual(expected, test_out, "Should handle escape characters.")
        # empty str
        test_in = ""
        with self.assertRaises(ValueError, msg="Should raise ValueError for empty str."):
            sfbreplay.process_dict_arg(test_in)
        # List
        test_in = "[{'a':'hello'}]"
        with self.assertRaises(ValueError, msg="Should raise ValueError for non dict args."):
            sfbreplay.process_dict_arg(test_in)
        # incorrect syntax
        test_in = "[{'a':'hello'}"
        with self.assertRaises(ValueError, msg="Should raise ValueError for incorrect syntax."):
            sfbreplay.process_dict_arg(test_in)

if __name__ == '__main__':
    unittest.main()
