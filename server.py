#! /usr/bin/env python
# coding: utf-8


"""TODO"""


import argparse
import concurrent.futures
from getpass import getpass
import json
import logging
import math
import os

import bcrypt
import mysql.connector
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
try:
    import RPi.GPIO as GPIO
except RuntimeError as e:
    raise RuntimeError("{} \n==> Run the file 'server_demo_no_gpio.py' for a demo of the webserver without a Raspberry Pi.".format(e))

from inout.ultrasonic import UltrasonicSensor
from inout.relay import Relay


# Logging setup
logFormatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s'")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)
# Log in server.log
fileHandler = logging.FileHandler("./server.log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
# Log in stdout
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


# A thread pool to be used for password hashing with bcrypt.
executor = concurrent.futures.ThreadPoolExecutor(2)


def parse_args():
    """Command line parser."""
    parser = argparse.ArgumentParser()

    # Server
    server = parser.add_argument_group("Server.")
    server.add_argument("--port", type=int, default=9080,
        help="Port to run the server on (default: 9080)")
    server.add_argument("--cookie_secret", type=str, default="./config/cookie.secret",
        help="Path to the file containing the secret cookie string.")

    # Raspberry
    system = parser.add_argument_group("System.")
    system.add_argument("--pinconfig", type=str, default="./config/pins.json",
        help="Path to the pins configuration file (default: './config/pins.json').")
    system.add_argument("--temperature", type=int, default=20,
        help="Temperaturen in Celsius, to compute sound speed (default: 20°C).")

    # Water container
    db = parser.add_argument_group("Water container.")
    db.add_argument("--height", type=float, default=0.198,
        help="Height of the water container, in meters.")
    db.add_argument("--diameter", type=float, default=0.21,
        help="Diameter of the water container, in meters.")

    # Database
    db = parser.add_argument_group("SQL Database.")
    db.add_argument("--sqlhost", default="127.0.0.1",
        help="Database host (default: 127.0.0.1)."),
    db.add_argument("--sqlport", type=int, default=3306,
        help="Database port.")
    db.add_argument("--sqldb", default="openpluie",
        help="Database name (default: 'openpluie').")
    db.add_argument("--sqluser", default="eloi",
        help="Database user (default: 'eloi').")

    return parser.parse_args()


def load_pin_config(path):
    """Load the pin config file and check it"""
    with open(path, "r") as f:
        pins = json.load(f)
    assert sorted(pins.keys()) == sorted(["relay", "trigger", "echo"])
    return pins


def admin(method):
    """Decorator. Require that the user is logged in as an admin."""
    @tornado.web.authenticated
    def wrapper(self, *args, **kwargs):
        if not self.user_is_admin():
            raise tornado.web.HTTPError(403)("Denied: you are not admin.")
        return method(self, *args, **kwargs)
    return wrapper


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
            logging.warning("\nInterruption from user.")
        except Exception as e:
            logging.critical(e)
        finally:
            logging.info("Cleaning GPIO.")
            GPIO.cleanup()
    return gpio_function


class Application(tornado.web.Application):
    def __init__(self, cookie_secret, sql_config, sensor, relays, water_container):
        """TODO"""
        handlers = [
            (r"/", HomeHandler),
            (r'/ws', WSHandler),
            (r"/auth/create", AuthCreateHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
        ]

        settings = dict(
            page_title="OpenPluie",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret=cookie_secret,
            login_url="/auth/login",
            debug=True,
        )

        super(Application, self).__init__(handlers, **settings)

        # Hardware: ultrasonic sensor and relays
        self.relays = relays
        self.sensor = sensor

        # Water container
        self.water_container = water_container

        # Have one global connection to the database across all handlers
        self.database = mysql.connector.connect(
            host=sql_config["host"],
            port=sql_config["port"],
            database=sql_config["database"],
            user=sql_config["user"],
            password=sql_config["password"]
        )
        self.cursor = self.database.cursor()

    @property
    def relay_state(self):
        return {id: relay.read() for id, relay in self.relays.items()}

    @property
    def sensor_value(self):
        return self.sensor.median_measure()

    @property
    def water_level(self):
        volume = math.pi * (self.water_container["radius"] ** 2) * (self.water_container["height"] - self.sensor_value)
        return "{:.2f}".format(volume * 1000) # liters

class BaseHandler(tornado.web.RequestHandler):
    """TODO"""
    @property
    def cursor(self):
        return self.application.cursor

    @property
    def relay_state(self):
        return self.application.relay_state

    @property
    def sensor_value(self):
        return self.application.sensor_value

    @property
    def water_level(self):
        return self.application.water_level

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id:
            return None
        self.cursor.execute("SELECT * FROM users WHERE id = '{}'".format(int(user_id)))
        return self.cursor.fetchone()

    def any_user_exists(self):
        self.cursor.execute("SELECT * FROM users LIMIT 1")
        return bool(self.cursor.fetchall())

    def user_is_admin(self):
        user = self.get_current_user()
        if user:
            _, username, first_name, last_name, _ = user
            return username == 'admin' and first_name == "Eloi" and last_name == "Alonso"
        return False


class HomeHandler(BaseHandler):
    """TODO"""
    @tornado.web.authenticated # this decorator redirects the user the login_url if he is not authenticated
    def get(self):
        _, username, _, _, _ = self.get_current_user()
        logging.info("[HTTP](MainHandler) {} connected.".format(username))
        self.render("home.html", admin=self.user_is_admin(), relay_state=self.relay_state)


class AuthCreateHandler(BaseHandler):
    """TODO"""
    @admin
    def get(self):
        self.render("create_user.html", admin=self.user_is_admin(), error=None)

    @gen.coroutine
    def post(self):
        hashed_password = yield executor.submit(
            bcrypt.hashpw, tornado.escape.utf8(self.get_argument("password")),
            bcrypt.gensalt())
        hashed_password2 = yield executor.submit(
            bcrypt.hashpw, tornado.escape.utf8(self.get_argument("password2")),
            bcrypt.gensalt())
        username = self.get_argument("username")
        self.cursor.execute("SELECT * FROM users WHERE username = %s", username)
        if bool(self.cursor.fetchall()):
            self.render("create_user.html", error="user already created, please choose another username.")
            return
        if self.get_argument("password") != self.get_argument("password2"):
            self.render("create_user.html", error="Passwords are different.")
            return

        # insert query
        sql = "INSERT INTO users (username, first_name, last_name, hashed_password) VALUES (%s, %s, %s, %s)"
        val = (username, self.get_argument("first_name"), self.get_argument("last_name"), hashed_password)
        self.cursor.execute(sql, val)
        self.database.commit()

        self.redirect(self.get_argument("next", "/"))


class AuthLoginHandler(BaseHandler):
    """TODO"""
    def get(self):
        self.render("login.html", error=None)

    @gen.coroutine
    def post(self):
        self.cursor.execute("SELECT * FROM users WHERE username = '{}'".format(self.get_argument("username")))
        user = self.cursor.fetchone()
        if not user:
            self.render("login.html", error="username not found")
            return
        user_id, _, _, _, true_hash = user
        hashed_password = yield executor.submit(
            bcrypt.hashpw, tornado.escape.utf8(self.get_argument("password")),
            tornado.escape.utf8(true_hash))
        if bytes(true_hash, "utf-8") == hashed_password:
            self.set_secure_cookie("user", str(user_id), expires_days=None)
            self.redirect(self.get_argument("next", "/"))
        else:
            self.render("login.html", error="incorrect password")


class AuthLogoutHandler(BaseHandler):
    """TODO"""
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next", "/"))


class WSHandler(tornado.websocket.WebSocketHandler):
    """Handles web sockets for bidirectional communication between server and client."""
    def open(self):
        user_id = self.get_secure_cookie("user")
        if not user_id:
            return None
        logging.info('[WS] Connection was opened.')

    def on_message(self, message):
        """Function called when the client send a message"""
        logging.info("[WS] Incoming message: {}".format(message))

        # Relay message: open or close
        if message.startswith("slider"):
            id = int(message[6])
            if message.endswith("on"):
                self.application.relays[id].close() # turn on irrigation
            elif message.endswith("off"):
                self.application.relays[id].open()  # turn off irrigation
            else:
                raise tornado.web.HTTPError(404)("Unknown WS message: {}".format(message))
            logging.info('[App] GPIO states : {} '.format(self.application.relay_state))

        # Sensor message
        elif message == "do_measure":
            to_send = {"type": "sensor_measure", "value": self.application.water_level}
            self.write_message(to_send)
            logging.info('[WS] Outgoing message: {}'.format(to_send))

        # Unexpected message
        else:
            raise tornado.web.HTTPError(404)("Unknown WS message: {}".format(message))


    def on_close(self):
        logging.info('[WS] Connection was closed.')


@gpio
def main():

    # Parse command line
    args = parse_args()

    # Cookie secret
    with open(args.cookie_secret, "r") as f:
        cookie_secret = f.read()

    # Load pin config file
    pins = load_pin_config(args.pinconfig)

    # Create ultrasonic sensor
    sensor = UltrasonicSensor(trig=pins["trigger"],
                              echo=pins["echo"],
                              temperature=args.temperature)

    # Create relays
    relays = {}
    for id, pin in pins["relay"].items():
        if pin is None:
            logging.warning("Relay n°{} is not available (according to the pin config file)".format(id))
            continue
        relays[int(id)] = Relay(pin)

    # Water container
    water_container = {
        "height": args.height,
        "radius": args.diameter / 2,
    }

    # Database config
    sql_password = getpass("Database password: ")
    sql_config = {"host": args.sqlhost, "port": args.sqlport, "database": args.sqldb, "user": args.sqluser, "password": sql_password}

    try:
        app = Application(cookie_secret, sql_config, sensor, relays, water_container)
        http_server = tornado.httpserver.HTTPServer(app)
        http_server.listen(args.port)
        main_loop = tornado.ioloop.IOLoop.instance()
        logging.info("Tornado Server started on port {}".format(args.port))
        main_loop.start()

    except KeyboardInterrupt:
        logging.warning("Stopped by user.")

    except Exception as e:
        logging.critical(e)


if __name__ == "__main__":
    main()




