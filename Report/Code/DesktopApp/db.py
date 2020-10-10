import sqlite3
import time


class sqlite3DB(object):
    """sqlite3 database class"""

    def __init__(self, db_location):
        """Initialize db class variables"""
        self.connection = sqlite3.connect(db_location)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        """Create a database table if it does not exist already"""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS "weather_records" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"sensor_id"	INTEGER NOT NULL DEFAULT 0,
	"station_id"	INTEGER NOT NULL DEFAULT 0,
	"temperature"	REAL NOT NULL DEFAULT 0,
	"pressure"	REAL NOT NULL DEFAULT 0,
	"light_intensity"	REAL NOT NULL DEFAULT 0,
	"humidity"	REAL NOT NULL DEFAULT 0,
	"wind_speed"	REAL NOT NULL DEFAULT 0,
	"wind_direction"	REAL NOT NULL DEFAULT 0,
	"timestamp"	INTEGER NOT NULL
	);''')

    def commit(self):
        """Commit changes to database"""
        self.connection.commit()

    def getLastRow(self):
        """Returns last weather record"""
        self.cursor.execute(
            'SELECT "temperature", "pressure", "light_intensity", "humidity", "wind_speed", "wind_direction", "timestamp" FROM "weather_records" ORDER BY id DESC LIMIT 1')
        return self.cursor.fetchone()

    def insert(self, data):
        """Inserts weather station records"""
        # Make a list from data 
        data = list(data)
        if len(data) == 8:
            # Add timestamp field
            data.append(time.time())
        # Insert to db
        self.cursor.execute(
            'INSERT INTO "weather_records" ("sensor_id", "station_id", "temperature", "pressure", "light_intensity", "humidity", "wind_speed", "wind_direction", "timestamp") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
            data)
        # Commit changes
        self.commit()
        # Return inserted row id
        return self.cursor.lastrowid

    def getDataBetween(self, start, end):
        """Return data in range of selected dates"""
        self.cursor.execute(
            'SELECT "temperature", "pressure", "light_intensity", "humidity", "wind_speed", "wind_direction", "timestamp" FROM "weather_records" WHERE "timestamp" > ? AND "timestamp" < ? ORDER BY id ASC',
            [start, end])
        return self.cursor.fetchall()

    def close(self):
        """Close sqlite3 connection"""
        # Commit changes before closing connection
        self.commit()
        # Close connection
        self.connection.close()

    def __del__(self):
        """Class destructor"""
        # Close db connection
        self.close()
