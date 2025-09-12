from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
import sqlite3
import os


def parse_file(gedcom_path):
    parser = Parser()
    parser.parse_file(gedcom_path, False)
    elements = parser.get_element_list()
    return elements

# define CreateDB with db_path and elements as inputs
def CreateDB(db_path):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS individuals (
                    id TEXT PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    maiden_surname TEXT,
                    sex TEXT,
                    birth_date TEXT,
                    birth_place TEXT,
                    death_date TEXT,
                    death_place TEXT,
                    occupation TEXT,
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS families (
                    id TEXT PRIMARY KEY,
                    husband_id TEXT,
                    wife_id TEXT,
                    marriage_date TEXT,
                    marriage_place TEXT,
                    children TEXT
                )
            ''')
            print("Database and Tables successfully Created.")
    except sqlite3.Error as e:
        print(f"An SQL error occurred: {e}")


# connect to and initialise DB
# initialise cursor
# Create Table "individuals":
# id
# first_name
# last_name
# sex
# birth_date
# birth_place
# death_date
# death_place
# occupation
# religion
# maiden_surname

# Create Table "families"
# id
# husband_id
# wife_id
# marriage_date
# marriage_place
# children_ID

