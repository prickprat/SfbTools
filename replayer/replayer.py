from .mocker import SdnMocker
from .mocker import OdbcMocker
from .xmlmessage import SdnMessage
from .xmlmessage import SqlQueryMessage
from lxml import etree as ET
import logging
import logging.config
import datetime as DT
import os


class SfbReplayer():

    """
    Used for replaying a mock test file, given mocker configurations
    """

    def __init__(self, **kwargs):
        self.mock_test = kwargs['etree']
        # Set the default namespace for the mock test xml
        self.default_ns = self.mock_test.getroot().nsmap.get(None, '')
        if self.default_ns != '':
            self.default_ns = "{{{0}}}".format(self.default_ns)
        # Set the configuration for the mockers
        self.sdn_config = kwargs.get('sdn_config', None)
        self.odbc_config = kwargs.get('odbc_config', None)

        # default to SDN version 2.1.1 if not defined
        if self.sdn_config is not None:
            self.sdn_config['version'] = self.sdn_config.get('version', '2.1.1')

        # Configure the Mockers
        self.sdn_mocker = SdnMocker(**self.sdn_config) if self.sdn_config else None
        self.odbc_mocker = OdbcMocker(**self.odbc_config) if self.odbc_config else None

        # Validate Mock Test against the XML Schema
        if kwargs.get('validate', True):
            self.validate()

        self.replay_config = self.extract_replay_config()

        self.replay_messages = self.extract_replay_messages()

        if self.replay_config['currenttime']:
            self.update_timestamps()

    @classmethod
    def fromstring(cls, mock_test_str, **kwargs):
        """
        Parses the mock test as a string.
        Raises ParseError if invalid XML is encountered.
        """
        try:
            mock_test_etree = ET.ElementTree(element=ET.fromstring(mock_test_str))
            return cls(etree=mock_test_etree, **kwargs)
        except ET.XMLSyntaxError as e:
            logging.error("XMLSyntaxError: " + str(e))
            raise

    @classmethod
    def fromfile(cls, mock_test_path, **kwargs):
        """
        Parses the mock test as a string.
        Raises ParseError if invalid XML is encountered.
        """
        try:
            return cls(etree=ET.parse(mock_test_path), **kwargs)
        except ET.ParseError as e:
            logging.error("ParseError whilst parsing mock file : " + str(e))
            raise ValueError("Invalid Sfb Replay Test XML Format.")

    def run(self):
        try:
            if self.sdn_mocker is not None:
                self.sdn_mocker.open()
            if self.odbc_config is not None:
                self.odbc_mocker.open()

            # Send the messages using appropriate mocker and intervals
            prev_timestamp = None
            for msg in self.replay_messages:
                mocker = None
                if isinstance(msg, SdnMessage):
                    mocker = self.sdn_mocker
                elif isinstance(msg, SqlQueryMessage):
                    mocker = self.odbc_mocker
                else:
                    raise ValueError("Unrecognised Mock Message instance.")

                delay = self.calculate_delay(msg.get_timestamp(),
                                             prev_timestamp)
                mocker.send_message(msg, delay)
                prev_timestamp = msg.get_timestamp()

        finally:
            if self.sdn_mocker is not None:
                self.sdn_mocker.close()
            if self.odbc_mocker is not None:
                self.odbc_mocker.close()

    def validate(self):
        # Use correct schema for SDN version
        # no SDN or SDN version 2.1.1 use schema C
        schema_file = "Mocker.Schema.C.xsd"
        if (self.sdn_config is not None
                and self.sdn_config['version'] == '2.2'):
            schema_file = "Mocker.Schema.D.xsd"
        schema_path = os.path.join(os.path.dirname(__file__), 'schemas/' + schema_file)
        schema_doc = ET.parse(schema_path)
        schema = ET.XMLSchema(schema_doc)
        try:
            schema.assertValid(self.mock_test)
        except ET.DocumentInvalid as e:
            logging.error("Document Invalid Error: " + str(e))
            raise ValueError(
                "Failed SfbReplayer Test Validation. Check the SDN Version or error log.")

    def extract_replay_config(self):
        """
        Return a dictionary of replay configurations. If the element was
        not present, then the value will be None.

        Returned keys - values (types)

        max_delay   -   (int)
        realtime    -   (bool)
        currenttime -   (bool)
        """
        def str_to_bool(s):
            try:
                return (s.lower() == "true") if s is not None else None
            except ValueError:
                logging.error(
                    "ValueError: String to boolean conversion failed.")
                raise

        def str_to_int(s):
            try:
                return int(s) if s is not None else None
            except ValueError:
                logging.error(
                    "ValueError: String to int conversion failed.")
                raise
        max_delay_xpath = "./{0}MockerConfiguration/{0}MaxDelay".format(self.default_ns)
        realtime_xpath = "./{0}MockerConfiguration/{0}RealTime".format(self.default_ns)
        currenttime_xpath = "./{0}MockerConfiguration/{0}CurrentTime".format(self.default_ns)
        max_delay = self.mock_test.findtext(max_delay_xpath)
        realtime = self.mock_test.findtext(realtime_xpath)
        currenttime = self.mock_test.findtext(currenttime_xpath)

        return {'max_delay': str_to_int(max_delay),
                'realtime': str_to_bool(realtime),
                'currenttime': str_to_bool(currenttime)}

    def extract_replay_messages(self):
        mock_messages_tag = "./{0}MockMessages".format(self.default_ns)
        sdn_message_tag = "{0}{1}".format(self.default_ns, SdnMessage.get_root_tag())
        sql_query_tag = "{0}{1}".format(self.default_ns, SqlQueryMessage.get_root_tag())
        mock_messages = []

        mock_messages_elem = self.mock_test.find(mock_messages_tag)
        if mock_messages_elem is None:
            return mock_messages

        for msg in list(mock_messages_elem):
            if (msg.tag == sdn_message_tag):
                msg = SdnMessage(msg)
            elif (msg.tag == sql_query_tag):
                msg = SqlQueryMessage(msg)
            else:
                raise ValueError("Unrecognised Mock Message : " + str(msg.tag))
            mock_messages.append(msg)
        return mock_messages

    def calculate_delay(self, curr_timestamp, prev_timestamp):
        # Find the wait delay
        delay = 0
        if self.replay_config['realtime']:
            if prev_timestamp is not None:
                time_diff = curr_timestamp - prev_timestamp
                delay = int(time_diff.total_seconds())
        else:
            delay = self.replay_config['max_delay']
        # Delay must be non-negative and less than max_delay.
        delay = min(self.replay_config['max_delay'], delay)
        delay = max(delay, 0)
        return delay

    def update_timestamps(self):
        old_timestamp = None
        for msg in self.replay_messages:
            if old_timestamp is None:
                # This is the first message
                old_timestamp = msg.get_timestamp()
                new_timestamp = DT.datetime.now(DT.timezone.utc)
            else:
                # Calculate the time differential
                delta = msg.get_timestamp() - old_timestamp
                old_timestamp = msg.get_timestamp()
                new_timestamp = new_timestamp + delta
            msg.set_timestamp(new_timestamp)

    def __str__(self):
        """
        Readable representation of the SfbReplayer instance, shows the mocker configurations within
        """
        template = "SfbReplayer Configurations :\n"
        template += str(self.sdn_mocker) + '\n' if self.sdn_mocker else ''
        template += str(self.odbc_mocker) + '\n' if self.odbc_mocker else ''
        return template
