from lxml import etree as ET
import re
import logging
import mmap
import abc
import dateutil.parser as DUP
from datetime import timedelta


class XmlMessage(metaclass=abc.ABCMeta):

    """class
    Abstract XML message
    """
    _namespace = {}

    def __init__(self, root_element):
        """
        Returns and instance of an XML message.

        root        -   root XML element for the XML Message.
        default_ns  -   Default Namespace for the root element.
        """
        self._etree = ET.ElementTree(element=root_element)
        self.root = self._etree.getroot()

    @classmethod
    def fromstring(cls, msg_str):
        """
        Parses the xml message as a string.
        Raises ParseError if invalid XML is encountered.
        """
        try:
            return cls(ET.XML(msg_str))
        except ET.XMLSyntaxError as e:
            logging.error("XMLSyntaxError: " + str(e))
            raise

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

    @classmethod
    @abc.abstractmethod
    def get_root_tag(cls):
        """
        Returns the tag of the root xml element for this xml wrapper.
        """

    @classmethod
    def get_root_regex(cls):
        """
        Returns a re.compile object which can be used to
        extract this xml element from text.
        """
        root_tag = cls.get_root_tag()
        rx_str = "<{0}.*?>.*?</{0}>".format(root_tag).encode('utf-8')
        return re.compile(rx_str, re.DOTALL | re.MULTILINE | re.IGNORECASE)

    @abc.abstractmethod
    def __str__(self):
        """Returns a human readable string representation of the XMLMessage."""

    def tostring(self, encoding="us-ascii"):
        """
        Returns a string representation of the xml element.

        Parameters:
        encoding    -   'us-ascii' returns a byte string. [default]
                        'unicode' returns a unicode string.
        """
        try:
            out_str = ET.tostring(self.root, encoding=encoding)
            return re.sub(rb'( xmlns="[^"]+"| xmlns:xsi="[^"]+")', rb'', out_str)
        except LookupError as e:
            logging.error("LookupError: " + str(e))
            raise ValueError("Encoding parameter must be either 'us-ascii' or 'unicode'.")

    @classmethod
    def convert_timestamp(cls, timestamp_str):
        """
        Converts a ISO 8601 timestamp to a datetime object
        with a UTC timezone offset.

        Raises TypeError or ValueError if conversion fails for
        a particular reason.

        Arguments:
        timestamp_str -- ISO 8601 formatted datetime string with time-zone information.
        """
        try:
            timestamp = DUP.parse(timestamp_str)
            if timestamp.utcoffset() is None:
                raise ValueError("Timestamp did not contain UTC offset information.")
            return timestamp
        except (ValueError, TypeError) as e:
            logging.error("{0} raised : {1}".format(e.__class__, str(e)))
            raise ValueError("Timestamp string does not match the ISO-8601 format.")

    @classmethod
    def convert_datetime(cls, timestamp_dt):
        """
        """
        offset = timestamp_dt.utcoffset()
        dt_str = "{:%Y-%m-%dT%H:%M:%S.%f0}".format(timestamp_dt)
        if offset is None or offset == timedelta(0):
            offset_str = 'Z'
        else:
            offset_str = "{:%z}".format()
            offset_str = offset_str[:3] + ':' + offset_str[3:]
        dt_str = dt_str + offset_str
        return dt_str

    @abc.abstractmethod
    def get_timestamp(self):
        """
        Returns the timestamp for the message as a datetime object.
        """

    @abc.abstractmethod
    def set_timestamp(self, timestamp):
        """
        Sets the timestamp in the xml message in ISO 8601 format.

        timestamp   -   Must be a datetime object with a utcoffset/
        """

class SdnMessage(XmlMessage):

    @classmethod
    def get_root_tag(cls):
        return "LyncDiagnostics"

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

    def get_timestamp(self):
        timestamp_element = self.root.find(
            self.qualify_xpath("./ConnectionInfo/TimeStamp"))

        if (timestamp_element is not None):
            timestamp_str = timestamp_element.text
            return self.convert_timestamp(timestamp_str)
        else:
            raise ValueError("TimeStamp Element does not exist in the XML element.")

    def set_timestamp(self, timestamp_dt):
        timestamp_element = self.root.find(
            self.qualify_xpath("./ConnectionInfo/TimeStamp"))

        if timestamp_element is not None:
            timestamp_element.text = self.convert_datetime(timestamp_dt)
        else:
            raise ValueError("TimeStamp Element does not exist in the XML element.")

    def __str__(self):
        desc_template = "<SdnMessage object : Timestamp - {0} : Contains {1}>"
        return desc_template.format(str(self.get_timestamp()),
                                    tuple(x.tag for x in list(self.root)))


