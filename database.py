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
        cursor = self.db_conn.cursor()
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
        cursor = self.db_conn.cursor()
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
        cursor = self.db_conn.cursor()
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

    def create_user_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT,
                email TEXT,
                pass_hash TEXT,
                salt TEXT
            )  
        ''')
        self.db_conn.commit()

    def new_user(self, username, email, pass_hash, salt):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (
            username, email, pass_hash, salt)
        VALUES (?, ?, ?, ?)
        ''',(
            username,
            email,
            pass_hash,
            salt
        ))
        self.db_conn.commit()

    def verify_user(self, username):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            SELECT pass_hash, salt
            FROM users
            WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()

        if result:
            return result
        else:
            return(None, None)


    def close(self):
        self.db_conn.close()