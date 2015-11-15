import logging
import unittest
import datetime as DT
import dateutil.parser as DUP
from sfbtools.replayer.xmlmessage import SdnMessage
from sfbtools.replayer.xmlmessage import NoElementException
from lxml import etree as ET

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
        msg = SdnMessage.fromstring(XML_1)
        self.assertTrue(isinstance(msg, SdnMessage),
                        msg="valid xml Should be an instance of SdnMessage.")
        msg = SdnMessage.fromstring(XML_2)
        self.assertTrue(isinstance(msg, SdnMessage),
                        msg="valid xml Should be an instance of SdnMessage.")
        msg = SdnMessage.fromstring(XML_3)
        self.assertTrue(isinstance(msg, SdnMessage),
                        msg="valid xml Should be an instance of SdnMessage.")

    def test_invalid_mxl(self):
        # Malformed Tag
        test_input = "<test</test>"
        with self.assertRaises(ET.XMLSyntaxError,
                               msg="Should raise XMLSyntaxError for malformed tag."):
            SdnMessage.fromstring(test_input)
        # Empty string
        test_input = ""
        with self.assertRaises(ET.XMLSyntaxError,
                               msg="Should raise XMLSyntaxError for empty input."):
            SdnMessage.fromstring(test_input)
        # non-xml content
        test_input = "sdad<test></test>sdaf"
        with self.assertRaises(ET.XMLSyntaxError,
                               msg="Should raise XMLSyntaxError for non-xml content."):
            SdnMessage.fromstring(test_input)


class TestContainsCallId(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SdnMessage.fromstring(XML_1)
        cls.msg_2 = SdnMessage.fromstring(XML_2)
        cls.msg_3 = SdnMessage.fromstring(XML_3)

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

        cls.msg_1 = SdnMessage.fromstring(XML_1)
        cls.msg_2 = SdnMessage.fromstring(XML_2)
        cls.msg_3 = SdnMessage.fromstring(XML_3)

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


class TestGetTimestamp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SdnMessage.fromstring(XML_1)
        cls.msg_2 = SdnMessage.fromstring(XML_2)
        cls.msg_3 = SdnMessage.fromstring(XML_3)

    def setUp(self):
        self.msg_funcs = {'normal': self.msg_1.get_timestamp,
                          'no_timestamp_elem': self.msg_2.get_timestamp,
                          'incorrect_tree': self.msg_3.get_timestamp}

    def test_normal_tree(self):
        expected_offset = DT.timezone(-DT.timedelta(hours=4, minutes=00))
        expected = DT.datetime(2015, 8, 4, 9, 11, 10, 822625, expected_offset)
        output = self.msg_funcs['normal']()
        self.assertEqual(expected, output, "Should return the correct converted datetime element.")

    def test_no_element(self):
        with self.assertRaises(NoElementException,
                               msg="Should raise NoElement if there is no TimeStamp Element."):
            self.msg_funcs['no_timestamp_elem']()

    def test_incorrect_tree(self):
        with self.assertRaises(NoElementException,
                               msg="Should raise NoElement for incorrect xml tree."):
            self.msg_funcs['incorrect_tree']()


class TestConvertDatetime(unittest.TestCase):

    def test_convert_zulu(self):
        # Full microseconds
        expected = "2000-01-01T01:01:01.9990000Z"
        dt_in = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, DT.timezone.utc)
        output = SdnMessage.convert_datetime(dt_in)
        self.assertEqual(expected, output, "Should capture all Microseconds.")
        # Nanoseconds
        expected = "2000-01-01T01:01:01.1112140Z"
        dt_in = DT.datetime(2000, 1, 1, 1, 1, 1, 111214, DT.timezone.utc)
        output = SdnMessage.convert_datetime(dt_in)
        self.assertEqual(expected, output, "Should trim nanoseconds to microseconds.")
        # No fractional seconds
        expected = "2000-01-01T01:01:01.0000000Z"
        dt_in = DT.datetime(2000, 1, 1, 1, 1, 1, 0,  DT.timezone.utc)
        output = SdnMessage.convert_datetime(dt_in)
        self.assertEqual(expected, output, "Should parse no microseconds.")
        # Maximum date allowed
        expected = "9999-12-31T23:59:59.9999990Z"
        dt_in = DT.datetime(9999, 12, 31, 23, 59, 59, 999999,  DT.timezone.utc)
        output = SdnMessage.convert_datetime(dt_in)
        self.assertEqual(expected, output, "Should parse the maximum datetime allowed.")
        # Minimum date allowed
        expected = "100-01-01T00:00:00.0000000Z"
        dt_in = DT.datetime(100, 1, 1, 0, 0, 0, 0,  DT.timezone.utc)
        output = SdnMessage.convert_datetime(dt_in)
        self.assertEqual(expected, output, "Should parse the minimum datetime allowed.")

    def test_tz_offset(self):
        # Positive UTC offset
        expected = "2000-01-01T01:01:01.9990000+11:40"
        dt_in_offset = DT.timezone(DT.timedelta(hours=11, minutes=40))
        dt_in = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, dt_in_offset)
        output = SdnMessage.convert_datetime(dt_in)
        self.assertEqual(expected, output, "Should preserve positive UTC offset.")
        # Negative UTC offset
        expected = "2000-01-01T01:01:01.9990000-01:22"
        dt_in_offset = DT.timezone(-DT.timedelta(hours=1, minutes=22))
        dt_in = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, dt_in_offset)
        output = SdnMessage.convert_datetime(dt_in)
        self.assertEqual(expected, output, "Should preserve negative UTC offset.")
        # Zero UTC offset
        expected = "2000-01-01T01:01:01.9990000Z"
        dt_in_offset = DT.timezone(-DT.timedelta(hours=0, minutes=0))
        dt_in = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, dt_in_offset)
        output = SdnMessage.convert_datetime(dt_in)
        self.assertEqual(expected, output, "Should preserve Zulu notation.")

    def test_invalid_datetime(self):
        # Invalid datetime stamp
        test_input = "Monday"
        with self.assertRaises(ValueError, msg="Should raise ValueError for invalid datetime."):
            SdnMessage.convert_datetime(test_input)

    def test_invalid_tz(self):
        # Invalid datetime timezone
        invalid_tz = "2000-01-01T01:01:01.999+24:01"
        invalid_dt = DUP.parse(invalid_tz)
        with self.assertRaises(ValueError, msg="Should raise ValueError for invalid timezone."):
            SdnMessage.convert_datetime(invalid_dt)


