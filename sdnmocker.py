from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from xmlmessage import SdnMessage
from xmlmessage import XMLMessageFactory
from xmlmessage import SdnMockerMessage
import argparse
import logging
import logging.config
import logging_conf
import time


def main():
    args = parse_sys_args()
    mock_sdn_messages(args.infile)


def extract_mock_config(infile_path):
    """
    Returns a dictionary of configuration settings.
    """
    with open(infile_path, mode="rt", errors="strict") as infile:
        with XMLMessageFactory(infile, SdnMockerMessage) as mock_gen:
            try:
                mock_msg = next(iter(mock_gen))
                return mock_msg.todict()
            except StopIteration as e:
                logging.error("StopIteration Error: Possibly an invalid " +
                              "or non-existant SdnMocker message.")
                raise ValueError("Invalid SdnMocker Message. Check the input file.")



def mock_sdn_messages(infile_path):
    config = extract_mock_config(infile_path)
    wait_time = 0 if (config['RealTime']) else config['MaxDelay']

    with open(infile_path, mode="rt", errors="strict") as infile:
        with XMLMessageFactory(infile, SdnMessage) as sdn_gen:
            prev_sdn_msg = None
            for sdn_msg in sdn_gen:
                post_request = Request(config['TargetUrl'],
                                       data=sdn_msg.tostring(encoding="us-ascii"),
                                       headers={'Content-Type': 'application/xml'})
                if config['RealTime']:
                    # Calculate the time to wait from the time interval
                    if prev_sdn_msg is not None:
                        time_diff = (sdn_msg.get_timestamp() -
                                     prev_sdn_msg.get_timestamp()).total_seconds()
                        time_diff = int(time_diff)
                        if (time_diff >= 0 and time_diff <= config['MaxDelay']):
                            wait_time = time_diff
                        else:
                            wait_time = config['MaxDelay']
                    prev_sdn_msg = sdn_msg

                try:
                    print('RealTime {0} : Sleeping for {1}s.'.format(config['RealTime'], wait_time))
                    time.sleep(wait_time)
                    print("Sending Sdn Message : " + str(sdn_msg))
                    response = urlopen(post_request)
                    if response is not None:
                        print("Server Response Recevied.")
                except URLError as e:
                    logging.error("URLError : " + str(e))
                    print("Connection Error! Check the Target Url in the SdnMocker element.")
                    return


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
    Skype for Business SDN Mocker Tool.

    Mocks the Skype SDN API using preconfigured SDN messages. Each Sdn Mocker test is configured as a
    single xml file. The file must contain a SdnMocker element which configures the tool and
    successive LyncDiagnostic Messages which will be sent in order of appearance to the target server.

    Technically the mock xml file is malformed, since it doesn't have a root element.
    This may change in the future.

    Mock File Format:

        <SdnMocker>
            <Description>...</Description>
            <Configuration>
                <TargetUrl>...</TargetUrl>
                <MaxDelay>....</MaxDelay>
                <RealTime>....</RealTime>
            </Configuration>
        </SdnMocker>
        <LyncDiagnostic>
            ...
        </LyncDiagnostic>
        ...

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
