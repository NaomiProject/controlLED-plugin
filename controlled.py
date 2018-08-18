from jasper import plugin
import serial
import logger

class ControlledPlugin(plugin.SpeechHandlerPlugin):
    def get_phrases(self):
        """
        Keyword list to trigger this module
        """
        return [
            self.gettext("LED"),
            self.gettext("RED"),
            self.gettext("GREEN"),
            self.gettext("ON"),
            self.gettext("OFF"),
            self.gettext('TEMPERATURE')]

    def handle(self, text, mic):
        """
        Once the brain detected the keywords above,
        it trigger this part
        """
        try:
            ser = serial.Serial('/dev/ttyUSB0', 9600)
        else:
            break

        if self.gettext('GREEN').upper() in text.upper():
            if self.gettext('ON').upper() in text.upper():
                ser.write('A') #set the green led on ON
            else:
                ser.write('B') #set the green led on OFF
        elif self.gettext('RED').upper() in text.upper():
            if self.gettext('ON').upper() in text.upper():
                ser.write('C') #set the red led on ON
            else:
                ser.write('D') #set the red led on OFF


    def is_valid(self, text):
        """
        Returns True if the input is related to controlled.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
