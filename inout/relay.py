# coding: utf-8

import time

import RPi.GPIO as GPIO


"""Module to use a Relay Card with Raspberry Pi"""


class Relay:
    """TODO"""
    def __init__(self, pin):
        """TODO"""
        self._pin = pin
        # Set pin as out
        GPIO.setup(self._pin, GPIO.OUT)

        self.state = None

        # Initialize as an open relay
        self.open()

        # Store state names
        self._state_open = "open"
        self._state_closed = "closed"

    @property
    def pin(self):
        return self._pin

    def close(self):
        self.state = True
        GPIO.output(self.pin, GPIO.LOW)

    def open(self):
        self.state = False
        GPIO.output(self.pin, GPIO.HIGH)

    def read(self):
        return self.state
        # return GPIO.input(self.pin) # == GPIO.LOW

    # def state(self):
    #     state = GPIO.input(self.pin)
    #     if state == GPIO.LOW:
    #         return self._state_closed
    #     else:
    #         return self._state_open

    def reverse(self):
        if self.state:
            self.open()
        else:
            self.close()
        # state = self.state()
        # if state == self._state_open:
            # self.close()
        # else:
            # self.open()
