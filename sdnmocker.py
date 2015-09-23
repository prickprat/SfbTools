import http.client
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from xmlmessage import SdnMessage
from xmlmessage import SqlMessage
from xmlmessage import XMLMessageFactory
from xmlmessage import SdnMockerMessage
from xmlmessage import SqlMockerMessage
import xml.etree.ElementTree as ET
import argparse
import logging
import logging.config
import logging_conf
import time
import pyodbc


class SdnMocker():

    """
    Generates a configurable instance of a SDN mocker.
    Uses the Mocker interface.
    """

    def __init__(self, **kwargs):
        try:
            self.target_url = kwargs['target_url']
            self.realtime = kwargs.get('realtime', False)
            self.max_delay = kwargs['max_delay']
            self._prev_sdn_msg = None
        except KeyError as e:
            logging.error("KeyError : " + str(e))
            raise ValueError("target_url and max_delay must be given as parameters.")

    @classmethod
    def fromfilename(cls, file_path):
        """
        Initialise SdnMocker from file.
        File should contain a SdnMockerConfiguration xml element.
        """
        with open(file_path, mode="rt", errors="strict") as infile:
            with XMLMessageFactory(infile, SdnMockerMessage) as mock_gen:
                try:
                    mock_msg = next(iter(mock_gen))
                    return cls.fromdict(mock_msg.todict())
                except StopIteration as e:
                    logging.error("StopIteration Error: " + str(e))
                    raise ValueError("Invalid SdnMocker Message. Check the input file.")

    @classmethod
    def fromdict(cls, config_dict):
        """
        Initialise SdnMocker from dictionary.
        """
        return cls(**config_dict)

    def open(self):
        """
        Returns true if the target url is responsive.
        """
        return (urlopen(self.target_url).status == http.client.OK)

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
        post_request = Request(self.target_url,
                               data=data,
                               headers={'Content-Type': 'application/xml'})
        response = urlopen(post_request)
        return True if response is not None else False


