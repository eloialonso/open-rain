# coding: utf-8


"""Test."""


import argparse
import json

import RPi.GPIO as GPIO

from relay.relay import Relay
from sensor.ultrasonic import UltrasonicSensor


def parse_args():
    """Command line parser"""
    parser = argparse.ArgumentParser()

    parser.add_argument("--pins", type=str, default="./config/pins.json",
            help="Path to the pin config file (default: './config/pins.json')")

    return parser.parse_args()


def gpio(function):
    """Decorator.
    
    - Set mode to GPIO.BCM
    - Call GPIO.cleanup if an exception is raised (or if ctrl+c)
    """
    
    def gpio_function():
        GPIO.setmode(GPIO.BCM)
        try:
            function()
        except KeyboardInterrupt:
            print("\nInterruption from user.")
        except Exception as e:
            print(e)
        finally:
            print("Cleaning GPIO.")
            GPIO.cleanup()
    
    return gpio_function


@gpio
def main():
    
    # Parse command line
    args = parse_args()

    # set pin mode
    # GPIO.setmode(GPIO.BCM)

    # Load pin info
    with open(args.pins, "r") as f:
        pins = json.load(f)
    
    # Create ultrasonic sensor
    sensor = UltrasonicSensor(trig=pins["trigger"],
                              echo=pins["echo"],
                              temperature=20)
    
    # Create relays
    relays = {}
    for id, pin in pins["relay"].items():
        if pin is None:
            print("Relay {} is not available (according to 'pins.json')".format(id))
            relays[int(id)] = None
            continue
        relays[int(id)] = Relay(pin)
    
    while True:
        
        # Read input from user
        i = input("Press 'm' to measure, or any number between 1 and 8 to change a relay state (ctrl + c to stop): ").lower()
        
        # Measurement
        if i == 'm':
            dist = sensor.median_measure() * 100
            print("\nMeasured Distance = %.1f cm" % dist)
            continue

        # Relay
        try:
            i = int(i)
            if i < 1 or i > 8:
                print("Number out of range: {}".format(i))
                continue
        except:
            print("Invalid input: {}".format(i))
            continue
        
        r = relays[i]
        if r is None:
            print("Relay {} is unavailable".format(i))
            continue

        # Reverse relay state
        r.reverse()


if __name__ == "__main__":
    
    main()
    #try:
    #    main()
    # Reset by pressing CTRL + C
    #except KeyboardInterrupt:
    #    print("\n\nMeasurement stopped by user.")
    #except Exception as e:
    #    print(e)
    #finally:
    #    print("Cleaning GPIO.")
    #    GPIO.cleanup()
