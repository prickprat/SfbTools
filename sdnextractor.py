import logging
import logging.config
import logging_conf
import argparse
from xmlmessage import SdnMessage
from xmlmessage import XMLMessageFactory
import logcleaner


def main():
    args = parse_sys_args()
    if args.clean_log:
        logCleaner = logcleaner.LogCleaner(args.infile, args.outfile)
        logCleaner.clean()
    else:
        extract_sdn_messages(args.infile, args.outfile,
                             args.call_ids, args.conf_ids)


def extract_sdn_messages(infile_path, outfile_path, call_ids, conf_ids):

    with open(infile_path, mode="rt", errors="strict") as infile:
        with open(outfile_path, mode="wt", errors="strict") as outfile:
            with XMLMessageFactory(infile, SdnMessage) as xml_gen:
                logging.info("Parsing Sdn Messages.")
                for sdn_msg in xml_gen:
                    logging.info("Parse Success.")
                    if call_ids is not None:
                        if not sdn_msg.contains_call_id(*call_ids):
                            logging.info("No matching call id : Skipping.")
                            continue
                    if conf_ids is not None:
                        if not sdn_msg.contains_conf_id(*conf_ids):
                            logging.info("No matching conf id : Skipping.")
                            continue

                    outfile.write('\n\n')
                    outfile.write(str(sdn_msg))
                    logging.info("Sdn message written to outfile.")


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(description="""
        Skype for Business SDN Extractor Tool.
        Functionality includes: Extracting SDN messages from log files
        with specific call or conference ids, and cleaning the logs files of
        formatting errors.
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
    arg_parser.add_argument("--clean-log",
                            action="store_true",
                            help="""Cleans the log file of all non-xml data
                            and reformats split-logs (i.e. caused by SDN
                            messages being too large for a single log message.
                            This is usually the cause of Parse Errors).""")

    return arg_parser.parse_args()


if __name__ == '__main__':
    # Load logging configurations
    logging.config.dictConfig(logging_conf.LOGGING_CONFIG)
    main()
