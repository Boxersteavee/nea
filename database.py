import sqlite3

# class for database
# initialise DB (connect, which creates the file if it doesn't exist)
# create tables if they don't already exist.

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db_conn = None
        try:
            self.db_conn = sqlite3.connect(db_path)
        except sqlite3.Error as e:
            print(f"SQL Error Occurred: {e}")

    def create_fam_db(self):
        with self.db_conn.cursor() as cursor:
            cursor.execute('''
               CREATE TABLE IF NOT EXISTS individuals (
                  id TEXT PRIMARY KEY,
                  first_name TEXT,
                  last_name TEXT,
                  sex TEXT,
                  birth_date TEXT,
                  birth_place TEXT,
                  death_date TEXT,
                  death_place TEXT,
                  occupation TEXT
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
        self.db_conn.commit()

    def add_person_data(self, id, first_name, last_name, sex, birth_date, birth_place, death_date, death_place, occupation):
        with self.db_conn.cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO individuals (
                    id, first_name, last_name, sex, birth_date, birth_place, death_date, death_place, occupation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                id,
                first_name,
                last_name,
                sex,
                birth_date,
                birth_place,
                death_date,
                death_place,
                occupation
            ))
        self.db_conn.commit()

    def add_family_data(self, id, husband_id, wife_id, marriage_date, marriage_place, children):
        with self.db_conn.cursor() as cursor:
            cursor.execute('''
                INSERT OR IGNORE INTO families (
                    id, husband_id, wife_id, marriage_date, marriage_place, children)
                VALUES (?, ?, ?, ?, ?, ?)
               ''', (
                   id,
                   husband_id,
                   wife_id,
                   marriage_date,
                   marriage_place,
                   ','.join(children)
               ))

    def close(self):
        self.db_conn.close()