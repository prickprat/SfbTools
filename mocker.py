import http.client
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from xmlmessage import SdnMessage
from xmlmessage import SqlQueryMessage
from xmlmessage import MockerConfiguration
from lxml import etree as ET
import argparse
import logging
import logging.config
import logging_conf
import time
import datetime as DT
import pyodbc
import ast


class SdnMocker():

    """
    Generates a configurable instance of a SDN mocker.
    Uses the Mocker interface.
    """

    def __init__(self, **kwargs):
        try:
            self.receiver = kwargs['receiver']
        except KeyError as e:
            logging.error("KeyError : " + str(e))
            raise ValueError("receiver must be given as parameters.")

    @classmethod
    def fromdict(cls, config_dict):
        """
        Initialise SdnMocker from dictionary.
        """
        return cls(**config_dict)

    def open(self):
        """
        Returns true if the receiver is responsive to POST requests.
        """
        try:
            response = urlopen(self.receiver, data="".encode("us-ascii"), timeout=1)
            return (response.status == http.client.OK)
        except URLError:
            return False

    def close(self):
        """
        Does nothing.
        """
        pass

    def send(self, data):
        """
        Sends a http POST request to the configured Target Url.
        Raises URLError on errors.

        Returns True if client received a
        response from the server, False otherwise.

        data    -   String in byte code format (e.g. us-ascii)
        """
        post_request = Request(self.receiver,
                               data=data,
                               headers={'Content-Type': 'application/xml'})
        response = urlopen(post_request)
        return True if response is not None else False

    def send_message(self, sdn_msg, delay):
        """
        Sends the given SdnMessage using http POST to the Target Url.
        The delay applied is either:
            If RealTime was configured False    =>  The configured Max Delay
            If RealTime was configured True     =>  The smaller of the time interval
                                                    from the previous message
                                                    or the max_delay.
        """

        try:
            print('Sdn Mocker Sleeping for {0}s.'.format(delay))
            time.sleep(delay)
            print("Sending Sdn Message : " + str(sdn_msg))
            if self.send(sdn_msg.tostring(encoding="us-ascii").encode("us-ascii")):
                print("Response Received from Server.")
        except URLError as e:
            logging.error("URLError : " + str(e))
            print("Connection Error! Check the receiver in the sdn configuration.")


class OdbcMocker():

    """
    Generates a configurable instance of an ODBC mocker.
    Uses the Mocker interface.
    """

    def __init__(self, **kwargs):
        try:
            self.driver = kwargs['driver']
            self.server = kwargs.get('server')
            self.database = kwargs['database']
            self.uid = kwargs['uid']
            self.pwd = kwargs['pwd']
            self._connection = None
            self._closed = True
        except KeyError as e:
            logging.error("KeyError : " + str(e))
            raise ValueError(
                "driver, server, database, uid, pwd must be given as keyword parameters.")

    @classmethod
    def fromdict(cls, config_dict):
        """
        Initialise OdbcMocker from dictionary.
        """
        return cls(**config_dict)

    def open(self):
        """
        Opens the odbc connection.
        """
        print("Trying to connect")
        try:
            if self._closed:
                self._connection = pyodbc.connect(driver=self.driver,
                                                  server=self.server,
                                                  database=self.database,
                                                  uid=self.uid,
                                                  pwd=self.pwd)
                self._closed = False
        except:
            print("POKEMON EXCEPTION!!")
            raise

    def close(self):
        """
        Closes the odbc connection.
        """
        if not self._closed and self._connection is not None:
            self._connection.close()
        self._closed = True

    def send(self, data):
        """
        Executes and Commits the given query using an existing connection.
        """
        if self._closed:
            logging.debug("Connection is Closed. Ignoring Send Command.")
            return

        cursor = self._connection.cursor()
        cursor.execute(data)
        self._connection.commit()

    def send_message(self, sql_msg, delay):
        """
        """
        print('Odbc Mocker Sleeping for {0}s.'.format(delay))
        time.sleep(delay)
        print("Sending Sql Query Message : " + str(sql_msg))
        self.send(sql_msg.get_query())


