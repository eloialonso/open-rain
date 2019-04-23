# coding: utf-8


"""Module to use a Relay Card with Raspberry Pi"""


import time

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    RPI = False
    print("WARNING: not running on a Raspberry Pi. We simulate a relay for the webserver demo.")
else:
    RPI = True


class Relay:
    """TODO"""
    def __init__(self, pin):
        """TODO"""
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
