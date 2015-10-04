import re
import logging
import logging.config
import logging_conf
import argparse


START_RX = re.compile(r'Start_Prognosis_datadump >>>>>>>>>>>>>>>>>>: (.*)',
                      re.DOTALL | re.IGNORECASE)
END_RX = re.compile(r'<<<<<<<<<<<<<<<<<< Stop_Prognosis_datadump',
                    re.DOTALL | re.IGNORECASE)
SPLIT_RX = re.compile(r'IRLYNC\s+httpserv\s+\d+\s+T\d+\s+(.*)',
                      re.DOTALL | re.IGNORECASE)


def main():
    args = parse_sys_args()
    clean(args.infile, args.outfile)


def clean(in_path, out_path):
    with open(in_path, mode="rt", errors="strict") as infile:
        with open(out_path, mode="wt", errors="strict") as outfile:
            in_sdn_msg = False
            logging.info("Attempting to clean log file.")
            for line_no, line in enumerate(infile, start=1):
                in_sdn_msg, cleaned_line = clean_line(line, in_sdn_msg, line_no)
                outfile.write(cleaned_line)
            logging.info("Log file successfully cleaned.")


def clean_line(line, inside_message, line_no=None):
    """
    Helper method to parse and clean a IRLYNC Log file (for SDN messages).

    Removes newlines and the '.' character from the end of the line.
    Automatically deals with split-log issues.

    Arugments:
    line            - Input line to clean
    inside_message  - Current state of parse before cleaning. Boolean
    line_no         - optional argument for debugging.

    Returns: tuple (inside_message, cleaned_line)
    inside_message  - New state of parser (either inside sdn message or not). Boolean
    cleaned_line    - resulting line from the clean.

    """
    line = line.rstrip('\n')
    # Strip offending period artefacts
    if line[-1] == '.':
        line = line[:-1]

    if inside_message:
        match = END_RX.search(line)
        if match:
            logging.debug("Found 'Stop datadump' marker at line {0}.".format(line_no))
            return (False, '')
        # Check for split sdn message dumps
        match = SPLIT_RX.search(line)
        if match:
            # Should join directly on to previous line with no whitespace
            logging.debug("Found 'Split logs' marker at line {0}.".format(line_no))
            return (True, match.group(1))
        # Include all normal sdn lines with a newline prefix
        return (True, '\n' + line)
    else:
        match = START_RX.search(line)
        if match:
            logging.debug("Found 'Start datadump' marker at line {0}.".format(line_no))
            return (True, '\n' + match.group(1))
        # Ignore non-starting line outside of message
        return (False, '')


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
