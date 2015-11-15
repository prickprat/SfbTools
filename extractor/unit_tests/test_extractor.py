import logging
import unittest
from lxml import etree as ET
from sfbtools.extractor.extractor import SdnMessage

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)

# Reusable XML input strings
XML_1 = """
<LyncDiagnostics>
    <ConnectionInfo>
        <CallId>Hello1234@</CallId>
        <ConferenceId>Hello1234@</ConferenceId>
        <TimeStamp>2015-08-04T09:11:10.8226250-04:00</TimeStamp>
    </ConnectionInfo>
</LyncDiagnostics>
"""
XML_2 = """
<LyncDiagnostics>
  <ConnectionInfo>
  </ConnectionInfo>
</LyncDiagnostics>
"""
XML_3 = """
<LyncDiagnostics>
    <CallId>Hello1234@</CallId>
    <ConferenceId>Hello1234@</ConferenceId>
    <TimeStamp>2015-08-04T09:11:10.8226250-04:00</TimeStamp>
</LyncDiagnostics>
"""


class TestSdnMessageInit(unittest.TestCase):

    def test_valid_xml(self):
        msg = SdnMessage(XML_1)
        self.assertTrue(isinstance(msg, SdnMessage),
                        msg="valid xml Should be an instance of SdnMessage.")
        msg = SdnMessage(XML_2)
        self.assertTrue(isinstance(msg, SdnMessage),
                        msg="valid xml Should be an instance of SdnMessage.")
        msg = SdnMessage(XML_3)
        self.assertTrue(isinstance(msg, SdnMessage),
                        msg="valid xml Should be an instance of SdnMessage.")

    def test_invalid_mxl(self):
        # Malformed Tag
        test_input = "<test</test>"
        with self.assertRaises(ET.XMLSyntaxError,
                               msg="Should raise XMLSyntaxError for malformed tag."):
            SdnMessage(test_input)
        # Empty string
        test_input = ""
        with self.assertRaises(ET.XMLSyntaxError,
                               msg="Should raise XMLSyntaxError for empty input."):
            SdnMessage(test_input)
        # non-xml content
        test_input = "sdad<test></test>sdaf"
        with self.assertRaises(ET.XMLSyntaxError,
                               msg="Should raise XMLSyntaxError for non-xml content."):
            SdnMessage(test_input)


class TestContainsCallId(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SdnMessage(XML_1)
        cls.msg_2 = SdnMessage(XML_2)
        cls.msg_3 = SdnMessage(XML_3)

    def setUp(self):
        self.msg_funcs = {'normal': TestContainsCallId.msg_1.contains_call_id,
                          'no_call_elm': TestContainsCallId.msg_2.contains_call_id,
                          'incorrect_tree': TestContainsCallId.msg_3.contains_call_id}

    def test_no_arguments(self):
        call_ids = []
        self.assertFalse(self.msg_funcs['normal'](*call_ids))
        self.assertFalse(self.msg_funcs['no_call_elm'](*call_ids))
        self.assertFalse(self.msg_funcs['incorrect_tree'](*call_ids))

    def test_single(self):
        # Match
        call_ids = ['Hello1234@']
        self.assertTrue(self.msg_funcs['normal'](*call_ids))
        # No Match
        call_ids = ['Bye1234']
        self.assertFalse(self.msg_funcs['normal'](*call_ids))
        # Match case-insensitive
        call_ids = ['hello1234@']
        self.assertTrue(self.msg_funcs['normal'](*call_ids))

    def test_multiple(self):
        # Match
        call_ids = ['blank', 'Hello1234@', 'blank2']
        self.assertTrue(self.msg_funcs['normal'](*call_ids))
        # No Match
        call_ids = ['blank', 'Blarg1234@', 'blank2']
        self.assertFalse(self.msg_funcs['normal'](*call_ids))
        # Match case-insentive
        call_ids = ['blank', 'hello1234@', 'blank2']
        self.assertTrue(self.msg_funcs['normal'](*call_ids))

    def test_no_element(self):
        call_ids = ['Hello1234@']
        self.assertFalse(self.msg_funcs['no_call_elm'](*call_ids))

    def test_incorrect_tree(self):
        call_ids = ['Hello1234@']
        self.assertFalse(self.msg_funcs['incorrect_tree'](*call_ids))


class TestContainsConfId(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.msg_1 = SdnMessage(XML_1)
        cls.msg_2 = SdnMessage(XML_2)
        cls.msg_3 = SdnMessage(XML_3)

    def setUp(self):
        self.msg_funcs = {'normal': TestContainsConfId.msg_1.contains_conf_id,
                          'no_conf_elm': TestContainsConfId.msg_2.contains_conf_id,
                          'incorrect_tree': TestContainsConfId.msg_3.contains_conf_id}

    def test_no_arguments(self):
        conf_ids = []
        self.assertFalse(self.msg_funcs['normal'](*conf_ids))
        self.assertFalse(self.msg_funcs['no_conf_elm'](*conf_ids))
        self.assertFalse(self.msg_funcs['incorrect_tree'](*conf_ids))

    def test_single(self):
        # Match
        conf_ids = ['Hello1234@']
        self.assertTrue(self.msg_funcs['normal'](*conf_ids))
        # No Match
        conf_ids = ['Bye1234']
        self.assertFalse(self.msg_funcs['normal'](*conf_ids))
        # Match case-insensitive
        conf_ids = ['hello1234@']
        self.assertTrue(self.msg_funcs['normal'](*conf_ids))

    def test_multiple(self):
        # Match
        conf_ids = ['blank', 'Hello1234@', 'blank2']
        self.assertTrue(self.msg_funcs['normal'](*conf_ids))
        # No Match
        conf_ids = ['blank', 'Blarg1234@', 'blank2']
        self.assertFalse(self.msg_funcs['normal'](*conf_ids))
        # Match case-insentive
        conf_ids = ['blank', 'hello1234@', 'blank2']
        self.assertTrue(self.msg_funcs['normal'](*conf_ids))

    def test_no_element(self):
        conf_ids = ['Hello1234@']
        self.assertFalse(self.msg_funcs['no_conf_elm'](*conf_ids))

    def test_incorrect_tree(self):
        conf_ids = ['Hello1234@']
        self.assertFalse(self.msg_funcs['incorrect_tree'](*conf_ids))


if __name__ == '__main__':
    unittest.main()
