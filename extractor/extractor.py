from lxml import etree as ET
import re
import mmap
import logging


class SdnMessage():

    def __init__(self, msg_str):
        """
        Parses the xml message as a string.
        Raises ParseError if invalid XML is encountered.
        """
        try:
            self.root = ET.XML(msg_str)
        except ET.XMLSyntaxError as e:
            logging.error("XMLSyntaxError: " + str(e))
            raise

    @classmethod
    def get_root_regex(cls):
        """
        Returns a re.compile object which can be used to
        extract this xml element from text.
        """
        rx_str = "<{0}.*?>.*?</{0}>".format("LyncDiagnostics").encode('utf-8')
        return re.compile(rx_str, re.DOTALL | re.MULTILINE | re.IGNORECASE)

    def qualify_xpath(self, x_path):
        # Split the xpath variables
        path_tokens = x_path.split('/')
        # Extract default namespace from xml Element
        default_ns = self.root.nsmap.get(None, '')

        # prefix with default namespace if normal tag
        for i, token in enumerate(path_tokens):
            if (any(x in token for x in (':', '.', '=', '}'))
                    or token == ""):
                continue

            path_tokens[i] = "{{{0}}}{1}".format(default_ns, token)
        return '/'.join(path_tokens)

    def contains_call_id(self, *call_ids):
        """
        Returns true if the Message contains any of the given call Ids.
        Case-insensitive.
        """
        call_id_element = self.root.find(self.qualify_xpath("./ConnectionInfo/CallId"))
        call_ids_lower = map(lambda x: x.lower(), call_ids)
        if (call_id_element is not None and
                call_id_element.text.lower() in call_ids_lower):
            return True
        return False

    def contains_conf_id(self, *conf_ids):
        """
        Returns true if the Message contains any of the given conference Ids.
        Case-insensitive.
        """
        conference_id_element = self.root.find(
            self.qualify_xpath("./ConnectionInfo/ConferenceId"))
        conf_ids_lower = map(lambda x: x.lower(), conf_ids)
        if (conference_id_element is not None and
                conference_id_element.text.lower() in conf_ids_lower):
            return True
        return False

    def tostring(self, encoding="us-ascii"):
        """
        Returns a string representation of the xml element.

        Parameters:
        encoding    -   'us-ascii' returns a byte string. [default]
                        'utf-8' returns a unicode string.
        """
        try:
            out_bytes = ET.tostring(self.root, encoding="us-ascii")
            out_bytes = re.sub(rb'( xmlns="[^"]+"| xmlns:xsi="[^"]+")', rb'', out_bytes)
            return out_bytes.decode(encoding)
        except LookupError as e:
            logging.error("LookupError: " + str(e))
            raise ValueError("Encoding parameter must be either 'us-ascii' or 'unicode'.")


def extract_sdn_messages(infile_path, outfile_path, call_ids, conf_ids):

    with open(infile_path, mode="rt", errors="strict") as infile:
        with open(outfile_path, mode="wt", errors="strict") as outfile:
            with mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ) as mmap_in:
                # with XMLMessageFactory(infile, SdnMessage) as xml_gen:
                logging.info("Attempting to parse Sdn Messages.")
                for match in SdnMessage.get_root_regex().finditer(mmap_in):
                    sdn_msg = SdnMessage(match.group(0))
                    # for sdn_msg in xml_gen:
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
