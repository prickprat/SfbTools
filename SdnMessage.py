import xml.etree.ElementTree as ET


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
        Returns the TimeStamp string from ConnectionInfo
        """

        timestamp_element = self.root.find("./ConnectionInfo/TimeStamp")
        if (timestamp_element is not None):
            timestamp_str = timestamp_element.text
            print(timestamp_str)
        else:
            return None

    @staticmethod
    def get_timestamp_interval(cls, message1, message2):
        """
        Returns the timestamp difference in milliseconds of message1 and message2.
        Positive if message1 timestamp is greater than message2 timestamp.
        """
        pass
