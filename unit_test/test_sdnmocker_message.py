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

    def test_get_target_url(self):
        self.assertEqual(self.msg_1.get_target_url(), "https://127.0.0.1:3000/SdnApiReceiver/site",
                         "Should match full target url.")

    def test_get_target_ip(self):
        self.assertEqual(self.msg_1.get_target_ip(), "127.0.0.1",
                         "Should match target ip address.")

    def test_get_target_port(self):
        self.assertEqual(self.msg_1.get_target_port(), "3000",
                         "Should match target port.")

    def test_is_realtime(self):
        self.assertTrue(self.msg_1.is_realtime(),
                        "Should be configured as real time.")

    def test_get_max_delay(self):
        self.assertEqual(self.msg_1.get_max_delay(), 100,
                         "Should match correct max delay.")

    def test_todist(self):
        self.assertEqual(self.msg_1.todict(),
                         {'TargetUrl': "https://127.0.0.1:3000/SdnApiReceiver/site",
                          'TargetIp': "127.0.0.1",
                          'TargetPort': "3000",
                          'MaxDelay': 100,
                          'RealTime': True},
                         "Should return a dictionary of configurations.")
