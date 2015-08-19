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
        """ Returns true if the Message contains any of the given call Ids. """

        call_id_element = self.root.find("./ConnectionInfo/CallId")
        if (call_id_element is not None and
                call_id_element.text in call_ids):
            return True
        return False

    def contains_conf_id(self, *conference_ids):
        """
        Returns true if the Message contains any of the given conference Ids.
        """

        conference_id_element = self.root.find("./ConnectionInfo/ConferenceId")
        if (conference_id_element is not None and
                conference_id_element.text in conference_ids):
            return True
        return False

    def get_timestamp(self):
        """
        Returns the TimeStamp string from ConnectionInfo
        """

        timestamp_element = self.root.find("./ConnectionInfo/TimeStamp")
        if (timestamp_element is not None):
            return timestamp_element.text
        return None

    # HOW DO YOU DO CLASS FUNCTIONS?
    def calculate_time_difference(message1, message2):
        timestamp_1 = message1.get_timestamp()
        timestamp_2 = message2.get_timestamp()
        # python
