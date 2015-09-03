import xml.etree.ElementTree as ET
import datetime
import re
import logging
import mmap


class XmlMessage:

    """
    Abstract XML message class
    """

    def __init__(self, message):
        self.root = self.parse_message(message)

    def parse_message(self, message):
        """
        Parses the SDN message.
        Raises ParseError if invalid XML.
        """
        try:
            return ET.XML(message)
        except ET.ParseError as e:
            logging.error("Parse Error: " + str(e))
            raise

    def get_root_regex():
        raise NotImplementedError

    def __str__(self):
        return "<XmlMessage object : Abstract>"

    def totext(self):
        return ET.tostring(self.root, encoding="us-ascii")


class SdnMessage(XmlMessage):

    def __init__(self, message):
        super().__init__(message)

    def get_root_regex():
        return re.compile(br"<LyncDiagnostics.*?>.*?</LyncDiagnostics>",
                          re.DOTALL | re.MULTILINE | re.IGNORECASE)

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
                return SdnMessage.convert_timestamp(timestamp_str)
            except (ValueError, TypeError):
                return None
        else:
            return None

    @staticmethod
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

    def __str__(self):
        desc_template = "<SdnMessage object : Timestamp - {0} : Contains {1}>"
        return desc_template.format(str(self.get_timestamp()),
                                    tuple(x.tag for x in list(self.root)))


class SdnReplayMessage(XmlMessage):

    def __init__(self, message):
        super().__init__(message)

    def get_root_regex():
        return re.compile(br"<SdnReplay.*?>.*?</SdnReplay>",
                          re.DOTALL | re.MULTILINE | re.IGNORECASE)

    def get_target_url(self):
        target_url_elem = self.root.find('./Configuration/TargetUrl')
        if target_url_elem is not None:
            return target_url_elem.text
        else:
            return None

    def get_target_ip(self):
        target_url = self.get_target_url()
        m = re.search(r'(?:http|https)://(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', target_url)
        if m is not None:
            return m.group(1)
        else:
            return None

    def get_target_port(self):
        target_url = self.get_target_url()
        m = re.search(r':(\d{1,5})/?', target_url)
        if m is not None:
            return m.group(1)
        else:
            return None

    def get_max_delay(self):
        max_delay_elem = self.root.find('./Configuration/MaxDelay')
        if max_delay_elem is not None:
            return int(max_delay_elem.text)
        else:
            return None

    def is_realtime(self):
        realtime_elem = self.root.find('./Configuration/RealTime')
        realtime_config = realtime_elem.text.lower()
        if realtime_elem is not None:
            if realtime_config == "true":
                return True
            elif realtime_config == "false":
                return False
        return None

    def todict(self):
        """
        Return a dictionary with keys as configuration options defined in the xml block.
        """
        return {'TargetUrl': self.get_target_url(),
                'TargetIp': self.get_target_ip(),
                'TargetPort': self.get_target_port(),
                'MaxDelay': self.get_max_delay(),
                'RealTime': self.is_realtime()}

    def __str__(self):
        return str(self.todict())


class XMLMessageFactory:

    def __init__(self, file_obj, xml_wrapper):
        """
        root_regex  - re.compiled regex to find the root elements in the xml document.
        file_obj - input file object.
        xml_wrapper   - the xml class that will parse the xml block. Must be a subclass of
                        XmlMessage.
        """
        assert issubclass(xml_wrapper, XmlMessage), "xml_wrapper must be a subclass of XmlMessage."

        self._root_rx = xml_wrapper.get_root_regex()
        self._file_obj = file_obj
        self._xml_wrapper = xml_wrapper

    def open(self):
        self._mmap = mmap.mmap(self._file_obj.fileno(), 0, access=mmap.ACCESS_READ)

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
                print("Parse Error raised. Stopping Iteration and closing Memory map.")
                self.close()
                raise StopIteration
        else:
            raise StopIteration

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exec_type, exec_value, exec_tb):
        self.close()
        return False
