from configparser import ConfigParser
import psycopg2

import os


def db_connection():
    config = ConfigParser()
    config.read(os.path.join("..", "db_config.ini"))
    try:
        return psycopg2.connect(
            host=config["postgresql"]["host"],
            dbname=config["postgresql"]["dbname"],
            user=config["postgresql"]["user"],
            password=config["postgresql"]["password"],
            port=int(config["postgresql"]["port"]),
        )
    except KeyError as e:
        print(f"Error: Missing configuration key in db_config.ini. Details: {e}")
        return None
    except Exception as e:
        print(f"Error connecting to PostgreSQL database. Details: {e}")
        return None
