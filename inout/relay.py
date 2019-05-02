# coding: utf-8


"""Module to use a Relay Card with Raspberry Pi.

If not run on a RPi, the behaviour is simulated and there is no real, hardware change such as pin writing.
"""


import time

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    RPI = False
    print("WARNING: not running on a Raspberry Pi. We simulate a relay for the webserver demo.")
else:
    RPI = True


class Relay:
    """Class to define that a specific GPIO pin is a relay.

    Methods to close, open, reverse the relay and to read its state.
    """

    def __init__(self, pin):
        """Initialization function.
        Set the pin as an output, and initialize it to HIGH (open relay)/

        Args:
            pin: The pin number of the relay.
        """

        self._pin = pin

        # Set pin as out
        if RPI:
            GPIO.setup(self._pin, GPIO.OUT)

        self.state = None

        # Initialize as an open relay
        self.open()

    @property
    def pin(self):
        return self._pin

    def close(self):
        self.state = True
        if RPI:
            GPIO.output(self.pin, GPIO.LOW)

    def open(self):
        self.state = False
        if RPI:
            GPIO.output(self.pin, GPIO.HIGH)

    def read(self):
        return self.state

    def reverse(self):
        if self.state:
            self.open()
        else:
            self.close()
