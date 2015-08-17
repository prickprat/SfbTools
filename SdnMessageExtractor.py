import logging
import argparse
import mmap
import re
import SdnMessage
from xml.etree.ElementTree import ParseError as ParseError


def main():
    start_logging()
    args = parse_sys_args()
    if args.clean_log:

        clean_log_file(args.infile, args.outfile)
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


def clean_log_file(infile_path, outfile_path):
    start_regex = re.compile(
        r'Start_Prognosis_datadump >>>>>>>>>>>>>>>>>>: (.*)',
        re.DOTALL | re.IGNORECASE)
    end_regex = re.compile(
        r'<<<<<<<<<<<<<<<<<< Stop_Prognosis_datadump',
        re.DOTALL | re.IGNORECASE)
    log_split_regex = re.compile(
        r'IRLYNC\s+httpserv\s+\d+\s+T\d+\s+(.*)',
        re.DOTALL | re.IGNORECASE)

    with open(infile_path, mode="rt", errors="strict") as infile:
        with open(outfile_path, mode="wt", errors="strict") as outfile:
            in_sdn_message = False
            for line in infile:
                # Remove the newline, to be added by successive lines
                line = line.rstrip('\n')
                if in_sdn_message:
                    match = end_regex.search(line)
                    if match:
                        logging.debug("Found End of sdn message.")
                        in_sdn_message = False
                        continue
                    # Check for split sdn message dumps
                    match = log_split_regex.search(line)
                    if match:
                        # Join directly on to previous line
                        logging.debug("Found Split log line.")
                        outfile.write(match.group(1))
                        continue
                    # Include all normal sdn lines with a newline prefix
                    outfile.write('\n' + line)
                else:
                    match = start_regex.search(line)
                    if match:
                        in_sdn_message = True
                        logging.debug("Found Start of sdn message.")
                        outfile.write('\n' + match.group(1))
    return


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
