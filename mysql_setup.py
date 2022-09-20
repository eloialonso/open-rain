#! /usr/bin/env python
# coding: utf-8


"""Script to set up a mysql database.

1) Create 'openrain' MySQL database.
2) Create 'admin_openrain' MySQL user.
3) Create 'users' table in 'openrain' database.
4) Insert an admin user entry in the 'users' table.
"""


import bcrypt
from getpass import getpass
import mysql.connector
import tornado.escape


def main():
    """Main function of our script."""

    # Log in with root
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=getpass("[MySQL] Root password: ")
        )
    cursor = connection.cursor()

    # 1) Create the database 'openrain'
    try:
        print("\n[MySQL] Creating database 'openrain'.")
        cursor.execute("""CREATE DATABASE openrain""")
    except mysql.connector.errors.DatabaseError:
        overwrite = input("\t --> Database 'openrain' already exists. Overwrite it? [y/N] ").lower() == "y"
        if overwrite:
            print("\t --> Overwriting database 'openrain'.")
            cursor.execute("""DROP DATABASE openrain""")
            cursor.execute("""CREATE DATABASE openrain""")
        else:
            print("\nExiting.")
            return

    # 2) Create the user 'admin_openrain'
    print("\n[MySQL] Creating user 'admin_openrain'.")
    sql_pwd = getpass("\t --> Define a password for 'admin_openrain': ")
    cursor.execute("""GRANT ALL PRIVILEGES ON *.* TO 'admin_openrain'@'localhost' IDENTIFIED BY '{}'""".format(sql_pwd))
    print("\t --> User 'admin_openrain' successfully created.")


    # Close the connection of root
    cursor.close()
    connection.close()

    # Log in with 'admin_openrain' user
    connection = mysql.connector.connect(
        host="localhost",
        database="openrain",
        user="admin_openrain",
        password=sql_pwd
        )
    cursor = connection.cursor()

    # 3) Create table 'users'
    print("\n[MySQL] Creating table 'users'.")
    cursor.execute(
        """
        CREATE TABLE users (
            id INT (11) NOT NULL AUTO_INCREMENT,
            admin BOOLEAN NOT NULL DEFAULT false,
            username VARCHAR (100) NOT NULL UNIQUE,
            hashed_password VARCHAR (100) NOT NULL,
            PRIMARY KEY (id)
        )
        """)
    print("\t --> Table 'users' successfully created.")

    # 4) Create a new user (admin) for our website
    print("\n[Website] Creating user 'admin'.")

    # Get password and hash it
    admin_pwd = getpass("\t --> Define a password for user 'admin': ")
    hash_admin_pwd = bcrypt.hashpw(
        tornado.escape.utf8(admin_pwd),
        bcrypt.gensalt()
    ).decode("utf-8")

    # Insert admin in db
    cursor.execute("""INSERT INTO users (admin, username, hashed_password) VALUES (1, "admin", "{}")""".format(hash_admin_pwd))
    print("\t --> User 'admin' successfully created.")

    # Exiting
    connection.commit()
    print("\nDone.")
    cursor.close()
    connection.close()
    return


if __name__ == "__main__":
    main()



