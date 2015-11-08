from mocker import SdnMocker
from mocker import OdbcMocker
from xmlmessage import SdnMessage
from xmlmessage import SqlQueryMessage
from xmlmessage import MockerConfiguration
from lxml import etree as ET
import argparse
import logging
import logging.config
import logging_conf
import datetime as DT
import ast
import os


class SfbReplay():

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
            print("SDN VERSION : " + str(self.sdn_config['version']))

        # Validate Mock Test against the XML Schema
        if kwargs.get('validate', True):
            self.validate()

        self.replay_config = self.extract_replay_config()
        print("REPLAY CONFIG: " + str(self.replay_config))

        self.replay_messages = self.extract_replay_messages()
        print("REPLAY MESSAGES: {0} found.".format(len(self.replay_messages)))

        if self.replay_config['currenttime']:
            self.update_timestamps()
            print("TIMESTAMPS UPDATED")

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
        # Initialise the mockers
        sdn_mocker = None
        odbc_mocker = None
        try:
            print("Configuring Mockers ... ")
            if self.sdn_config is not None:
                sdn_mocker = SdnMocker(**self.sdn_config)
                print(sdn_mocker)
                sdn_mocker.open()
            if self.odbc_config is not None:
                odbc_mocker = OdbcMocker(**self.odbc_config)
                print(odbc_mocker)
                odbc_mocker.open()

            # Send the messages using appropriate mocker and intervals
            prev_timestamp = None
            for msg in self.replay_messages:
                mocker = None
                if isinstance(msg, SdnMessage):
                    mocker = sdn_mocker
                elif isinstance(msg, SqlQueryMessage):
                    mocker = odbc_mocker
                else:
                    raise ValueError("Unrecognised Mock Message instance.")

                delay = self.calculate_delay(msg.get_timestamp(),
                                             prev_timestamp)
                mocker.send_message(msg, delay)
                prev_timestamp = msg.get_timestamp()

        finally:
            if sdn_mocker is not None:
                sdn_mocker.close()
            if odbc_mocker is not None:
                odbc_mocker.close()

    def validate(self):
        # Use correct schema for SDN version
        # no SDN or SDN version 2.1.1 use schema C
        schema_file = "Mocker.Schema.C.xsd"
        if (self.sdn_config is not None
                and self.sdn_config['version'] == 2.2):
            schema_file = "Mocker.Schema.D.xsd"
        schema_path = os.path.join(os.path.dirname(__file__), 'schemas/' + schema_file)
        schema_doc = ET.parse(schema_path)
        schema = ET.XMLSchema(schema_doc)
        try:
            schema.assertValid(self.mock_test)
        except ET.DocumentInvalid as e:
            logging.error("Document Invalid Error: " + str(e))
            raise ValueError(
                "Failed SfbReplay Test Validation. Check the SDN Version or error log.")

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

        for msg in list(self.mock_test.find(mock_messages_tag)):
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


def main():
    args = parse_sys_args()

    sdn_config = None
    odbc_config = None
    if args.sdn_config is not None:
        sdn_config = process_dict_arg(args.sdn_config)
    if args.odbc_config is not None:
        odbc_config = process_dict_arg(args.odbc_config)

    replayer = SfbReplay.fromfile(args.infile,
                                  sdn_config=sdn_config,
                                  odbc_config=odbc_config)
    replayer.run()

    # Run the Mocker
    # run_mocker(args.infile, sdn_config, odbc_config)


# def calculate_delay(is_realtime, max_delay, curr_timestamp, prev_timestamp):
#     # Find the wait delay
#     delay = 0
#     if is_realtime:
#         if prev_timestamp is not None:
#             time_diff = curr_timestamp - prev_timestamp
#             delay = int(time_diff.total_seconds())
#     else:
#         delay = max_delay
#     # Delay must be non-negative and less than max_delay.
#     delay = min(max_delay, delay)
#     delay = max(delay, 0)
#     return delay


def process_dict_arg(arg_str):
    """
    Converts a str representing a python dictionary to a dict.
    Raises ValueError if conversion is not possible.
    """
    try:
        dict_arg = ast.literal_eval(arg_str.strip())
        if not isinstance(dict_arg, dict):
            raise TypeError
        return dict_arg
    except (SyntaxError, TypeError, ValueError) as e:
        logging.error(str(e))
        raise ValueError("Invalid configuration argument.")


# def extract_mock_messages(mock_test, default_ns):
#     mock_messages = []
#     for msg in list(mock_test.find("./{{{0}}}MockMessages".format(default_ns))):
#         if (msg.tag == "{{{0}}}{1}".format(default_ns, SdnMessage.get_root_tag())):
#             msg = SdnMessage(msg)
#         elif (msg.tag == "{{{0}}}{1}".format(default_ns, SqlQueryMessage.get_root_tag())):
#             msg = SqlQueryMessage(msg)
#         else:
#             raise ValueError("Unrecognised Mock Message.")
#         mock_messages.append(msg)
#     return mock_messages


# def update_message_timestamp(mock_messages):
#     old_timestamp = None
#     for msg in mock_messages:
#         if old_timestamp is None:
#             # This is the first message
#             old_timestamp = msg.get_timestamp()
#             new_timestamp = DT.datetime.now(DT.timezone.utc)
#         else:
#             # Calculate the time differential
#             delta = msg.get_timestamp() - old_timestamp
#             old_timestamp = msg.get_timestamp()
#             new_timestamp = new_timestamp + delta
#         msg.set_timestamp(new_timestamp)
#     return mock_messages


# def run_mocker(mock_file_path, sdn_config=None, odbc_config=None):
#     mock_test = ET.parse(mock_file_path)

