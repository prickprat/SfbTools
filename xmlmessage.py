import xml.etree.ElementTree as ET
import datetime
import re
import logging
import mmap
import abc


def convert_timestamp(timestamp_str):
    """
    Converts a ISO 8601 timestamp to a datetime object
    with a UTC timezone offset.

    Raises TypeError or ValueError if conversion fails for
    a particular reason.

    Arguments:
    timestamp_str -- ISO 8601 formatted datetime string with time-zone information.
    """
    timestamp_regex = re.compile(
        r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'
        r'T'
        r'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})'
        r'(?P<fractional>\.\d+)?'
        r'((?P<zulu>[zZ])|(?P<z_sign>[+-])(?P<z_hour>\d{2}):(?P<z_minute>\d{2}))')
    try:
        m = re.search(timestamp_regex, timestamp_str)
        if m is None:
            raise ValueError("Timestamp string does not match the ISO-8601 format.")
        # Trim fractional seconds to nearest microsecond
        fractional_seconds = m.group('fractional')
        microseconds = 0
        if fractional_seconds is not None:
            microseconds = int(float(fractional_seconds) * 1e6)
        # Calculate the timezone delta
        tz_delta = datetime.timedelta(0)  # Zulu Time offset
        if m.group('zulu') is None:
            sign = -1 if (m.group('z_sign') == '-') else 1
            tz_delta = sign * datetime.timedelta(hours=int(m.group('z_hour')),
                                                 minutes=int(m.group('z_minute')))

        converted_datetime = datetime.datetime(int(m.group('year')),
                                               int(m.group('month')),
                                               int(m.group('day')),
                                               int(m.group('hour')),
                                               int(m.group('minute')),
                                               int(m.group('second')),
                                               microseconds,
                                               datetime.timezone(tz_delta))
        return converted_datetime
    except TypeError as e:
        logging.error("TypeError raised : " + str(e))
        raise
    except ValueError as e:
        logging.error("ValueError raised : " + str(e))
        raise


class XmlMessage(metaclass=abc.ABCMeta):

    """
    Abstract XML message class
    """

    def __init__(self, root_element):
        """
        Returns and instance of an XML message.

        root    -   root XML element for the XML Message.
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
        except ET.ParseError as e:
            logging.error("Parse Error: " + str(e))
            raise

    @classmethod
    @abc.abstractmethod
    def get_root_tag(cls):
        """
        Returns the tag of the root xml element for this xml wrapper.
        """

    def get_root_regex(self):
        """
        Returns a re.compile object which can be used to
        extract this xml element from text.
        """
        root_tag = self.get_root_tag()
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
            return ET.tostring(self.root, encoding)
        except LookupError as e:
            logging.error("LookupError: " + str(e))
            raise ValueError("Encoding parameter must be either 'us-ascii' or 'unicode'.")


class SdnMessage(XmlMessage):

    @classmethod
    def get_root_tag(cls):
        return "LyncDiagnostics"

    def contains_call_id(self, *call_ids):
        """
        Returns true if the Message contains any of the given call Ids.
        Case-insensitive.
        """
        call_id_element = self.root.find("./ConnectionInfo/CallId")
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
        conference_id_element = self.root.find("./ConnectionInfo/ConferenceId")
        conf_ids_lower = map(lambda x: x.lower(), conf_ids)
        if (conference_id_element is not None and
                conference_id_element.text.lower() in conf_ids_lower):
            return True
        return False

    def get_timestamp(self):
        """
        Returns a datetime instance representing the TimeStamp information
        from the SDN message. Returns None if no TimeStamp element exists or
        Timestamp is incorrectly formatted.s
        """

        timestamp_element = self.root.find("./ConnectionInfo/TimeStamp")
        if (timestamp_element is not None):
            timestamp_str = timestamp_element.text

            try:
                return convert_timestamp(timestamp_str)
            except (ValueError, TypeError):
                return None
        else:
            return None

    def __str__(self):
        desc_template = "<SdnMessage object : Timestamp - {0} : Contains {1}>"
        return desc_template.format(str(self.get_timestamp()),
                                    tuple(x.tag for x in list(self.root)))


class SdnMockerMessage(XmlMessage):

    @classmethod
    def get_root_tag(cls):
        return "SdnMockerConfiguration"

    def todict(self):
        """
        Return a dictionary with keys as configuration options and values
        as the string present in the respective Element. If the element was not present,
        then the value will be None.

        Raises ValueError if element text is invalid / cannot be cast properly.

        The configuration keys can be:
            target_url
            target_ip
            target_port
            max_delay
            realtime
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

        def strip_ip_port(url):
            res = {'ip': None, 'port': None}

            if url is None:
                return res
            m_ip = re.search(r'(?:http|https)://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', url)
            m_port = re.search(r':(\d{1,5})', url)
            if m_ip is not None:
                res['ip'] = m_ip.group(1)
            if m_port is not None:
                res['port'] = m_port.group(1)
            return res

        def convert_url(url):
            """
            Converts to http if https is not supported.
            """
            if url is not None and re.search("^https://", url):
                logging.warning(
                    "'{0}' : HTTPS is not currently supported. Switching to HTTP.".format(url))
                return re.sub("^https://", "http://", url, count=1)
            return url

        target_url = convert_url(self.root.findtext('./TargetUrl'))
        max_delay = self.root.findtext('./MaxDelay')
        real_time = self.root.findtext('./RealTime')

        return {'target_url': target_url,
                'target_ip': strip_ip_port(target_url)['ip'],
                'target_port': strip_ip_port(target_url)['port'],
                'max_delay': str_to_int(max_delay),
                'realtime': str_to_bool(real_time)}

    def __str__(self):
        return "<SdnMockerMessage object : " + str(self.todict()) + ">"


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

        max_delay = self.root.findtext('./MaxDelay')
        real_time = self.root.findtext('./RealTime')

        return {'max_delay': str_to_int(max_delay),
                'realtime': str_to_bool(real_time)}


class SqlQueryMessage(XmlMessage):

    @classmethod
    def get_root_tag(cls):
        return "SqlQuery"

    def get_timestamp(self):
        """
        Returns a datetime instance representing the TimeStamp information
        from the SDN message. Returns None if no TimeStamp element exists or
        Timestamp is incorrectly formatted.
        """

        timestamp_element = self.root.find("./TimeStamp")
        if timestamp_element is not None:
            timestamp_str = timestamp_element.text

            try:
                return convert_timestamp(timestamp_str)
            except (ValueError, TypeError):
                return None
        else:
            return None

    def get_query(self):
        """
        Returns the SQL query as a string.
        """
        query_element = self.root.find("./Query")
        if query_element is not None:
            return query_element.text
        return None

    def __str__(self):
        pass


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

    def open(self):
        self._mmap = mmap.mmap(self._fileno, 0, access=mmap.ACCESS_READ)

    def close(self):
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
                return self._xml_wrapper(match.group(0))
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
