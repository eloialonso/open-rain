import bcrypt
import concurrent.futures
import MySQLdb
import markdown
import os
import sys
import re
import json
import functools
import unicodedata
import subprocess
import torndb
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import RPi.GPIO as GPIO

from tornado import gen
from tornado.options import define, options

define("port", default=9080, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="openpluie", help="blog database name")
define("mysql_user", default="eloi", help="blog database user")
define("mysql_password", default="openpluie", help="blog database password")

# open log file
log_file = open("./server.log", 'w')

# A thread pool to be used for password hashing with bcrypt.
executor = concurrent.futures.ThreadPoolExecutor(2)

# pins list
with open("./config/pins.json", "r") as f:
    all_pins = json.load(f)
#with open("./config/pins.txt", "r") as f:
#    pins = next(f).split(" ")

pins = [int(pin) for id, pin in all_pins["relay"].items()]

# loop through pins and set mode and state to "high"
GPIO.setmode(GPIO.BCM)
for i in pins:
   GPIO.setup(i, GPIO.OUT)
   GPIO.output(i, GPIO.HIGH)

# Admin decorator
def admin(method):
    """Decorate methods with this to require that the user be logged in as an admin."""
    @tornado.web.authenticated
    def wrapper(self, *args, **kwargs):
        if not self.user_is_admin():
            raise tornado.web.HTTPError(403), 'you are not admin'
        return method(self, *args, **kwargs)
    return wrapper


class Application(tornado.web.Application):
    def __init__(self):
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
            cookie_secret="iuev1456yih5678kvje78on",
            login_url="/auth/login",
            debug=True,
        )

        super(Application, self).__init__(handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        self.db = torndb.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)

        # manage gpio state
        self.gpio_state = [False] * len(pins)


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    @property
    def gpio_state(self):
        return self.application.gpio_state

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id:
            return None
        return self.db.get("SELECT * FROM users WHERE id = %s", int(user_id))

    def any_user_exists(self):
        return bool(self.db.get("SELECT * FROM users LIMIT 1"))

    def user_is_admin(self):
        user = self.get_current_user()
        if user:
            return user.username=='admin' and user.first_name=="Eloi" and user.last_name=="Alonso"
        return False

class HomeHandler(BaseHandler):
    @tornado.web.authenticated # this decorator redirects the user the login_url if he is not authenticated
    def get(self):
        print >> log_file, "[HTTP](MainHandler) {} connected.".format(self.get_current_user().username)
        # name = tornado.escape.xhtml_escape(self.current_user)
        # self.write("Hello, " + name)
        self.render("home.html", admin=self.user_is_admin(), gpio_state=self.gpio_state)


class AuthCreateHandler(BaseHandler):
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
        if bool(self.db.get("SELECT * FROM users WHERE username = %s", username)):
            # raise tornado.web.HTTPError(400, "user already created, please choose another username.")
            self.render("create_user.html", error="user already created, please choose another username.")
            return
        if self.get_argument("password") != self.get_argument("password2"):
            self.render("create_user.html", error="Passwords are different.")
            return
        user_id = self.db.execute(
            "INSERT INTO users (username, first_name, last_name, hashed_password) "
            "VALUES (%s, %s, %s, %s)", username, self.get_argument("first_name"),
            self.get_argument("last_name"), hashed_password)
        self.redirect(self.get_argument("next", "/"))


class AuthLoginHandler(BaseHandler):
    def get(self):
        self.render("login.html", error=None)

    @gen.coroutine
    def post(self):
        user = self.db.get("SELECT * FROM users WHERE username = %s", self.get_argument("username"))
        if not user:
            self.render("login.html", error="username not found")
            return
        hashed_password = yield executor.submit(
            bcrypt.hashpw, tornado.escape.utf8(self.get_argument("password")),
            tornado.escape.utf8(user.hashed_password))
        if hashed_password == user.hashed_password:
            self.set_secure_cookie("user", str(user.id), expires_days=None)
            self.redirect(self.get_argument("next", "/"))
        else:
            self.render("login.html", error="incorrect password")


class AuthLogoutHandler(BaseHandler):
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
        print >> log_file, '[WS] Connection was opened.'

    def on_message(self, message):
        print >> log_file, '[WS] Incoming message: {}'.format(message)
        print >> log_file, '[App] GPIO states : {} '.format(self.application.gpio_state)
        if message == "slider1_on":
            self.application.gpio_state[0] = True
            GPIO.output(pins[0], GPIO.LOW)
        elif message == "slider1_off":
            self.application.gpio_state[0] = False
            GPIO.output(pins[0], GPIO.HIGH)
        elif message == "slider2_on":
            self.application.gpio_state[1] = True
            GPIO.output(pins[1], GPIO.LOW)
        elif message == "slider2_off":
            self.application.gpio_state[1] = False
            GPIO.output(pins[1], GPIO.HIGH)
        else:
            raise tornado.web.HTTPError(404), "Unknown WS message"


    def on_close(self):
        print >> log_file, '[WS] Connection was closed.'


def main():

    try:
        tornado.options.parse_command_line()
        http_server = tornado.httpserver.HTTPServer(Application())
        http_server.listen(options.port)
        main_loop = tornado.ioloop.IOLoop.instance()
        print >> log_file, 'Tornado Server started'

        main_loop.start()

    except:
        print >> log_file, "Exception triggered - Tornado Server stopped."
        for i in pins:
               GPIO.setup(i, GPIO.OUT)
               GPIO.output(i, GPIO.HIGH)
        GPIO.cleanup()
        log_file.close()

if __name__ == "__main__":
    main()




