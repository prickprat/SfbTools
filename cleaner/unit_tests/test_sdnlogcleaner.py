import logging
import unittest
import sfbtools.cleaner.cleaner as LC

# Disable non-critical logging for Testing
logging.disable(logging.CRITICAL)


class TestLogCleaner(unittest.TestCase):

    def test_clean_line_inside(self):
        in_inside_message = True

        # Non ending message
        in_line = "Hello"
        expected_line = "\nHello"
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertTrue(out_inside_message, "Should still be inside the message.")
        self.assertEqual(expected_line, out_line, "Should only prepend with newline.")

        # Another non ending message
        in_line = "Hel'<<<<<<<<<<<<<<<<<<lo<Dont><Delete></Delete><Stop></Stop></Dont>"
        expected_line = "\nHel'<<<<<<<<<<<<<<<<<<lo<Dont><Delete></Delete><Stop></Stop></Dont>"
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertTrue(out_inside_message, "Should still be inside the message.")
        self.assertEqual(expected_line, out_line, "Should only prepend with newline.")

        # rightstrip test
        in_line = "\nHello. \n"
        expected_line = "\n\nHello. "
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertTrue(out_inside_message, "Should still be inside the message.")
        self.assertEqual(expected_line, out_line, "Should prepend newline and right strip newline.")

        # rightstrip test 2
        in_line = "\nHello.\n"
        expected_line = "\n\nHello"
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertTrue(out_inside_message, "Should still be inside the message.")
        self.assertEqual(expected_line, out_line, "Should prepend newline and right strip newline.")

        # End of log message
        in_line = "Hello.<<<<<<<<<<<<<<<<<< Stop_Prognosis_datadump"
        expected_line = ""
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertFalse(out_inside_message, "Should be outside of message.")
        self.assertEqual(expected_line, out_line, "Should be an empty string.")

        # Split logs case 1
        in_line = "04/08/2015 09:27:54 IRLYNC   httpserv 000000036 T3800              nMOS>"
        expected_line = "nMOS>"
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertTrue(out_inside_message, "Should be inside of message.")
        self.assertEqual(expected_line, out_line, "Should be end portion of split with no space.")

        # Split logs case 2
        in_line = "04/08/2015 09:27:54 IRLYNC   httpserv 000000036 T3800 "
        expected_line = ""
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertTrue(out_inside_message, "Should be inside of message.")
        self.assertEqual(expected_line, out_line, "Should be empty string.")

    def test_clean_line_outside(self):
        in_inside_message = False

        # Non starting message
        in_line = "Hello."
        expected_line = ""
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertFalse(out_inside_message, "Should still be outside the message.")
        self.assertEqual(expected_line, out_line, "Should be an empty string.")

        # Found starting message
        in_line = "Start_Prognosis_datadump >>>>>>>>>>>>>>>>>>: Hello"
        expected_line = "\nHello"
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertTrue(out_inside_message, "Should be inside the message.")
        self.assertEqual(expected_line, out_line, "Should be the end portion of the start.")

        # Found starting message
        in_line = "Start_Prognosis_datadump >>>>>>>>>>>>>>>>>>: "
        expected_line = "\n"
        out_inside_message, out_line = LC.clean_line(in_line, in_inside_message)
        self.assertTrue(out_inside_message, "Should be inside the message.")
        self.assertEqual(expected_line, out_line, "Should be just the newline.")
