from urllib.request import urlopen
from urllib.request import Request
from xmlmessage import SdnMessage
from xmlmessage import XMLMessageFactory
from xmlmessage import SdnReplayMessage
import argparse
import logging
import time


def main():
    start_logging()
    args = parse_sys_args()
    replay_sdn_messages(args.infile)


def extract_replay_config(infile_path):
    """
    Returns a dictionary of configuration settings.
    """
    with open(infile_path, mode="rt", errors="strict") as infile:
        with XMLMessageFactory(infile, SdnReplayMessage) as replay_gen:
            replay_msg = next(iter(replay_gen))
            return replay_msg.todict()


def replay_sdn_messages(infile_path):
    config = extract_replay_config(infile_path)
    wait_time = 0 if (config['RealTime']) else config['MaxDelay']

    with open(infile_path, mode="rt", errors="strict") as infile:
        with XMLMessageFactory(infile, SdnMessage) as sdn_gen:
            prev_sdn_msg = None
            for sdn_msg in sdn_gen:
                post_request = Request(config['TargetUrl'],
                                       data=sdn_msg.totext(),
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

                print('RealTime {0} : Sleeping for {1}s.'.format(config['RealTime'], wait_time))
                time.sleep(wait_time)
                print("Sending Sdn Message : " + str(sdn_msg))
                response = urlopen(post_request)
                print("Server Response : " + str(response.read()))


def start_logging():
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        filename="last_run.log",
                        filemode="w",
                        level=logging.DEBUG)


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description="""
    Skype for Business SDN Replay Tool.

    Functionality includes:
        Mocking the Skype SDN API using preconfigured SDN messages.

    Mock File Format:

        <SdnReplay>
            <Description>...</Description>
            <Configuration>
                <TargetUrl>...</TargetUrl>
                <MaxDelay>...</MaxDelay>
                <RealTime>...</RealTime>
            </Configuration>
        </SdnReplay>
        <LyncDiagnostic>
            ...
        </LyncDiagnostic>
        ...

    Configuration Options:

        TargetUrl   -   The full url of the receiving server.
                        (e.g. https://127.0.0.1:3000/SdnReceiver/)
        MaxDelay    -   The maximum delay time for each consecutive message.
                        Number of seconds.
                        (e.g. 120)
        RealTime    -   Realtime uses the actual time interval between
                        consecutive messages in the file. The Max Delay time is respected.
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
    main()