#     default_ns = mock_test.getroot().nsmap.get(None, '')
#     test_config_elem = mock_test.find(
#         './{{{0}}}MockerConfiguration'.format(default_ns))
#     test_config = MockerConfiguration(test_config_elem).todict()
#     print(test_config)
#     # Initialise the mockers
#     sdn_mocker = None
#     odbc_mocker = None
#     try:
#         print("Configuring Mockers ... ")
#         if sdn_config is not None:
#             sdn_mocker = SdnMocker.fromdict(sdn_config)
#             print(sdn_mocker)
#             sdn_mocker.open()
#         if odbc_config is not None:
#             odbc_mocker = OdbcMocker.fromdict(odbc_config)
#             print(odbc_mocker)
#             odbc_mocker.open()

#         # Parse the messages and convert timestamps
#         mock_messages = extract_mock_messages(mock_test, default_ns)
#         if test_config['currenttime']:
#             mock_messages = update_message_timestamp(mock_messages)

#         # Send the messages using appropriate mocker and intervals
#         prev_timestamp = None
#         for msg in mock_messages:
#             mocker = None
#             if isinstance(msg, SdnMessage):
#                 mocker = sdn_mocker
#             elif isinstance(msg, SqlQueryMessage):
#                 mocker = odbc_mocker
#             else:
#                 raise ValueError("Unrecognised Mock Message instance.")

#             delay = calculate_delay(test_config['realtime'],
#                                     test_config['max_delay'],
#                                     msg.get_timestamp(),
#                                     prev_timestamp)
#             mocker.send_message(msg, delay)
#             prev_timestamp = msg.get_timestamp()

#     finally:
#         if sdn_mocker is not None:
#             sdn_mocker.close()
#         if odbc_mocker is not None:
#             odbc_mocker.close()


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
    Skype for Business Mocker Tool.

    This tool is designed to replay a Conference or Call by sending pre-defined
    SDN messages directly to a receiver, and replaying predefined insert/delete
    statements against the SQL database.

    The tool requires a pre-defined 'Mocker Test' as an input file and configurations
    for the SDN receiver and ODBC connection as parameters.

    Each 'Mocker Test' is an XML document representing a test scenario.
    It contains test configurations and Mock Messages sent to either
    the SDN receiver or the database. Details below.

    --------------------------Mock Test File--------------------------

    *********** Format Example ****************

    <Mocker xmlns="http://www.ir.com/Mocker"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://www.ir.com/Mocker ../schemas/Mocker.Schema.xsd">

        <Description>...</Description>
        <MockerConfiguration>
            <MaxDelay>....</MaxDelay>
            <RealTime>....</RealTime>
            <CurrentTime>...</CurrentTime>
        </MockerConfiguration>
        <MockMessages>
            <LyncDiagnostic>
                ...
            </LyncDiagnostic>
            ...
            <SqlQueryMessage>
                <TimeStamp>...</TimeStamp>
                <Query><![CDATA[...]]></Query>
            </SqlQueryMessage>
            ...
        </MockMessages>
    </Mocker>

    *******************************************

    Elements explained :

        Mocker      -   The root element for the xml.
                        Namespace must be 'http://www.ir.com/Mocker' since this test is validated
                        against a schema before it is executed.
        Description -   Short description of the mock test scenario. [Optional]
        MaxDelay    -   The maximum delay time for each consecutive message.
                        Number of seconds.
                        (e.g. 120)
        RealTime    -   Realtime uses the actual time interval between consecutive
                        mock messages. The Max Delay time is still respected.
                        If disabled then the time delay is always Max Delay.
                        true or false.
                        (e.g. true)
        CurrentTime -   If CurrentTime is true, all timestamps for messages will be made relative
                        to the current date-time. The timestamp of the final MockMessage
                        will be replaced with the current UTC timestamp. Preceding message
                        timestamps will also be replaced, depending on RealTime and MaxDelay
                        settings.
                        true or false.
                        (e.g. true)

    -------------------SDN Configuration -----------------------------

    The SDN configuration must be in python dictionary format.

    The following SDN parameters are supported :
        receiver    -   Target URL for the http/https listener
        version     -   The SDN API version of the mock messages.
                        Optional. Default version is 2.1.1

        e.g. --sdn-config "{ 'receiver': 'https://127.0.0.1:3000/SdnApiReceiver/site',
                             'version' : '2.2' }"

    -------------------ODBC Configuration -----------------------------

    The ODBC connection parameters must be in python dictionary format.
    NB: Backslashes must be triple escaped (e.g. \\\\\\\\ for \\)

    The following ODBC parameters are supported :
        driver      -   Odbc Driver used for the connection.
        server      -   Location of database server.
        database    -   Database name. [Optional]
        uid         -   user id. [Optional]
        pwd         -   user password. [Optional]

        e.g. --odbc-config "{ 'driver': 'SQL SERVER',
                              'server': '10.102.70.4\\\\\\\\SqlServer',
                              'database': 'LcsCDR',
                              'uid': 'sa',
                              'pwd': 'C1sc0c1sc0' }" """)

    arg_parser.add_argument("infile",
                            type=str,
                            help="""
                            Path to the Mock Test XML file.
                            See the detailed description above for formatting.""")

    arg_parser.add_argument("--sdn-config",
                            metavar="SDN_PARAMS",
                            type=str,
                            help="""
                            SDN Mocker configuration parameters in python dictionary format.
                            See the detailed description above.""")

    arg_parser.add_argument("--odbc-config",
                            metavar="ODBC_PARAMS",
                            type=str,
                            help="""
                            ODBC connection string parameters in python dictionary format.
                            See the detailed description above.""")

    return arg_parser.parse_args()


if __name__ == "__main__":
    # Load logging configurations
    logging.config.dictConfig(logging_conf.LOGGING_CONFIG)
    main()
