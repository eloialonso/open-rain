# coding: utf-8

import time
import random

import RPi.GPIO as GPIO


"""Module to use a Relay Card with Raspberry Pi"""


class Relay:
    """TODO"""
    def __init__(self, pin):
        """TODO"""
        self._pin = pin
        # Set pin as out
        GPIO.setup(self._pin, GPIO.OUT)
        
        # Initialize as an open relay
        self.open()
        
        # Store state names
        self._state_open = "open"
        self._state_closed = "closed"

    @property
    def pin(self):
        return self._pin

    def close(self):
        GPIO.output(self.pin, GPIO.LOW)

    def open(self):
        GPIO.output(self.pin, GPIO.HIGH)
    
    def read(self):
        return GPIO.input(self.pin) == GPIO.LOW

    def state(self):
        state = GPIO.input(self.pin)
        if state == GPIO.LOW:
            return self._state_closed
        else:
            return self._state_open

    def reverse(self):
        state = self.state()
        if state == self._state_open:
            self.close()
        else:
            self.open()
