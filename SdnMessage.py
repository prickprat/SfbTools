import xml.etree.ElementTree as ET
import datetime
import re


class SdnMessage:

    def __init__(self, message):
        self.root = self.parse_message(message)

    def __str__(self):
        return ET.tostring(self.root, encoding="unicode")

    def parse_message(self, message):
        """
        Attempts to parse the message in its original form.
        If this fails, it attempts to repair the message to a valid
        XML format. If this fails, then it throws a parse error.
        """
        return ET.XML(message)

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
        Returns a datetime object representing the TimeStamp information
        from the SDN message. Returns None if no TimeStamp element exists or
        Timestamp is incorrectly formatted.
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
        with a UTC timezone offset. Returns None if conversion
        is not possible.

        Arguments:
        timestamp_str -- ISO 8601 formatted datetime string with time-zone information.
        """
        timestamp_regex = re.compile(
            r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})'
            r'T'
            r'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})'
            r'(?P<fractional>\.\d+)?'
            r'((?P<zulu>[zZ])|(?P<z_sign>[+-])(?P<z_hour>\d{2}):(?P<z_minute>\d{2}))')
        m = re.search(timestamp_regex, timestamp_str)
        if m is None:
            return None

        try:
            # Trim fractional seconds to nearest microsecond
            fractional_seconds = m.group('fractional')
            if fractional_seconds is not None:
                microseconds = int(float(fractional_seconds) * 1e6)
            else:
                microseconds = 0
            # Calculate the timezone delta
            if m.group('zulu') is not None:
                tz_delta = datetime.timedelta(0)
            else:
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
        except (TypeError, ValueError):
            return None

    @staticmethod
    def get_timestamp_interval(message1, message2):
        """
        Returns the timestamp difference in milliseconds of message1 and message2.
        Positive if message1 timestamp is greater than message2 timestamp.
        """
        pass