class TestConvertTimestamp(unittest.TestCase):

    def test_zulu_time(self):
        # Full microseconds
        zulu = "2000-01-01T01:01:01.999Z"
        expected = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, DT.timezone.utc)
        output = SdnMessage.convert_timestamp(zulu)
        self.assertEqual(expected, output, "Should capture all Microseconds.")
        # Nanoseconds
        zulu = "2000-01-01T01:01:01.11121314Z"
        expected = DT.datetime(2000, 1, 1, 1, 1, 1, 111213, DT.timezone.utc)
        output = SdnMessage.convert_timestamp(zulu)
        self.assertEqual(expected, output, "Should trim nanoseconds to microseconds.")
        # No fractional seconds
        zulu = "2000-01-01T01:01:01Z"
        expected = DT.datetime(2000, 1, 1, 1, 1, 1, 0,  DT.timezone.utc)
        output = SdnMessage.convert_timestamp(zulu)
        self.assertEqual(expected, output, "Should parse no microseconds.")
        # Maximum date allowed
        zulu = "9999-12-31T23:59:59.9999999Z"
        expected = DT.datetime(9999, 12, 31, 23, 59, 59, 999999,  DT.timezone.utc)
        output = SdnMessage.convert_timestamp(zulu)
        self.assertEqual(expected, output, "Should parse the maximum datetime allowed.")
        # Minimu8m date allowed
        zulu = "100-01-01T00:00:00.0000000Z"
        expected = DT.datetime(100, 1, 1, 0, 0, 0, 0,  DT.timezone.utc)
        output = SdnMessage.convert_timestamp(zulu)
        self.assertEqual(expected, output, "Should parse the minimum datetime allowed.")

    def test_timezone_offset(self):
        # Positive UTC offset
        test_input = "2000-01-01T01:01:01.999+11:40"
        expected_offset = DT.timezone(DT.timedelta(hours=11, minutes=40))
        expected = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, expected_offset)
        output = SdnMessage.convert_timestamp(test_input)
        self.assertEqual(expected, output, "Should preserve positive UTC offset.")
        # Negative UTC offset
        test_input = "2000-01-01T01:01:01.999-01:22"
        expected_offset = DT.timezone(-DT.timedelta(hours=1, minutes=22))
        expected = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, expected_offset)
        output = SdnMessage.convert_timestamp(test_input)
        self.assertEqual(expected, output, "Should preserve negative UTC offset.")
        # Zero UTC offset
        test_input = "2000-01-01T01:01:01.999+00:00"
        expected_offset = DT.timezone(-DT.timedelta(hours=0, minutes=0))
        expected = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, expected_offset)
        output = SdnMessage.convert_timestamp(test_input)
        self.assertEqual(expected, output, "Should preserve negative UTC offset.")

    def test_invalid_timezone(self):
        # Invalid timezone negative
        test_input = "2000-01-01T01:01:01.999-24:01"
        with self.assertRaises(ValueError,
                               msg="Should raise Exception for invalid negative timezone."):
            SdnMessage.convert_timestamp(test_input)
        # Invalid timezone positive
        test_input = "2000-01-01T01:01:01.999+24:01"
        with self.assertRaises(ValueError,
                               msg="Should raise Exception for invalid positive timezone."):
            SdnMessage.convert_timestamp(test_input)
        # Invalid timezone Zulu
        test_input = "2000-01-01T01:01:01.999P"
        with self.assertRaises(ValueError,
                               msg="Should raise Exception for invalid Zulu."):
            SdnMessage.convert_timestamp(test_input)
        # No Z or timezone
        test_input = "2000-01-01T01:01:01.999"
        with self.assertRaises(ValueError, msg="Should raise Exception for no timezone."):
            SdnMessage.convert_timestamp(test_input)

    def test_invalid_timestamp(self):
        # Invalid datetime stamp
        test_input = "Monday"
        with self.assertRaises(ValueError, msg="Should raise ValueError for invalid timestamp."):
            SdnMessage.convert_timestamp(test_input)
        # Invalid hour stamp
        test_input = "2000-01-01T25:01:01.999Z"
        with self.assertRaises(ValueError, msg="Should raise ValueError for invalid hour."):
            SdnMessage.convert_timestamp(test_input)
        # Invalid date stamp
        test_input = "2000-01-32T12:01:01.999Z"
        with self.assertRaises(ValueError, msg="Should raise ValueError for invalid date."):
            SdnMessage.convert_timestamp(test_input)


