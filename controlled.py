import serial
from naomi import plugin


warning_msg = ""


class SimulatedSerial(object):
    @staticmethod
    def write(binary):
        print("Simulation mode: {}".format(warning_msg))
        print("I would have sent: {}".format(binary))


class ControlLEDPlugin(plugin.SpeechHandlerPlugin):
    LED = [0, 0]
    GREEN = 0
    RED = 1
    ON = 1
    OFF = 0
    _SER = None

    # I seem to have to open the serial port in the init method
    # because it never seems to work right directly after opening.
    # If I give it a second, it seems to work better.
    def __init__(self, *args, **kwargs):
        global warning_msg
        super(ControlLEDPlugin, self).__init__(*args, **kwargs)
        try:
            # Buster seems to see an arduino as an ACM device, not
            # a USB device.
            # There are a lot of things that can go wrong here, including
            # having something else (like a 3D printer or something)
            # already using the ttyACM0 device, in which case it might be
            # ttyACM1
            # This should probably be a property that the user can set in
            # the profile.yml
            self._SER = serial.Serial(
                port='/dev/ttyACM0',
                baudrate=9600,
                timeout=0
            )
        except serial.serialutil.SerialException as e:
            warning_msg = e.args[1]
            try:
                self._SER = serial.Serial(
                    port='/dev/ttyUSB0',
                    baudrate=9600,
                    timeout=0
                )
                print("Reading: {}".format(self._SER.read_until()))
            except Exception as e:
                warning_msg = e.args[1]
                self._SER = SimulatedSerial()
        if not self._SER:
            raise serial.serialutil.SerialException(warning_msg)

    # AJC 2019 - I am leaving these phrases as is for the moment, so
    # this plugin will be compatible with both Naomi 2.2 and Naomi 3.0+
    def get_phrases(self):
        """
        Keyword list to trigger this module
        """
        return [
            self.gettext("LED"),
            self.gettext("RED"),
            self.gettext("GREEN"),
            self.gettext("ON"),
            self.gettext("OFF")
        ]
    
    def intents(self):
        return {
            'LEDIntent': {
                'locale': {
                    'en-US': {
                        'keywords': {
                            'LEDThingKeyword': [
                                'ELLEEDEE',
                                'LIGHT'
                            ],
                            'LEDColorKeyword': [
                                'RED',
                                'GREEN'
                            ],
                            'LEDOperationKeyword': [
                                'ON',
                                'OFF'
                            ]
                        },
                        'templates': [
                            "TURN THE {LEDColorKeyword} {LEDThingKeyword} {LEDOperationKeyword}",
                            "TURN {LEDOperationKeyword} THE {LEDColorKeyword} {LEDThingKeyword}"
                        ]
                    },
                    'fr-FR': {
                        'keywords': {
                            'LEDThingKeyword': [
                                'ELLEEDEE',
                                'LUMIERE'
                            ],
                            'LEDColorKeyword': [
                                'ROUGE',
                                'VERTE'
                            ],
                            'LEDOperationKeyword': [
                                'ALLUME',
                                'ETEINT'
                            ]
                        },
                        'templates': [
                            "{LEDOperationKeyword} LA {LEDThingKeyword} {LEDColorKeyword}"
                        ]
                    }
                },
                'action': self.handle
            }
        }

    def switch(self, COLOR, ACTION):
        # Set a default warning message in case something
        # goes wrong but we are unable to extract an error message
        warning_msg = "An unknown error has occurred"
        # if the serial connection goes out of scope, then the arduino
        # seems to reset
        if self._SER:
            cmd = bytes([65 + (COLOR * 2) + (1 - ACTION)])
            self._SER.write(cmd)
            self.LED[COLOR] = ACTION

    def handle(self, intent, mic):
        """
        Once the brain detected the keywords above,
        it trigger this part
        """
        COLOR = None
        ACTION = None
        if(isinstance(intent, dict)):
            # Naomi 3.0+
            text = intent['input']
            try:
                COLORS = intent['matches']['LEDColorKeyword']
            except KeyError:
                COLORS = None
            try:
                ACTION = intent['matches']['LEDOperationKeyword'][0]
            except KeyError:
                ACTION = None
        else:
            # Naomi 2.2-
            text = intent
            COLORS = []
            if self.gettext('GREEN').upper() in text.upper():
                COLORS.append('GREEN')
            if self.gettext('RED').upper() in text.upper():
                COLORS.append('RED')
            if self.gettext('ON').upper() in text.upper():
                ACTION = "ON"
            if self.gettext('OFF').upper() in text.upper():
                ACTION = "OFF"
        try:
            if COLORS:
                for COLOR in COLORS:
                    if COLOR == 'GREEN':
                        if ACTION == "ON" or(ACTION == "" and self.GREEN == self.OFF):
                            # Turn green on
                            self.switch(self.GREEN, self.ON)
                        else:
                            self.switch(self.GREEN, self.OFF)
                    elif COLOR == 'RED':
                        if ACTION == "ON" or(ACTION == "" and self.RED == self.OFF):
                            # Turn red on
                            self.switch(self.RED, self.ON)
                        else:
                            self.switch(self.RED, self.OFF)
            else:
                if ACTION == "ON":
                    self.switch(self.GREEN, self.ON)
                    self.switch(self.RED, self.ON)
                elif ACTION == "OFF":
                    self.switch(self.GREEN, self.OFF)
                    self.switch(self.RED, self.OFF)
                else:
                    self.switch(self.GREEN, self.LED[1 - self.GREEN])
                    self.switch(self.RED, self.LED[1 - self.RED])
        except serial.serialutil.SerialException as e:
            self._logger.warn(e.args[0])

    # Is valid is only used by Naomi 2.2 and below. For Naomi 3.0+
    # it is ignored.
    def is_valid(self, text):
        """
        Returns True if the input is related to controlled.

        Arguments:
        text -- user-input, typically transcribed speech
        """
        return any(p.lower() in text.lower() for p in self.get_phrases())
