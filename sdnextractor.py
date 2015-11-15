import logging
import logging.config
from . import logging_conf
import argparse
from .extractor.extractor import extract_sdn_messages


def main():
    args = parse_sys_args()
    extract_sdn_messages(args.infile, args.outfile,
                         args.call_ids, args.conf_ids)


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
    Skype for Business SDN Extractor Tool.

    Extracts SDN messages from clean log files to a single output file.
    Users can filter SDN messages based on specific Call Ids or Conference Ids, or both.

    When both conference ids and call ids are specified, then any sdn messages with either ids
    will be included in the extraction.

    **NB: Raw IRLYNC log files should be cleaned with the SDN Log Cleaner Tool first.**

    """)
    arg_parser.add_argument("infile",
                            type=str,
                            help="Path to the input file. This must be the first argument.")
    arg_parser.add_argument("outfile",
                            type=str,
                            help="Path to the output file. This must be the second argument.")
    arg_parser.add_argument("--conf-ids",
                            metavar="CONF_ID",
                            type=str,
                            nargs="+",
                            help="""The sdn message will only be included if it contains
                            a conf id from the given space separated list.""")
    arg_parser.add_argument("--call-ids",
                            metavar="CALL_ID",
                            type=str,
                            nargs="+",
                            help="""The sdn message will only be included if it contains
                            a call id from the given space separated list.""")

    return arg_parser.parse_args()


if __name__ == '__main__':
    # Load logging configurations
    logging.config.dictConfig(logging_conf.LOGGING_CONFIG)
    main()
