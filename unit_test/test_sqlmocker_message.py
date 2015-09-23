import logging
import unittest
from xmlmessage import SqlMockerMessage
from xml.etree.ElementTree import ParseError

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)

XML_1 = """
<SqlMockerConfiguration>
  <Driver>SqlServer</Driver>
  <Server>10.2.3.4/SqlServerExpress</Server>
  <Database>LyncCDR</Database>
  <UID>hello</UID>
  <PWD>!@#!#!&lt;#!@$!QS</PWD>
</SqlMockerConfiguration>
"""

XML_2 = """
<SqlMockerConfiguration>
</SqlMockerConfiguration>
"""


class TestSdnMockerMessage(unittest.TestCase):

    def test_valid_xml(self):
        msg = SqlMockerMessage.fromstring(XML_1)
        self.assertTrue(isinstance(msg, SqlMockerMessage),
                        msg="valid xml Should be an instance of SqlMockerMessage.")

    def test_invalid_mxl(self):
        # Malformed Tag
        test_input = "<test</test>"
        with self.assertRaises(ParseError, msg="Should raise ParseError for malformed tag."):
            SqlMockerMessage.fromstring(test_input)
        # Empty string
        test_input = ""
        with self.assertRaises(ParseError, msg="Should raise ParseError for empty input."):
            SqlMockerMessage.fromstring(test_input)
        # non-xml content
        test_input = "sdad<test></test>sdaf"
        with self.assertRaises(ParseError, msg="Should raise ParseError for non-xml content."):
            SqlMockerMessage.fromstring(test_input)


class TestToDict(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SqlMockerMessage.fromstring(XML_1)
        cls.msg_2 = SqlMockerMessage.fromstring(XML_2)

    def test_existing_values(self):
        self.assertEqual(self.msg_1.todict(),
                         {'driver': "SqlServer",
                          'server': "10.2.3.4/SqlServerExpress",
                          'database': "LyncCDR",
                          'uid': "hello",
                          'pwd': "!@#!#!<#!@$!QS"
                          },
                         "Should return matching values for all configurations.")

    def test_non_existing_values(self):
        self.assertEqual(self.msg_2.todict(),
                         {'driver': None,
                          'server': None,
                          'database': None,
                          'uid': None,
                          'pwd': None
                          },
                         "Should return None for all configurations.")
