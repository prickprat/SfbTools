import sys
import logging
import argparse
import mmap
import re
import SdnMessage
from xml.etree.ElementTree import ParseError as ParseError

def main():
    start_logging()
    args = parse_sys_args()

    lyncDiagRegex = re.compile(br"<LyncDiagnostics.*?>.*?</LyncDiagnostics>", 
                            re.DOTALL | re.MULTILINE | re.IGNORECASE)

    with open(args.infile, mode="rt", errors="strict") as infile:
        mm_infile = mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ)
        
        with open(args.outfile, mode="wt", errors="strict") as outfile:
            all_matches = lyncDiagRegex.finditer(mm_infile)
            for m in all_matches:
                print("Start {0} : End {1}".format(*m.span()))
                
                try:
                    sdn_block = SdnMessage.SdnMessage(m.group(0))
                    if args.call_ids is not None:
                        if not sdn_block.contains_call_id(*args.call_ids):
                            print("no call id : skipping.")
                            continue
                    if args.conf_ids is not None:
                        if not sdn_block.contains_conference_id(*args.conf_ids):
                            print("no conf id : skipping.")
                            continue

                    outfile.write('\n\n')
                    outfile.write(str(sdn_block))

                    print("Writing to file.")
                except ParseError:
                    print("WARNING : INVALID XML.")

def start_logging():
    pass


def parse_sys_args():
    arg_parser = argparse.ArgumentParser(description="""Skype for Business Replay Tool. 
                                                        Functionality includes extracting SDN xml blocks from log files.""")
    arg_parser.add_argument("infile", 
                            type=str, 
                            help="Relative or absolue path to the input file.")
    arg_parser.add_argument("outfile", 
                            type=str, 
                            help="Relative or absolue path to the output file.")
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

if __name__ == "__main__":
    main()

            







