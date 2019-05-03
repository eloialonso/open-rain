<p align="center">
<img src="./static/images/logo.png" width="100" height="100">
<h1 align="center">Open Pluie</h1>
</p>

Homemade irrigation system with a Raspberry Pi, with two options:
1. Custom regular watering with a [cron](https://en.wikipedia.org/wiki/Cron) job.
2. On demand watering via a web interface.

**Table of contents**

- [Getting started](#getting-started)
   - [Basic installation](#basic-installation)
   - [MySQL server](#mysql-server)
   - [Secret cookie](#secret-cookie)

## Installation

### Basic installation

**Note**: The basic installation is sufficient to run the first option (regular watering with a cron job, detailed [here](#TODO)).

Clone the project in your current location, and navigate to it:
```bash
git clone https://github.com/bloodymosquito/open-pluie.git
cd open-pluie
```

Create a python3 virtual environment with [virtualenv](https://pypi.org/project/virtualenv/) and activate it. For instance, create it in `~/.virtualenvs/openrain/`:
```bash
virtualenv -p python3 ~/.virtualenvs/openrain
source ~/.virtualenvs/openrain/bin/activate
```

Install the requirements for this project:
```bash
pip install -r requirements.txt
```

**Note**: For the second option (on demand watering via a web interface), you also need the following steps.


### MySQL server

To run the web server, you need [MySQL](https://dev.mysql.com/doc/refman/8.0/en/installing.html). You can install it with [this tutorial](https://support.rackspace.com/how-to/installing-mysql-server-on-ubuntu/).

Then, setup a MySQL database for the openpluie web server:
```bash
python mysql_setup.py
```
It creates a MySQL user called `admin_openpluie`, a database called `openpluie`, containing a table `users` containing the `admin` user for the website.

### Secret cookie

Create a secret cookie for the web server:
```bash
touch ./config/cookie.secret
```

Edit this file and write a long random sequence of characters on the first line.
