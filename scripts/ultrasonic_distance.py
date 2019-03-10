#! /usr/bin/env python
# coding: utf-8


"""
Script to test ultrasonic sensor with RPi.
"""


import time
from statistics import median

import RPi.GPIO as GPIO


class UltrasonicSensor:
    """TODO"""
    def __init__(self, trig=18, echo=24, temperature=20):
        """TODO"""

        self._trig = trig
        self._echo = echo
        
        # setup in/out
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
        """TODO"""

        # set Trigger to HIGH for 10 microseconds
        GPIO.output(self.trig, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trig, GPIO.LOW)
        
        counter = 0
        while GPIO.input(self.echo) == GPIO.LOW:
            start_time = time.time()                 
            counter += 1
            if counter > 1000:
                raise SystemError("Echo pulse not received.")
        
        while GPIO.input(self.echo) == GPIO.HIGH:
            stop_time = time.time()
        
        # get time and deduce distance
        time_elapsed = stop_time - start_time       # in seconds
        distance = time_elapsed * self.speed / 2    # in meters

        return distance

    def median_measure(self, rep=11, pause=0.1):
        """TODO"""
        measures = []
        for _ in range(rep):
            # Wait between measures
            GPIO.output(self.trig, GPIO.LOW)
            time.sleep(pause)

            # Do measure
            value = self.measure()
            measures.append(value)

        # Return the median measure
        return median(measures)


def main():
    """TODO"""
    # Set pin indexing mode
    GPIO.setmode(GPIO.BCM)

    sensor = UltrasonicSensor()

    try:
        while True:
            dist = sensor.median_measure() * 100
            print("Measured Distance = %.1f cm" % dist)
            time.sleep(5)
                                                     
    # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
    except:
        print("Other error")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()

