# coding: utf-8


"""Test."""


import json

import RPi.GPIO as GPIO

from relay.relay import Relay
from sensor.ultrasonic import UltrasonicSensor


def main():
    
    # set pin mode
    GPIO.setmode(GPIO.BCM)

    # Load pin info
    with open("pins.json", "r") as f:
        pins = json.load(f)
    
    # Create ultrasonic sensor
    sensor = UltrasonicSensor(trig=pins["trigger"],
                              echo=pins["echo"],
                              temperature=20)
    
    # Create relays
    relays = [Relay(int(p)) for p in pins["relay"]]

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
        
        r = relays[i - 1]
        # Reverse relay state
        r.reverse()
if __name__ == "__main__":
    
    try:
        main()

    # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("\n\nMeasurement stopped by user.")
    except Exception as e:
        print(e)
    finally:
        print("Cleaning GPIO.")
        GPIO.cleanup()
