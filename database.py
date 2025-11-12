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
            self.db_conn.execute("PRAGMA foreign_keys = ON")
            self.db_conn.set_trace_callback(lambda s: print("SQL:", s)) # DEBUG: Print all SQL messages.
        except sqlite3.Error as e:
            print(f"SQL Error Occurred: {e}")

    def create_fam_db(self):
        cursor = self.db_conn.cursor()
        # Create individuals table
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
              occupation TEXT,
              mother_id TEXT,
              father_id TEXT,
              FOREIGN KEY(father_id) REFERENCES individuals(id) ON DELETE SET NULL,
              FOREIGN KEY(mother_id) REFERENCES individuals(id) ON DELETE SET NULL               
           )
           ''')
        # Create families table
        cursor.execute('''
           CREATE TABLE IF NOT EXISTS families (
               id TEXT PRIMARY KEY,
               father_id TEXT,
               mother_id TEXT,
               marriage_date TEXT,
               marriage_place TEXT,
               children TEXT,
               FOREIGN KEY(mother_id) REFERENCES individuals(id) ON DELETE SET NULL,
               FOREIGN KEY(father_id) REFERENCES individuals(id) ON DELETE SET NULL
           )    
           ''')
        # Create parent_insert_data trigger
        cursor.executescript('''
            CREATE TRIGGER IF NOT EXISTS parent_insert_data
            AFTER INSERT ON families
            BEGIN
                WITH RECURSIVE split(token, rest) AS (
                    SELECT '', COALESCE(NEW.children, '') || ','
                    UNION ALL
                    SELECT substr(rest, 1, instr(rest, ',') -1),
                           substr(rest, instr(rest, ',') + 1)
                    FROM split
                    WHERE rest <> ''
                )
                UPDATE individuals
                SET father_id = NEW.father_id,
                    mother_id = NEW.mother_id
                WHERE id IN (SELECT trim(token) FROM split WHERE token <> '');
            END;
            ''')

        cursor.executescript('''
            CREATE TRIGGER IF NOT EXISTS parent_update_data
            AFTER UPDATE OF father_id, mother_id, children ON families
            BEGIN
                WITH RECURSIVE split_new(token, rest) AS (
                    SELECT '', COALESCE(NEW.children, '') || ','
                    UNION ALL
                    SELECT substr(rest, 1, instr(rest, ',') - 1),
                           substr(rest, instr(rest, ',') + 1)
                    FROM split_new
                    WHERE rest <> ''
                ), split_old(token, rest) AS (
                    SELECT '', COALESCE(OLD.children, '') || ','
                    UNION ALL
                    SELECT substr(rest, 1, instr(rest, ',') - 1),
                           substr(rest, instr(rest, ',') + 1)
                    FROM split_old
                    WHERE rest <> ''
                )
                
               UPDATE individuals
               SET father_id = CASE WHEN father_id = OLD.father_id THEN NULL ELSE father_id END,
                   mother_id = CASE WHEN mother_id = OLD.mother_id THEN NULL ELSE mother_id END
               WHERE id IN (SELECT trim(token) FROM split_old WHERE token <> '');
    
               UPDATE individuals
               SET father_id = NEW.father_id,
                   mother_id = NEW.mother_id
               WHERE id IN (SELECT trim(token) FROM split_new WHERE token <> '');
            END;
            ''')
        cursor.executescript('''
            CREATE TRIGGER IF NOT EXISTS parent_delete_data
            AFTER DELETE ON families
            BEGIN
                WITH RECURSIVE split(token, rest) AS (
                    SELECT '', COALESCE(OLD.children, '') || ','
                    UNION ALL
                    SELECT substr(rest, 1, instr(rest, ',') - 1),
                           substr(rest, instr(rest, ',') + 1)
                    FROM split
                    WHERE rest <> ''
                )
                UPDATE individuals
                SET father_id = CASE WHEN father_id = OLD.father_id THEN NULL ELSE father_id END,
                    mother_id = CASE WHEN mother_id = OLD.mother_id THEN NULL ELSE mother_id END
                WHERE id IN (SELECT trim(token) FROM split WHERE token <> '');
            END;
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

    def add_family_data(self, id, father_id, mother_id, marriage_date, marriage_place, children):
        cursor = self.db_conn.cursor()
        children_str = ','.join(children) if children else ''
        cursor.execute('''
            INSERT OR IGNORE INTO families (
                id, father_id, mother_id, marriage_date, marriage_place, children)
            VALUES (?, ?, ?, ?, ?, ?)
           ''', (
               id,
               father_id,
               mother_id,
               marriage_date,
               marriage_place,
               children_str
           ))
        self.db_conn.commit()

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