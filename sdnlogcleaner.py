import logging
import logging.config
from . import logging_conf
import argparse
from .cleaner.cleaner import clean


def main():
    args = parse_sys_args()
    clean(args.infile, args.outfile)


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
    Skype for Business SDN Log Cleaner Tool.

    Designed to clean up IRLYNC logs of artifacts left from logging.
    Fixes split-log issues and removes trailing '.' characters.
    Outputs only the SDN Message blocks.

    """)
    arg_parser.add_argument("infile",
                            type=str,
                            help="Path to the input IRLYNC log file.")
    arg_parser.add_argument("outfile",
                            type=str,
                            help="""Path to the output file.
                            This will contain all SDN messages from the input log.""")
    return arg_parser.parse_args()

if __name__ == '__main__':
    # Load logging configurations
    logging.config.dictConfig(logging_conf.LOGGING_CONFIG)
    main()
