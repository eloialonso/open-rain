"""
Script to run periodically with cron.
"""

#! /usr/bin/env python
# coding: utf-8


"""TODO"""


import argparse
import json
import logging as log
import os

import bcrypt
import mysql.connector
import RPi.GPIO as GPIO
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen

from sensor.ultrasonic import UltrasonicSensor
from relay.relay import Relay


# Define log file
log.basicConfig(filename='server.log', format='%(asctime)s %(message)s', level=log.DEBUG)


def parse_args():
    """Command line parser."""
    parser = argparse.ArgumentParser()

    # Server
    server = parser.add_argument_group("Server.")
    server.add_argument("--port", type=int, default=9080,
        help="Port to run the server on (default: 9080)")

    # Raspberry
    rpi = parser.add_argument_group("Raspberry.")
    rpi.add_argument("--pinconfig", type=str, default="./config/pins.json",
        help="Path to the pins configuration file (default: './config/pins.json').")
    rpi.add_argument("--temperature", type=int, default=20,
        help="Temperaturen in Celsius, to compute sound speed (default: 20°C).")

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
    db.add_argument("--sqlpwd", required=True, type=str,
        help="Database password.")

    return parser.parse_args()


def load_pin_config(path):
    """Load the pin config file and check it"""
    with open(path, "r") as f:
        pins = json.load(f)
    assert sorted(pins.keys()) == sorted(["relay", "trigger", "echo"])
    return pins


def admin(method):
    """Decorator.
    Require that the user is logged in as an admin."""
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
            log.warning("\nInterruption from user.")
        except Exception as e:
            log.critical(e)
        finally:
            log.info("Cleaning GPIO.")
            GPIO.cleanup()
    return gpio_function


class Application(tornado.web.Application):
    def __init__(self, sql_config, sensor, relays):
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
            cookie_secret="iuev1456yih5678kvje78on", # TODO warning here
            login_url="/auth/login",
            debug=True,
        )

        super(Application, self).__init__(handlers, **settings)

        # Hardware: ultrasonic sensor and relays
        self.relays = relays
        self.sensor = sensor

        # Have one global connection to the database across all handlers
        self.database = mysql.connector.connect(
            host=sql_config["host"],
            port=sql_config["port"],
            database=sql_config["database"],
            user=sql_config["user"],
            password=sql_config["password"]
        )
        self.cursor = self.database.cursor()

        # manage gpio state TODO wtf ??
        self.relay_state = {id: relay.read() for id, relay in relays.items()}


class BaseHandler(tornado.web.RequestHandler):
    """TODO"""
    @property
    def cursor(self):
        return self.application.cursor

    @property
    def relay_state(self):
        return self.application.relay_state

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id:
            return None
        self.cursor.execute("SELECT * FROM users WHERE id = '{}'".format(int(user_id)))
        return self.cursor.fetchone()
        # return self.db.get("SELECT * FROM users WHERE id = %s", int(user_id))

    def any_user_exists(self):
        self.cursor.execute("SELECT * FROM users LIMIT 1")
        return bool(self.cursor.fetchall())
        # return bool(self.db.get("SELECT * FROM users LIMIT 1"))

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
        log.info("[HTTP](MainHandler) {} connected.".format(username))
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
        # if bool(self.db.get("SELECT * FROM users WHERE username = %s", username)):
        self.cursor.execute("SELECT * FROM users WHERE username = %s", username)
        if bool(self.cursor.fetchall()):
            # raise tornado.web.HTTPError(400, "user already created, please choose another username.")
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
        # user = self.db.get("SELECT * FROM users WHERE username = %s", self.get_argument("username"))
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
    """ handles web sockets """
    def open(self):
        user_id = self.get_secure_cookie("user")
        if not user_id:
            return None
        log.info('[WS] Connection was opened.')

    def on_message(self, message):
        log.info('[WS] Incoming message: {}'.format(message))
        if message.startswith("slider"):
            id = int(message[6])
            if message.endswith("on"):
                self.application.relays[id].close()
                self.application.relay_state[id] = True
            elif message.endswith("off"):
                self.application.relays[id].open()
                self.application.relay_state[id] = False
            else:
                raise tornado.web.HTTPError(404)("Unknown WS message.")
        #if message == "slider1_on":
        log.info('[App] GPIO states : {} '.format(self.application.relay_state))
        #    self.application.relays[1].close()
        #    self.application.relay_state[1] = True
        #elif message == "slider1_off":
        #    self.application.relays[1].open()
        #    self.application.relay_state[1] = False
        #elif message == "slider2_on":
        #    self.application.relays[2].close()
        #    self.application.relay_state[2] = True
        #elif message == "slider2_off":
        #    self.application.relays[2].open()
        #    self.application.relay_state[2] = False
        #else:

    def on_close(self):
        log.info('[WS] Connection was closed.')


@gpio
def main():

    # Parse command line
    args = parse_args()

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
            log.warning("Relay n°{} is not available (according to the pin config file)".format(id))
            relays[int(id)] = None
            continue
        relays[int(id)] = Relay(pin)

    # Database config
    sql_config = {"host": args.sqlhost, "port": args.sqlport, "database": args.sqldb, "user": args.sqluser, "password": args.sqlpwd}

    try:
        # tornado.options.parse_command_line()
        app = Application(sql_config, sensor, relays)
        http_server = tornado.httpserver.HTTPServer(app)
        http_server.listen(args.port)
        main_loop = tornado.ioloop.IOLoop.instance()
        log.info("Tornado Server started on port {}".format(args.port))
        main_loop.start()

    except KeyboardInterrupt:
        log.warning("Stopped by user.")

    except Exception as e:
        log.critical(e)


if __name__ == "__main__":
    main()