class TestSetTimestamp(unittest.TestCase):

    def setUp(self):
        self.msg_1 = SdnMessage.fromstring(XML_1)
        self.msg_2 = SdnMessage.fromstring(XML_2)
        self.msg_3 = SdnMessage.fromstring(XML_3)

    def test_normal_tree(self):
        # Full microseconds
        expected = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, DT.timezone.utc)
        self.msg_1.set_timestamp(expected)
        output = self.msg_1.get_timestamp()
        self.assertEqual(expected, output, "Should set timestamp with full microseconds.")
        # No fractional seconds
        expected = DT.datetime(2000, 1, 1, 1, 1, 1, 0,  DT.timezone.utc)
        self.msg_1.set_timestamp(expected)
        output = self.msg_1.get_timestamp()
        self.assertEqual(expected, output, "Should set timestamp with no microseconds.")

    def test_no_element(self):
        test_in = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, DT.timezone.utc)
        with self.assertRaises(NoElementException,
                               msg="Should raise NoElementException for no element."):
            self.msg_2.set_timestamp(test_in)

    def test_incorrect_tree(self):
        test_in = DT.datetime(2000, 1, 1, 1, 1, 1, 999000, DT.timezone.utc)
        with self.assertRaises(NoElementException,
                               msg="Should raise NoElementException for incorrect tree."):
            self.msg_3.set_timestamp(test_in)


if __name__ == '__main__':
    unittest.main()
