import http.client
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from xmlmessage import SdnMessage
from xmlmessage import SqlQueryMessage
from xmlmessage import MockerConfiguration
import xml.etree.ElementTree as ET
import argparse
import logging
import logging.config
import logging_conf
import time
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
            if self.send(sdn_msg.tostring(encoding="us-ascii")):
                print("Response Received from Server.")
        except URLError as e:
            logging.error("URLError : " + str(e))
            print("Connection Error! Check the Target Url in the OdbcMocker element.")


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
    if args.odbc_config is not None:
        odbc_config = process_dict_arg(args.odbc_config)

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


def run_mocker(mock_file_path, sdn_config=None, odbc_config=None):
    # Parse the mocker file
    try:
        mock_test = ET.parse(mock_file_path)
    except ET.ParseError as e:
        logging.error("ParseError whilst parsing mock file : " + str(e))
        raise ValueError("Invalid Mocker Test Format.")

    test_config_elem = mock_test.find(MockerConfiguration.get_root_tag())
    test_config = MockerConfiguration(test_config_elem).todict()
    print(test_config)
    # Initialise the mockers
    sdn_mocker = None
    odbc_mocker = None
    try:
        if sdn_config is not None:
            sdn_mocker = SdnMocker.fromdict(sdn_config)
            sdn_mocker.open()
        if odbc_config is not None:
            odbc_mocker = OdbcMocker.fromdict(odbc_config)
            odbc_mocker.open()

        # Parse the messages and send them
        prev_timestamp = None
        for msg in list(mock_test.find("./MockMessages")):
            mocker = None
            if (msg.tag == SdnMessage.get_root_tag()):
                msg = SdnMessage(msg)
                mocker = sdn_mocker
            elif (msg.tag == SqlQueryMessage.get_root_tag()):
                msg = SqlQueryMessage(msg)
                mocker = odbc_mocker
            else:
                continue

            delay = calculate_delay(test_config['realtime'],
                                    test_config['max_delay'],
                                    msg.get_timestamp(),
                                    prev_timestamp)
            if mocker is not None:
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

    Mocks the Skype SDN API using pre-configured SDN messages.
    Each Sdn Mocker test is configured as a single xml file.
    The file must contain a SdnMocker element which configures the tool and
    successive LyncDiagnostic Messages which will be sent in order of
    appearance to the target server.

    -------------------Mock File Format : Example -----------------
    <Mocker>
        <Description>...</Description>
        <MockerConfiguration>
            <MaxDelay>....</MaxDelay>
            <RealTime>....</RealTime>
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
    ----------------------------------------------------------------

    Configuration Options:
        Description -   Short description of the mock test scenario. [Optional]
        MaxDelay    -   The maximum delay time for each consecutive message.
                        Number of seconds.
                        (e.g. 120)
        RealTime    -   Realtime uses the actual time interval between consecutive
                        messages in the file. The Max Delay time is still respected.
                        If disabled then the time delay is always Max Delay. True or False.
                        (e.g. True)

    The following ODBC parameters are supported :
        driver      -   Odbc Driver used for the connection.
        server      -   Location of database server.
        database    -   Database name. [Optional]
        uid         -   user id. [Optional]
        pwd         -   user password. [Optional]

""")
    arg_parser.add_argument("infile",
                            type=str,
                            help="""
                            Path to the input file.
                            This needs to be in the Mock file format as above.
                            """)

    arg_parser.add_argument("--sdn-config",
                            metavar="SDN_PARAMS",
                            type=str,
                            help="""SDN configuration must be in dictionary format.
                            E.g.
                            { "receiver": "https://127.0.0.1:3000/SdnApiReceiver/site" }""")

    arg_parser.add_argument("--odbc-config",
                            metavar="ODBC_PARAMS",
                            type=str,
                            help=r"""ODBC connection string parameters in python dictionary format.
                            E.g. { "driver": "SQL SERVER",
                              "server": "10.102.70.4\\\\SqlServer",
                              "database": "LcsCDR",
                              "uid": "sa",
                              "pwd": "C1sc0c1sc0" }""")

    return arg_parser.parse_args()


if __name__ == "__main__":
    # Load logging configurations
    logging.config.dictConfig(logging_conf.LOGGING_CONFIG)
    main()
