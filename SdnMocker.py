import urllib.request as UR
from urllib.request import Request
from xmlmessage import SdnMessage
from xmlmessage import XMLMessageFactory
from xmlmessage import SdnReplayMessage
import argparse
import logging
import time


# Read in the file
# Look for configuration seconds or die
# Loop through each sdn message and replay accordingly

def main():
    start_logging()
    args = parse_sys_args()
    #r = extract_replay_config(args.infile)
    # print(r)
    replay_sdn_messages(args.infile)


def extract_replay_config(infile_path):
    """
    Returns a dictionary of configuration settings.
    """
    with open(infile_path, mode="rt", errors="strict") as infile:
        with XMLMessageFactory(infile, SdnReplayMessage) as replay_gen:
            replay_msg = next(iter(replay_gen))
            return {'TargetUrl': replay_msg.get_target_url(),
                    'TargetIp': replay_msg.get_target_ip(),
                    'TargetPort': replay_msg.get_target_port(),
                    'MaxDelay': replay_msg.get_max_delay(),
                    'RealTime': replay_msg.is_realtime()}


def replay_sdn_messages(infile_path):
    replay_config = extract_replay_config(infile_path)
    with open(infile_path, mode="rt", errors="strict") as infile:
        with XMLMessageFactory(infile, SdnMessage) as sdn_gen:
            for sdn_msg in sdn_gen:
                post_request = Request(replay_config['TargetUrl'],
                                       data=str(sdn_msg).encode('ascii'),
                                       headers={'Content-Type': 'application/xml'})
                response = UR.urlopen(post_request)
                if replay_config['RealTime'] == True:
                    # Sleep for the time interval
                    print('RealTime : sleep 5.')
                    time.sleep(5)
                else:
                    # Sleep for the max time delay
                    print('RealTime off : sleep max.')
                    time.sleep(replay_config['MaxDelay'])
                print(response.read())


def start_logging():
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        filename="last_run.log",
                        filemode="w",
                        level=logging.DEBUG)


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(description="""
        Skype for Business SDN Replay Tool.

        Functionality includes:
            Mocking the Skype SDN API using preconfigured SDN messages.

            Mock File Format:
                <SdnReplay>
                    <Description>...</Description>
                    <Configuration>

                    </Configuration>
                </SdnReplay>
                <LyncDiagnostic>
                    ...
                </LyncDiagnostic>
                ...

            Restrictions:

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
