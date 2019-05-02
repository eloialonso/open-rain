# coding: utf-8


"""
Module to use a HC-SR04 ultrasonic sensor with RPi.

If not run on a RPi, the behaviour is simulated and there is no real, hardware change such as pin reading.
"""



import random
import sys
from statistics import median
import time

try:
    import RPi.GPIO as GPIO
except RuntimeError as e:
    RPI = False
    print("WARNING: not running on a Raspberry Pi. We simulate an ultrasonic sensor for the webserver demo.")
else:
    RPI = True


class UltrasonicSensor:
    """Class to define that a specific GPIO pin is an ultrasonic sensor.

    Methods to measure the distance once or get the median on several measures.
    """

    def __init__(self, trig=18, echo=24, temperature=20):
        """Initialization function.
        Set the trigger pin as an output and the echo pin as an input.

        Args:
            trig: The pin number of the trigger pin.
            echo: The pin number of the echo pin.
            temperature: The temperature, to estimate the speed of sound.
        """

        self._trig = trig
        self._echo = echo

        # setup in/out
        if RPI:
            GPIO.setup(self._trig, GPIO.OUT)
            GPIO.setup(self._echo, GPIO.IN)

        # set sound speed
        self._speed = 331.5 + 0.607 * temperature

    @property
    def trig(self):
        return self._trig

    @property
    def echo(self):
        return self._echo

    @property
    def speed(self):
        return self._speed

    def measure(self):
        """Do one measure with the ultrasonic sensor.

        WARNING: if not run on a RPi, this function return a random value for illustration purpose.
        """

        # When not running on a raspberry pi, we just return a random value.
        if not RPI:
            return random.uniform(0, 3)

        # Set Trigger to HIGH for 10 microseconds
        GPIO.output(self.trig, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trig, GPIO.LOW)

        # Wait for the echo pulse
        counter = 0
        while GPIO.input(self.echo) == GPIO.LOW:
            start_time = time.time()
            counter += 1
            if counter > 1000:
                raise SystemError("Echo pulse not received.")

        while GPIO.input(self.echo) == GPIO.HIGH:
            stop_time = time.time()

        # Get time and deduce distance
        time_elapsed = stop_time - start_time       # in seconds
        distance = time_elapsed * self.speed / 2    # in meters

        return distance

    def median_measure(self, rep=11, pause=0.1):
        """Perform several measures and return the median.

        Args:
            rep: Number of measures.
            pause: Time between measures.
        """

        measures = []
        for _ in range(rep):
            # Wait between measures
            # GPIO.output(self.trig, GPIO.LOW)
            time.sleep(pause)

            # Do measure
            value = self.measure()
            measures.append(value)

        # Return the median measure
        return median(measures)


