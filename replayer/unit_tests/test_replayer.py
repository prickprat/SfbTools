import logging
import unittest
from sfbtools import sfbreplay
from sfbtools.replayer.replayer import SfbReplayer

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)

XML_1 = """
<SfbReplay>
  <ReplayConfiguration>
    <MaxDelay>100</MaxDelay>
    <RealTime>True</RealTime>
    <CurrentTime>False</CurrentTime>
  </ReplayConfiguration>
</SfbReplay>
"""
XML_2 = """
<SfbReplay>
  <ReplayConfiguration>
  </ReplayConfiguration>
</SfbReplay>
"""
XML_3 = """
<SfbReplay>
  <ReplayConfiguration>
      <MaxDelay>random##$</MaxDelay>
      <RealTime>random!@888**</RealTime>
      <CurrentTime>skljdalsie</CurrentTime>
  </ReplayConfiguration>
</SfbReplay>
"""


class TestArgumentParsing(unittest.TestCase):

    def test_process_dict_arg(self):
        # Valid dict
        test_in = r"{ 'a':'hello', 'b': 123, 'c':True }"
        expected = {'a': 'hello', 'b': 123, 'c': True}
        test_out = sfbreplay.process_dict_arg(test_in)
        self.assertEqual(expected, test_out, "Should be a valid dict.")
        # Unexpected indentation
        test_in = r"   { 'a':'hello',    'b': 123,    'c':True }   "
        expected = {'a': 'hello', 'b': 123, 'c': True}
        test_out = sfbreplay.process_dict_arg(test_in)
        self.assertEqual(expected, test_out, "Should handle whitespace.")
        # Escape characters
        test_in = "{ 'a':'he\\ll\ao\\\\World\S' }"
        expected = {'a': 'he\\ll\ao\\World\\S'}
        test_out = sfbreplay.process_dict_arg(test_in)
        self.assertEqual(expected, test_out, "Should handle escape characters.")
        # empty str
        test_in = ""
        with self.assertRaises(ValueError, msg="Should raise ValueError for empty str."):
            sfbreplay.process_dict_arg(test_in)
        # List
        test_in = "[{'a':'hello'}]"
        with self.assertRaises(ValueError, msg="Should raise ValueError for non dict args."):
            sfbreplay.process_dict_arg(test_in)
        # incorrect syntax
        test_in = "[{'a':'hello'}"
        with self.assertRaises(ValueError, msg="Should raise ValueError for incorrect syntax."):
            sfbreplay.process_dict_arg(test_in)


class TestGetters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SfbReplayer.fromstring(XML_1, validate=False)
        cls.msg_2 = SfbReplayer.fromstring(XML_2, validate=False)

    def test_extract_replay_config(self):
        self.assertEqual(self.msg_1.replay_config,
                         {'max_delay': 100,
                          'realtime': True,
                          'currenttime': False},
                         "Should return a dictionary of configurations.")

    def test_extract_replay_config_empty(self):
        self.assertEqual(self.msg_2.replay_config,
                         {'max_delay': None,
                          'realtime': None,
                          'currenttime': None},
                         "Should return a dictionary of configurations with None values.")

    def test_extract_replay_invalid(self):
        with self.assertRaises(ValueError,
                               msg="Should raise ValueError for incorrect element content."):
            SfbReplayer.fromstring(XML_3, validate=False)

if __name__ == '__main__':
    unittest.main()
