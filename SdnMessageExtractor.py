import logging
import argparse
import mmap
import re
import SdnMessage
import LogCleaner
from xml.etree.ElementTree import ParseError as ParseError


def main():
    start_logging()
    args = parse_sys_args()
    if args.clean_log:
        logCleaner = LogCleaner.LogCleaner(args.infile, args.outfile)
        logCleaner.clean()
    else:
        extract_sdn_messages(args.infile, args.outfile,
                             args.call_ids, args.conf_ids)


def extract_sdn_messages(infile_path, outfile_path, call_ids, conf_ids):
    lyncDiagRegex = re.compile(br"<LyncDiagnostics.*?>.*?</LyncDiagnostics>",
                               re.DOTALL | re.MULTILINE | re.IGNORECASE)

    with open(infile_path, mode="rt", errors="strict") as infile:
        mm_infile = mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ)

        with open(outfile_path, mode="wt", errors="strict") as outfile:
            all_matches = lyncDiagRegex.finditer(mm_infile)
            for m in all_matches:
                logging.info(
                    "Processing Start {0} : End {1}".format(*m.span()))

                try:
                    sdn_block = SdnMessage.SdnMessage(m.group(0))
                    if call_ids is not None:
                        if not sdn_block.contains_call_id(*call_ids):
                            logging.info("no call id : skipping.")
                            continue
                    if conf_ids is not None:
                        if not sdn_block.contains_conf_id(*conf_ids):
                            logging.info("no conf id : skipping.")
                            continue

                    outfile.write('\n\n')
                    outfile.write(str(sdn_block))

                    logging.info("Writing to file.")
                except ParseError:
                    logging.warning("Parse Error - Invalid XML")
                    logging.debug(m.group(0).decode("utf-8", "strict"))


def start_logging():
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        filename="last_run.log",
                        filemode="w",
                        level=logging.DEBUG)


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(description="""
        Skype for Business Replay Tool.
        Functionality includes: Extracting SDN messages from log files
        with specific call or conference ids, and cleaning the logs files of
        formatting errors.
        """)
    arg_parser.add_argument("infile",
                            type=str,
                            help="Path to the input file.")
    arg_parser.add_argument("outfile",
                            type=str,
                            help="Path to the output file.")
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

if __name__ == "__main__":
    main()
