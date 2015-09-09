import logging
import unittest
from xmlmessage import SqlMockerMessage
from xml.etree.ElementTree import ParseError

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)

XML_1 = """
<SqlMocker>
    <Configuration>
        <Driver>SqlServer</Driver>
        <Server>10.2.3.4/SqlServerExpress</Server>
        <Database>LyncCDR</Database>
        <UID>hello</UID>
        <PWD>!@#!#!&lt;#!@$!QS</PWD>
    </Configuration>
</SqlMocker>
"""

XML_2 = """
<SqlMocker>
    <Configuration>
    </Configuration>
</SqlMocker>
"""


class TestSdnMockerMessage(unittest.TestCase):

    def test_valid_xml(self):
        msg = SqlMockerMessage(XML_1)
        self.assertTrue(isinstance(msg, SqlMockerMessage),
                        msg="valid xml Should be an instance of SqlMockerMessage.")

    def test_invalid_mxl(self):
        # Malformed Tag
        test_input = "<test</test>"
        with self.assertRaises(ParseError, msg="Should raise ParseError for malformed tag."):
            SqlMockerMessage(test_input)
        # Empty string
        test_input = ""
        with self.assertRaises(ParseError, msg="Should raise ParseError for empty input."):
            SqlMockerMessage(test_input)
        # non-xml content
        test_input = "sdad<test></test>sdaf"
        with self.assertRaises(ParseError, msg="Should raise ParseError for non-xml content."):
            SqlMockerMessage(test_input)


class TestToDict(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SqlMockerMessage(XML_1)
        cls.msg_2 = SqlMockerMessage(XML_2)

    def test_existing_values(self):
        self.assertEqual(self.msg_1.todict(),
                         {'Driver': "SqlServer",
                          'Server': "10.2.3.4/SqlServerExpress",
                          'Database': "LyncCDR",
                          'UID': "hello",
                          'PWD': "!@#!#!<#!@$!QS"
                          },
                         "Should return matching values for all configurations.")

    def test_non_existing_values(self):
        self.assertEqual(self.msg_2.todict(),
                         {'Driver': None,
                          'Server': None,
                          'Database': None,
                          'UID': None,
                          'PWD': None
                          },
                         "Should return None for all configurations.")
