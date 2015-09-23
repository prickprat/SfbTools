import logging
import unittest
from xmlmessage import SdnMockerMessage
from xml.etree.ElementTree import ParseError

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)

XML_1 = """
  <SdnMockerConfiguration>
    <TargetUrl>https://127.0.0.1:3000/SdnApiReceiver/site</TargetUrl>
    <MaxDelay>100</MaxDelay>
    <RealTime>True</RealTime>
  </SdnMockerConfiguration>
"""
XML_2 = """
<SdnMockerConfiguration>
</SdnMockerConfiguration>
"""
XML_3 = """
<SdnMockerConfiguration>
    <TargetUrl>random!@888**</TargetUrl>
    <MaxDelay>random##$</MaxDelay>
    <RealTime>random!@888**</RealTime>
</SdnMockerConfiguration>
"""


class TestSdnMockerMessage(unittest.TestCase):

    def test_valid_xml(self):
        msg = SdnMockerMessage.fromstring(XML_1)
        self.assertTrue(isinstance(msg, SdnMockerMessage),
                        msg="valid xml Should be an instance of SdnMockerMessage.")

    def test_invalid_mxl(self):
        # Malformed Tag
        test_input = "<test</test>"
        with self.assertRaises(ParseError, msg="Should raise ParseError for malformed tag."):
            SdnMockerMessage.fromstring(test_input)
        # Empty string
        test_input = ""
        with self.assertRaises(ParseError, msg="Should raise ParseError for empty input."):
            SdnMockerMessage.fromstring(test_input)
        # non-xml content
        test_input = "sdad<test></test>sdaf"
        with self.assertRaises(ParseError, msg="Should raise ParseError for non-xml content."):
            SdnMockerMessage.fromstring(test_input)


class TestGetters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SdnMockerMessage.fromstring(XML_1)
        cls.msg_2 = SdnMockerMessage.fromstring(XML_2)
        cls.msg_3 = SdnMockerMessage.fromstring(XML_3)

    def test_todist(self):
        self.assertEqual(self.msg_1.todict(),
                         {'target_url': "http://127.0.0.1:3000/SdnApiReceiver/site",
                          'target_ip': "127.0.0.1",
                          'target_port': "3000",
                          'max_delay': 100,
                          'realtime': True},
                         "Should return a dictionary of configurations.")

    def test_todist_empty(self):
        self.assertEqual(self.msg_2.todict(),
                         {'target_url': None,
                          'target_ip': None,
                          'target_port': None,
                          'max_delay': None,
                          'realtime': None},
                         "Should return a dictionary of configurations with None values.")

    def test_todist_invalid(self):
        with self.assertRaises(ValueError,
                               msg="Should raise ValueError for incorrect element content."):
            self.msg_3.todict()
