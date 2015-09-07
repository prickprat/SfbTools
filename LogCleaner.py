import re
import logging


class LogCleaner:

    def __init__(self, in_path, out_path):
        self.in_path = in_path
        self.out_path = out_path
        self.start_rx = re.compile(r'Start_Prognosis_datadump >>>>>>>>>>>>>>>>>>: (.*)',
                                   re.DOTALL | re.IGNORECASE)
        self.end_rx = re.compile(r'<<<<<<<<<<<<<<<<<< Stop_Prognosis_datadump',
                                 re.DOTALL | re.IGNORECASE)
        self.split_rx = re.compile(r'IRLYNC\s+httpserv\s+\d+\s+T\d+\s+(.*)',
                                   re.DOTALL | re.IGNORECASE)

    def clean(self):
        with open(self.in_path, mode="rt", errors="strict") as infile:
            with open(self.out_path, mode="wt", errors="strict") as outfile:
                in_sdn_msg = False
                for line_no, line in enumerate(infile, start=1):
                    in_sdn_msg, cleaned_line = self.clean_line(line, in_sdn_msg, line_no)
                    outfile.write(cleaned_line)

    def clean_line(self, line, inside_message, line_no=None):
        """
        Helper method to parse and clean a IRLYNC Log file (for SDN messages).
        Automatically right strips for newlines and deals with split-log issues.

        Arugments:
        line            - Input line to clean
        inside_message  - Current state of parse before cleaning.
        line_no         - optional argument for debugging.

        Returns: tuple (inside_message, cleaned_line)
        inside_message  - New state of parser (either inside sdn message or not).
        cleaned_line    - resulting line from the clean.

        """
        line = line.rstrip('\n')

        if inside_message:
            match = self.end_rx.search(line)
            if match:
                logging.debug("Found 'Stop datadump' marker at line {0}.".format(line_no))
                return (False, '')
            # Check for split sdn message dumps
            match = self.split_rx.search(line)
            if match:
                # Should join directly on to previous line with no whitespace
                logging.debug("Found 'Split logs' marker at line {0}.".format(line_no))
                return (True, match.group(1))
            # Include all normal sdn lines with a newline prefix
            return (True, '\n' + line)
        else:
            match = self.start_rx.search(line)
            if match:
                logging.debug("Found 'Start datadump' marker at line {0}.".format(line_no))
                return (True, '\n' + match.group(1))
            # Ignore non-starting line outside of message
            return (False, '')