class MockerConfiguration(XmlMessage):

    @classmethod
    def get_root_tag(cls):
        return "MockerConfiguration"

    def __str__(self):
        return "<MockerConfiguration object : " + str(self.todict()) + ">"

    def todict(self):
        """
        Return a dictionary with keys as configuration options and values
        as the string present in the respective Element. If the element was not present,
        then the value will be None.

        """
        def str_to_bool(s):
            try:
                return (s.lower() == "true") if s is not None else None
            except ValueError:
                logging.error(
                    "ValueError: String to boolean conversion failed.")
                raise

        def str_to_int(s):
            try:
                return int(s) if s is not None else None
            except ValueError:
                logging.error(
                    "ValueError: String to int conversion failed.")
                raise

        max_delay = self.root.findtext(self.qualify_xpath('./MaxDelay'))
        real_time = self.root.findtext(self.qualify_xpath('./RealTime'))
        current_time = self.root.findtext(self.qualify_xpath('./CurrentTime'))

        return {'max_delay': str_to_int(max_delay),
                'realtime': str_to_bool(real_time),
                'currenttime': str_to_bool(current_time)}

    def get_timestamp(self):
        raise NotImplementedError

    def set_timestamp(self):
        raise NotImplementedError


class SqlQueryMessage(XmlMessage):

    @classmethod
    def get_root_tag(cls):
        return "SqlQueryMessage"

    def get_timestamp(self):
        timestamp_element = self.root.find(
            self.qualify_xpath("./TimeStamp"))

        if (timestamp_element is not None):
            timestamp_str = timestamp_element.text
            return self.convert_timestamp(timestamp_str)
        else:
            raise ValueError("TimeStamp Element does not exist in the XML element.")

    def set_timestamp(self, timestamp_dt):
        timestamp_element = self.root.find(
            self.qualify_xpath("./TimeStamp"))

        if timestamp_element is not None:
            timestamp_element.text = self.convert_datetime(timestamp_dt)
        else:
            raise ValueError("TimeStamp Element does not exist in the XML element.")

    def get_query(self):
        """
        Returns the SQL query as a string.
        """
        query_element = self.root.find(
            self.qualify_xpath("./Query"))
        if query_element is not None:
            return query_element.text
        return None

    def __str__(self):
        desc_template = "<SqlQueryMessage object : Timestamp - {0} : Query {1}>"
        return desc_template.format(str(self.get_timestamp()), str(self.get_query()))


class XMLMessageFactory:

    def __init__(self, file_obj, xml_wrapper):
        """
        root_regex  - re.compiled regex to find the root elements in the xml document.
        file_obj    - input file object.
        xml_wrapper - the xml class that will parse the xml block. Must be a subclass of
                        XmlMessage.
        """
        assert issubclass(xml_wrapper, XmlMessage), "xml_wrapper must be a subclass of XmlMessage."

        self._root_rx = xml_wrapper.get_root_regex()
        self._fileno = file_obj.fileno()
        self._xml_wrapper = xml_wrapper
        self._mmap = None

    def open(self):
        self._mmap = mmap.mmap(self._fileno, 0, access=mmap.ACCESS_READ)

    def close(self):
        if self._mmap is not None:
            self._mmap.close()

    def __del__(self):
        self.close()

    def __iter__(self):
        if self._mmap.closed:
            self.open()
        self._current_pos = 0
        self._mmap.seek(0)
        return self

    def __next__(self):
        if self._mmap.closed:
            raise StopIteration

        match = self._root_rx.search(self._mmap, self._current_pos)
        if match:
            try:
                self._current_pos = match.end()
                return self._xml_wrapper.fromstring(match.group(0))
            except ET.ParseError:
                logging.error("ParseError : Stopping iterator.")
                raise StopIteration
        else:
            logging.debug("No more matches found. Stopping iterator.")
            raise StopIteration

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exec_type, exec_value, exec_tb):
        self.close()
        return False


class MessageFactory:

    @staticmethod
    def createMessage(root_element):
        for cls in MessageFactory.find_all_subclasses(XmlMessage):
            if cls.get_root_tag() == root_element.tag:
                return cls(root_element)
        return None

    @staticmethod
    def find_all_subclasses(arg_cls):
        return arg_cls.__subclasses__() + [x for y in arg_cls.__subclasses__()
                                           for x in MessageFactory.find_all_subclasses(y)]
