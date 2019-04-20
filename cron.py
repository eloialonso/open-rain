#! /usr/bin/env python
# coding: utf-8


"""
Script to water the plants. To be run periodically with cron.
"""


import argparse
import json
import logging as log
import math
import os
import time

import RPi.GPIO as GPIO

from inout.ultrasonic import UltrasonicSensor
from inout.relay import Relay


# Define log file
CODE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(CODE_DIR, "cron.log")
log.basicConfig(filename=LOG_FILE, format='%(asctime)s %(message)s', level=log.INFO)


def parse_args():
    """Command line parser."""
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Raspberry
    rpi = parser.add_argument_group("Raspberry.")
    rpi.add_argument("--pinconfig", type=str, default=os.path.join(CODE_DIR, "config", "pins.json"),
        help="Path to the pins configuration file.")
    rpi.add_argument("--temperature", type=int, default=20,
        help="Temperaturen in Celsius, to compute sound speed.")
    rpi.add_argument("--valve_relay", type=int, choices=[1, 2, 3, 4, 5, 6, 7, 8], default=1,
        help="Relay of the electrovalve.")

    # Water container
    container = parser.add_argument_group("Water container.")
    container.add_argument("--height", type=float, default=3,
        help="Height of the water container, in meters.")
    container.add_argument("--diameter", type=float, default=1,
        help="Diameter of the water container, in meters.")

    # Plant watering
    water = parser.add_argument_group("Plants watering.")
    water.add_argument("--liters", type=float, default=5,
        help="Number of liters to spread.")

    # Security
    security = parser.add_argument_group("Security limits.")
    security.add_argument("--min_volume", type=float, default=350,
        help="Minimum number of liters to allow to spread water.")
    security.add_argument("--rain_volume", type=float, default=250,
        help="Volume added to detect a rain fall.")
    security.add_argument("--time_limit", type=float, default=2700,
        help="Watering time limit, for security, in seconds.")

    return parser.parse_args()


def load_pin_config(path):
    """Load the pin config file and check it."""
    with open(path, "r") as f:
        pins = json.load(f)
    assert sorted(pins.keys()) == sorted(["relay", "trigger", "echo"])
    return pins


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
            log.warning("Interruption from user.")
        except Exception as e:
            log.critical(e)
        finally:
            log.info("Cleaning GPIO.")
            GPIO.cleanup()
    return gpio_function


def water_level(water_container, sensor_value):
    """Computes volume based on sensor mesure and geometry of the water container.
    
    Args:
        water_container: Dictionary containing the geometry of the container (height, diameter) in meters.
        sensor_value: Measurement in meters.
    Returns:
        The remaining volume in the container in liters.
    """
    volume = math.pi * (water_container["radius"] ** 2) * (water_container["height"] - sensor_value)
    return volume * 1000 # liters


@gpio
def main():
    """Main function to water plants."""
    
    # Log a new line for readability
    log.info("\n\n### New call ###\n")

    # Parse command line
    args = parse_args()

    # Load pin config file
    pins = load_pin_config(args.pinconfig)

    # Initialize ultrasonic sensor
    sensor = UltrasonicSensor(trig=pins["trigger"],
                              echo=pins["echo"],
                              temperature=args.temperature)

    # Initialize relays
    relays = {}
    for id, pin in pins["relay"].items():
        if pin is None:
            log.debug("Relay n°{} is not available (according to the pin config file)".format(id))
            relays[int(id)] = None
            continue
        relays[int(id)] = Relay(pin)
    
    # The valve is a specific relay
    valve = relays[args.valve_relay]

    # Water container geometry (height and diameter)
    water_container = {
        "height": args.height,
        "radius": args.diameter / 2,
    }

    # Measure the intial water level
    measure = sensor.median_measure(rep=101)            # Do measure
    volume = water_level(water_container, measure)      # Convert it in a volume in liters

    # Load the last volume logged
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
    last_volume = None
    for line in lines[::-1]:
        if "[VOLUME]" in line:
            last_volume = float(line.split("[VOLUME] ")[-1].split(" L")[0])
            log.info("[WATERING] Last volume: {:.2f} L".format(last_volume))
            break
    else:
        log.debug("[WATERING] No water volume measured yet.")

    # Log the new volume
    log.info("[VOLUME] {:.2f} L / {:.4f} cm (before watering)".format(volume, measure))

    # If not enough water in the container, do nothing
    if volume < args.min_volume:
        log.warning("[SECURITY] Not enough water: {:.2f} L. No watering.".format(volume))
        return

    # If it rained, do nothing
    if last_volume is not None and volume - last_volume > args.rain_volume:
        log.warning("[SECURITY] It rained {:.2f} L. No watering.".format(volume - last_volume))
        return

    # Water the plants, with a time limit for security.
    counter_stop = 0
    start_time = time.time()
    log.info("[WATERING] Starting.")
    valve.close()
    while counter_stop < 3:
        time.sleep(10)
        new_measure = sensor.median_measure(rep=21)             # Do measure
        new_volume = water_level(water_container, new_measure)  # Convert it in a volume in liters
        
        # Check that the desired volume is reached 
        if volume - new_volume > args.liters:
            counter_stop += 1
        else:
            counter_stop = 0
        
        # Time limit to prevent from accidentally emptying the container
        if time.time() - start_time > args.time_limit:
            log.warning("[SECURITY] Time limit reached, stopping watering.")
            break

        log.info("[VOLUME] {:.2f} L / {:.4f} cm (while watering).".format(new_volume, new_measure))
    
    # Stop watering.
    valve.open()
    log.info("[WATERING] Stopping. {:.2f} L used. Watered during {} seconds.".format(volume - new_volume, time.time() - start_time))
    log.info("[VOLUME] {:.2f} L / {:.4f} cm (after watering).".format(new_volume, new_measure))
    

if __name__ == "__main__":
    main()





