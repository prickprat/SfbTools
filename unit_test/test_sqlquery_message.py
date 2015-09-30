import logging
import unittest
from xmlmessage import SqlQueryMessage
from xml.etree.ElementTree import ParseError

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)

XML_1 = """
<SqlQueryMessage>
  <TimeStamp>2015-08-04T13:27:54.4519455Z</TimeStamp>
  <Query>insert into tbl values (1,2,3); delete from tbl where id = 1;</Query>
</SqlQueryMessage>
"""

XML_2 = """
<SqlQueryMessage>
  <TimeStamp>2015-08-04T13:27:54+1:00</TimeStamp>
  <Query><![CDATA[SELECT * FROM tbl WHERE tbl.id > 1;]]></Query>
</SqlQueryMessage>
"""

XML_3 = """
<SqlQueryMessage>
</SqlQueryMessage>
"""


class TestSqlQueryMessage(unittest.TestCase):

    def test_valid_xml(self):
        msg = SqlQueryMessage.fromstring(XML_1)
        self.assertTrue(isinstance(msg, SqlQueryMessage),
                        msg="valid xml Should be an instance of SqlQueryMessage.")

    def test_invalid_mxl(self):
        # Malformed Tag
        test_input = "<test</test>"
        with self.assertRaises(ParseError, msg="Should raise ParseError for malformed tag."):
            SqlQueryMessage.fromstring(test_input)
        # Empty string
        test_input = ""
        with self.assertRaises(ParseError, msg="Should raise ParseError for empty input."):
            SqlQueryMessage.fromstring(test_input)
        # non-xml content
        test_input = "sdad<test></test>sdaf"
        with self.assertRaises(ParseError, msg="Should raise ParseError for non-xml content."):
            SqlQueryMessage.fromstring(test_input)


class TestGetQuery(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SqlQueryMessage.fromstring(XML_1)
        cls.msg_2 = SqlQueryMessage.fromstring(XML_2)
        cls.msg_3 = SqlQueryMessage.fromstring(XML_3)

    def test_text(self):
        actual = self.msg_1.get_query()
        expected = r"insert into tbl values (1,2,3); delete from tbl where id = 1;"
        self.assertEqual(actual, expected, "Should correctly parse text queries.")

    def test_cdata(self):
        actual = self.msg_2.get_query()
        expected = r"SELECT * FROM tbl WHERE tbl.id > 1;"
        self.assertEqual(actual, expected, "Should correctly parse CDATA tags.")

    def test_no_elem(self):
        actual = self.msg_3.get_query()
        expected = None
        self.assertEqual(actual, expected, "Should return None if element doesn't exist.")
