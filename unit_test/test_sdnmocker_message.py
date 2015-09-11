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
XML_3 = """
<SdnMocker>
    <Configuration>
      <TargetUrl>random!@888**</TargetUrl>
      <MaxDelay>random##$</MaxDelay>
      <RealTime>random!@888**</RealTime>
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
        cls.msg_3 = SdnMockerMessage(XML_3)

    def test_todist(self):
        self.assertEqual(self.msg_1.todict(),
                         {'TargetUrl': "https://127.0.0.1:3000/SdnApiReceiver/site",
                          'TargetIp': "127.0.0.1",
                          'TargetPort': "3000",
                          'MaxDelay': 100,
                          'RealTime': True},
                         "Should return a dictionary of configurations.")

    def test_todist_empty(self):
        self.assertEqual(self.msg_2.todict(),
                         {'TargetUrl': None,
                          'TargetIp': None,
                          'TargetPort': None,
                          'MaxDelay': None,
                          'RealTime': None},
                         "Should return a dictionary of configurations with None values.")

    def test_todist_invalid(self):
        with self.assertRaises(ValueError,
                               msg="Should raise ValueError for incorrect element content."):
            self.msg_3.todict()
