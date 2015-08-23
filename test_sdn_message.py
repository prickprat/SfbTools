import unittest
import datetime as DT
from SdnMessage import SdnMessage

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


class TestGetTimestamp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.msg_1 = SdnMessage(XML_1)
        cls.msg_2 = SdnMessage(XML_2)
        cls.msg_3 = SdnMessage(XML_3)

    def setUp(self):
        self.msg_funcs = {'normal': TestContainsConfId.msg_1.contains_conf_id,
                          'no_conf_elm': TestContainsConfId.msg_2.contains_conf_id,
                          'incorrect_tree': TestContainsConfId.msg_3.contains_conf_id}

    def test(self):
        pass


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
        # Minimum date allowed
        zulu = "0001-01-01T00:00:00.0000000Z"
        expected = DT.datetime(1, 1, 1, 0, 0, 0, 0,  DT.timezone.utc)
        output = SdnMessage.convert_timestamp(zulu)
        self.assertEqual(expected, output, "Should parse the minimum datetime allowed.")

    def test_offset(self):
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

    def test_invalid(self):
        pass


if __name__ == '__main__':
    unittest.main()
