import xml.etree.ElementTree as ET

class SdnMessage:
    def __init__(self, message):
        self.root = self.parse_message(message)

    def __str__(self):
        return ET.tostring(self.root, encoding="unicode")

    def parse_message(self, message):
        return ET.XML(message)

    def contains_call_id(self, *call_ids):
        """ Retruns true if the Message contains any of the given call Ids. """
        
        call_id_element = self.root.find("./ConnectionInfo/CallId")
        if call_id_element is not None and call_id_element.text in call_ids:
            return True
        return False

    def contains_conference_id(self, *conference_ids):
        """ Returns true if the Message contains any of the given conference Ids. """
        
        conference_id_element = self.root.find("./ConnectionInfo/ConferenceId")
        if conference_id_element is not None and conference_id_element.text in conference_ids:
            return True
        return False



