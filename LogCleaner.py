import logging
import re


class LogCleaner:

    start_regex = re.compile(
        r'Start_Prognosis_datadump >>>>>>>>>>>>>>>>>>: (.*)',
        re.DOTALL | re.IGNORECASE)
    end_regex = re.compile(
        r'<<<<<<<<<<<<<<<<<< Stop_Prognosis_datadump',
        re.DOTALL | re.IGNORECASE)
    log_split_regex = re.compile(
        r'IRLYNC\s+httpserv\s+\d+\s+T\d+\s+(.*)',
        re.DOTALL | re.IGNORECASE)

    def __init__(self, in_path, out_path):
        self.in_path = in_path
        self.out_path = out_path

    def clean(self):
        with open(self.in_path, mode="rt", errors="strict") as infile:
            with open(self.out_path, mode="wt", errors="strict") as outfile:
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
                            logging.debug("Found Start of message.")
                            outfile.write('\n' + match.group(1))

    def clean_line(self, line):
        pass
