import logging
import unittest
from xmlmessage import MockerConfiguration
from lxml import etree as ET

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)

XML_1 = """
<MockerConfiguration>
  <MaxDelay>100</MaxDelay>
  <RealTime>True</RealTime>
  <CurrentTime>False</CurrentTime>
</MockerConfiguration>
"""
XML_2 = """
<MockerConfiguration>
</MockerConfiguration>
"""
XML_3 = """
<MockerConfiguration>
    <MaxDelay>random##$</MaxDelay>
    <RealTime>random!@888**</RealTime>
    <CurrentTime>skljdalsie</CurrentTime>
</MockerConfiguration>
"""


class TestMockerConfiguration(unittest.TestCase):

    def test_valid_xml(self):
        msg = MockerConfiguration.fromstring(XML_1)
        self.assertTrue(isinstance(msg, MockerConfiguration),
                        msg="valid xml Should be an instance of MockerConfiguration.")

    def test_invalid_mxl(self):
        # Malformed Tag
        test_input = "<test</test>"
        with self.assertRaises(ET.XMLSyntaxError,
                               msg="Should raise XMLSyntaxError for malformed tag."):
            MockerConfiguration.fromstring(test_input)
        # Empty string
        test_input = ""
        with self.assertRaises(ET.XMLSyntaxError,
                               msg="Should raise XMLSyntaxError for empty input."):
            MockerConfiguration.fromstring(test_input)
        # non-xml content
        test_input = "sdad<test></test>sdaf"
        with self.assertRaises(ET.XMLSyntaxError,
                               msg="Should raise XMLSyntaxError for non-xml content."):
            MockerConfiguration.fromstring(test_input)


class TestGetters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = MockerConfiguration.fromstring(XML_1)
        cls.msg_2 = MockerConfiguration.fromstring(XML_2)
        cls.msg_3 = MockerConfiguration.fromstring(XML_3)

    def test_todist(self):
        self.assertEqual(self.msg_1.todict(),
                         {'max_delay': 100,
                          'realtime': True,
                          'currenttime': False},
                         "Should return a dictionary of configurations.")

    def test_todist_empty(self):
        self.assertEqual(self.msg_2.todict(),
                         {'max_delay': None,
                          'realtime': None,
                          'currenttime': None},
                         "Should return a dictionary of configurations with None values.")

    def test_todist_invalid(self):
        with self.assertRaises(ValueError,
                               msg="Should raise ValueError for incorrect element content."):
            self.msg_3.todict()
