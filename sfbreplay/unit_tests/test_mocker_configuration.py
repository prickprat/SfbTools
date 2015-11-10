import logging
import unittest
from sfbreplay import SfbReplay

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)

XML_1 = """
<Mocker>
  <MockerConfiguration>
    <MaxDelay>100</MaxDelay>
    <RealTime>True</RealTime>
    <CurrentTime>False</CurrentTime>
  </MockerConfiguration>
</Mocker>
"""
XML_2 = """
<Mocker>
  <MockerConfiguration>
  </MockerConfiguration>
</Mocker>
"""
XML_3 = """
<Mocker>
  <MockerConfiguration>
      <MaxDelay>random##$</MaxDelay>
      <RealTime>random!@888**</RealTime>
      <CurrentTime>skljdalsie</CurrentTime>
  </MockerConfiguration>
</Mocker>
"""


class TestGetters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.msg_1 = SfbReplay.fromstring(XML_1, validate=False)
        cls.msg_2 = SfbReplay.fromstring(XML_2, validate=False)

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
            SfbReplay.fromstring(XML_3, validate=False)