class SqlMocker():

    """
    Generates a configurable instance of a SDN mocker.
    Uses the Mocker interface.

    NB: PASSWORDS ARE CURRENTLY EXPOSED.
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
    def fromfilename(cls, file_path):
        """
        Initialize SqlMocker from file.
        File should contain a SqlMockerConfiguration xml element.
        """
        with open(file_path, mode="rt", errors="strict") as infile:
            with XMLMessageFactory(infile, SqlMockerMessage) as mock_gen:
                try:
                    mock_msg = next(iter(mock_gen))
                    return cls.fromdict(mock_msg.todict())
                except StopIteration:
                    logging.error("StopIteration Error: Possibly an invalid " +
                                  "or non-existent SqlMocker message.")
                    raise ValueError("Invalid SqlMocker Message. Check the input file.")

    @classmethod
    def fromdict(cls, config_dict):
        """
        Initialise SqlMocker from dictionary.
        """
        return cls(**config_dict)

    def open(self):
        """
        Opens the odbc connection.
        """
        if self._closed:
            self._connection = pyodbc.connect(driver=self.driver,
                                              server=self.server,
                                              database=self.database,
                                              uid=self.uid,
                                              pwd=self.pwd)
        self._closed = False

    def close(self):
        """
        Closes the odbc connection.
        """
        if not self._closed and self._connection is not None:
            self._connection.close()
        self._closed = True

    def send(self, data):
        """
        """
        pass

    def send_sqlmessage(self, sql_msg):
        """
        """
        pass


def main():
    args = parse_sys_args()
    mock_sdn_messages(args.infile)


def mock_sdnmessage(sdn_mocker, sdn_msg, prev_timestamp):
    """
    Sends the given SdnMessage using http POST to the Target Url.
    The delay applied is either:
        If RealTime was configured False    =>  The configured Max Delay
        If RealTime was configured True     =>  The smaller of the time interval
                                                from the previous message
                                                or the max_delay.
    """
    if sdn_mocker.realtime:
        if prev_timestamp is not None:
            delay = int((sdn_msg.get_timestamp() -
                         prev_timestamp).total_seconds())
        else:
            # This is the first Message
            delay = 0
    else:
        delay = self.max_delay
    # Delay must be non-negative and less than max_delay.
    delay = min(self.max_delay, delay)
    delay = max(delay, 0)

    try:
        print('Sdn Mocker Sleeping for {0}s.'.format(delay))
        time.sleep(delay)
        print("Sending Sdn Message : " + str(sdn_msg))
        if self.send(sdn_msg.tostring(encoding="us-ascii")):
            print("Response Received from Server.")
    except URLError as e:
        logging.error("URLError : " + str(e))
        print("Connection Error! Check the Target Url in the SqlMocker element.")
    finally:
        self._prev_sdn_msg = sdn_msg


def mock_sdn_messages(infile_path):
    sdn_mocker = SdnMocker.fromfilename(infile_path)

    with open(infile_path, mode="rt", errors="strict") as infile:
        with XMLMessageFactory(infile, SdnMessage) as sdn_gen:
            for sdn_msg in sdn_gen:
                sdn_mocker.send_sdnmessage(sdn_msg)


def mock_sql_queries(infile_path):
    # Get configuration

    # Start a connection if not already connected

    # Send the query
    pass


def run_mocker(mock_file_path):
    # Parse the mocker file
    try:
        mock_test = ET.parse(mock_file_path)
    except ET.ParseError as e:
        logging.error("ParseError whilst parsing mock file : " + str(e))
        raise ValueError("Invalid Mocker Test Format. Read the help text for formatting.")

    sdn_mocker = None
    sql_mocker = None

    # Initialise the mockers
    try:
        sdn_config_elem = mock_test.find('./' + SdnMockerMessage.get_root_tag())
        sql_config_elem = mock_test.find('./' + SqlMockerMessage.get_root_tag())
        if sdn_config_elem is not None:
            sdn_mocker_config = SdnMockerMessage(sdn_config_elem).todict()
            sdn_mocker = SdnMocker.fromdict(sdn_mocker_config)
        if sql_config_elem is not None:
            sql_mocker_config = SqlMockerMessage(sql_config_elem).todict()
            sql_mocker = SqlMocker.fromdict(sql_mocker_config)
    except ValueError as e:
        raise

    # Parse the messages and send them
    for msg in list(mock_test.find("./MockMessages")):
        if msg.tag == SdnMessage.get_root_tag():
            sdn_mocker.send_sdnmessage(SdnMessage(msg))
        elif msg.tag == SqlMessage.get_root_tag():
            sql_mocker.send_sqlmessage(SqlMessage(msg))


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
    Skype for Business SDN Mocker Tool.

    Mocks the Skype SDN API using pre-configured SDN messages.
    Each Sdn Mocker test is configured as a single xml file.
    The file must contain a SdnMocker element which configures the tool and
    successive LyncDiagnostic Messages which will be sent in order of
    appearance to the target server.

    -------------------Mock File Format : Example -----------------
    <Mocker>
        <Description>...</Description>
        <Configuration>
            <MaxDelay>....</MaxDelay>
            <RealTime>....</RealTime>
            <SdnMocker>
                <TargetUrl>...</TargetUrl>
            </SdnMocker>
            <SqlMocker>
                <Driver>...</Driver>
                <Server>...</Server>
                <Database>...</Database>
                <UID>...</UID>
                <PWD>...</PWD>
            </SqlMocker>
        </Configuration>
        <MockMessages>
            <LyncDiagnostic>
                ...
            </LyncDiagnostic>
            ...
            <SqlMessage>
                <TimeStamp>...</TimeStamp>
                <Query>...</Query>
            </SqlMessage>
            ...
        </MockMessages>
    </Mocker>
    ----------------------------------------------------------------

    Configuration Options:
        Description -   Short description of the mock scenario. [Optional]
        TargetUrl   -   The full url of the SDN receiver.
                        (e.g. https://127.0.0.1:3000/SdnApiReceiver/site)
        MaxDelay    -   The maximum delay time for each consecutive message.
                        Number of seconds.
                        (e.g. 120)
        RealTime    -   Realtime uses the actual time interval between consecutive
                        messages in the file. The Max Delay time is still respected.
                        If disabled then the time delay is always Max Delay. True or False.
                        (e.g. True)
        """)
    arg_parser.add_argument("infile",
                            type=str,
                            help="""
                            Path to the input file.
                            This needs to be in the Mock file format as above.
                            """)
    return arg_parser.parse_args()


if __name__ == "__main__":
    # Load logging configurations
    logging.config.dictConfig(logging_conf.LOGGING_CONFIG)
    main()
