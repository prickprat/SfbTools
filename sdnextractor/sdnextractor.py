import logging
import logging.config
import sfbtools.sdnextractor.logging_conf as log_conf
import argparse
from sfbtools.sdnextractor.xmlmessage import SdnMessage
from sfbtools.sdnextractor.xmlmessage import XMLMessageFactory


def main():
    args = parse_sys_args()
    extract_sdn_messages(args.infile, args.outfile,
                         args.call_ids, args.conf_ids)


def extract_sdn_messages(infile_path, outfile_path, call_ids, conf_ids):

    with open(infile_path, mode="rt", errors="strict") as infile:
        with open(outfile_path, mode="wt", errors="strict") as outfile:
            with XMLMessageFactory(infile, SdnMessage) as xml_gen:
                logging.info("Attempting to parse Sdn Messages.")
                for sdn_msg in xml_gen:
                    logging.debug("Parse Success.")
                    if call_ids is not None:
                        if not sdn_msg.contains_call_id(*call_ids):
                            logging.debug("Skipping : Not in given call-ids list.")
                            continue
                    if conf_ids is not None:
                        if not sdn_msg.contains_conf_id(*conf_ids):
                            logging.debug("Skipping : Not in given conf-ids list.")
                            continue

                    outfile.write('\n\n')
                    outfile.write(sdn_msg.tostring(encoding="utf-8"))
                logging.info("Sdn messages successfully extracted.")


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
    logging.config.dictConfig(log_conf.LOGGING_CONFIG)
    main()