def main():
    args = parse_sys_args()

    sdn_config = None
    odbc_config = None
    if args.sdn_config is not None:
        sdn_config = process_dict_arg(args.sdn_config)
        sdn_version = sdn_config.get('version', '2.1.1')
    if args.odbc_config is not None:
        odbc_config = process_dict_arg(args.odbc_config)

    # Use correct schema for SDN version
    mocker_xsd_path = './schemas/Mocker.Schema.C.xsd'
    if sdn_version == '2.2':
        mocker_xsd_path = './schemas/Mocker.Schema.D.xsd'

    print('SDN VERSION:', sdn_version)

    # Valide Mock Test against the XML Schema
    validate_mock_test(args.infile, mocker_xsd_path)

    # Run the Mocker
    run_mocker(args.infile, sdn_config, odbc_config)


def calculate_delay(is_realtime, max_delay, curr_timestamp, prev_timestamp):
    # Find the wait delay
    delay = 0
    if is_realtime:
        if prev_timestamp is not None:
            time_diff = curr_timestamp - prev_timestamp
            delay = int(time_diff.total_seconds())
    else:
        delay = max_delay
    # Delay must be non-negative and less than max_delay.
    delay = min(max_delay, delay)
    delay = max(delay, 0)
    return delay


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


def validate_mock_test(mock_file_path, mocker_xsd_path):
    # Parse the Mocker Test
    try:
        mock_test = ET.parse(mock_file_path)
    except ET.ParseError as e:
        logging.error("ParseError whilst parsing mock file : " + str(e))
        raise ValueError("Invalid Mocker Test XML Format.")

    mocker_schema_doc = ET.parse(mocker_xsd_path)
    mocker_schema = ET.XMLSchema(mocker_schema_doc)
    try:
        mocker_schema.assertValid(mock_test)
    except ET.DocumentInvalid as e:
        logging.error("Document Invalid Error: " + str(e))
        raise ValueError("Failed Mocker Test Validation. Check the SDN Version or error log.")


def extract_mock_messages(mock_test, default_ns):
    mock_messages = []
    for msg in list(mock_test.find("./{{{0}}}MockMessages".format(default_ns))):
        if (msg.tag == "{{{0}}}{1}".format(default_ns, SdnMessage.get_root_tag())):
            msg = SdnMessage(msg)
        elif (msg.tag == "{{{0}}}{1}".format(default_ns, SqlQueryMessage.get_root_tag())):
            msg = SqlQueryMessage(msg)
        else:
            raise ValueError("Unrecognised Mock Message.")
        mock_messages.append(msg)
    return mock_messages


def update_message_timestamp(mock_messages):
    old_timestamp = None
    for msg in mock_messages:
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
    return mock_messages


def run_mocker(mock_file_path, sdn_config=None, odbc_config=None):
    mock_test = ET.parse(mock_file_path)

    default_ns = mock_test.getroot().nsmap.get(None, '')
    test_config_elem = mock_test.find('./{{{0}}}MockerConfiguration'.format(default_ns))
    test_config = MockerConfiguration(test_config_elem).todict()
    print(test_config)
    # Initialise the mockers
    sdn_mocker = None
    odbc_mocker = None
    try:
        if sdn_config is not None:
            sdn_mocker = SdnMocker.fromdict(sdn_config)
            # sdn_mocker.open()
        if odbc_config is not None:
            odbc_mocker = OdbcMocker.fromdict(odbc_config)
            odbc_mocker.open()

        # Parse the messages and convert timestamps
        mock_messages = extract_mock_messages(mock_test, default_ns)
        if test_config['currenttime']:
            mock_messages = update_message_timestamp(mock_messages)

        # Send the messages using appropriate mocker and intervals
        prev_timestamp = None
        for msg in mock_messages:
            mocker = None
            if isinstance(msg, SdnMessage):
                mocker = sdn_mocker
            elif isinstance(msg, SqlQueryMessage):
                mocker = odbc_mocker
            else:
                raise ValueError("Unrecognised Mock Message instance.")

            delay = calculate_delay(test_config['realtime'],
                                    test_config['max_delay'],
                                    msg.get_timestamp(),
                                    prev_timestamp)
            mocker.send_message(msg, delay)
            prev_timestamp = msg.get_timestamp()

    finally:
        if sdn_mocker is not None:
            sdn_mocker.close()
        if odbc_mocker is not None:
            odbc_mocker.close()


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
                        against Mocker.Schema.xsd before it is fired.
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
