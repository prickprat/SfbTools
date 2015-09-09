import logging
import unittest
from xmlmessage import SdnMockerMessage
from xml.etree.ElementTree import ParseError

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)

XML_1 = """
<SdnMocker>
    <Configuration>
        <TargetUrl>https://127.0.0.1:3000/SdnApiReceiver/site</TargetUrl>
        <MaxDelay>100</MaxDelay>
        <RealTime>True</RealTime>
    </Configuration>
</SdnMocker>
"""
XML_2 = """
<SdnMocker>
    <Configuration>
    </Configuration>
</SdnMocker>
"""



class TestSdnMockerMessage(unittest.TestCase):

    def test_valid_xml(self):
        msg = SdnMockerMessage(XML_1)
        self.assertTrue(isinstance(msg, SdnMockerMessage),
                        msg="valid xml Should be an instance of SdnMockerMessage.")

    def test_invalid_mxl(self):
        # Malformed Tag
        test_input = "<test</test>"
        with self.assertRaises(ParseError, msg="Should raise ParseError for malformed tag."):
            SdnMockerMessage(test_input)
        # Empty string
        test_input = ""
        with self.assertRaises(ParseError, msg="Should raise ParseError for empty input."):
            SdnMockerMessage(test_input)
        # non-xml content
        test_input = "sdad<test></test>sdaf"
        with self.assertRaises(ParseError, msg="Should raise ParseError for non-xml content."):
            SdnMockerMessage(test_input)


class TestGetters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SdnMockerMessage(XML_1)
        cls.msg_2 = SdnMockerMessage(XML_2)

    def test_get_target_ip(self):
        self.assertEqual(self.msg_1.get_target_ip(), "127.0.0.1",
                         "Should match target ip address.")
        self.assertEqual(self.msg_2.get_target_ip(), None,
                         "Should return None for no target ip address.")

    def test_get_target_port(self):
        self.assertEqual(self.msg_1.get_target_port(), "3000",
                         "Should match target port.")
        self.assertEqual(self.msg_2.get_target_port(), None,
                         "Should return None for no target port.")

    def test_todist(self):
        self.assertEqual(self.msg_1.todict(),
                         {'TargetUrl': "https://127.0.0.1:3000/SdnApiReceiver/site",
                          'MaxDelay': 100,
                          'RealTime': True},
                         "Should return a dictionary of configurations.")

    def test_todist_empty(self):
        self.assertEqual(self.msg_2.todict(),
                         {'TargetUrl': None,
                          'MaxDelay': None,
                          'RealTime': None},
                         "Should return a dictionary of configurations with None values.")
