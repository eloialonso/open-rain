<p align="center">
   <img src="./static/images/logo.png" width="100" height="100" align="center">
</p>
<h1 align="center">Open Pluie</h1>

Homemade irrigation system with a Raspberry Pi, with two options:
<ol>
   <li> Custom regular watering with a <a href="https://en.wikipedia.org/wiki/Cron">cron</a> job.
   <li> On demand watering via a web interface.
</ol>


**Remark**: This project is supposed to be run on a Raspberry Pi. On a standard computer, you can still run a demo of the web interface.


**Table of contents**

- [Installation](#Installation)
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



## Hardware

Main components:

- A [solenoid valve](https://www.amazon.com/d/Electronic-Drums/2W-200-20-AC220V-4inch-Electric-Solenoid/B073LS9QPX).
- A [relay module](https://www.amazon.com/JBtek-Channel-Module-Arduino-Raspberry/dp/B00KTELP3I?ref_=fsclp_pl_dp_1).
- An [ultrasonic sensor](https://www.amazon.com/SainSmart-HC-SR04-Ranging-Detector-Distance/dp/B004U8TOE6/ref=sr_1_5?keywords=hcsr04&qid=1556912786&s=gateway&sr=8-5).

<img src="./static/images/schema.png" width="250" height="200" />

## Demo of the web interface (on a standard computer)

## On a Raspberry Pi
