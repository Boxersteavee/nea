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
            #self.db_conn.set_trace_callback(lambda s: print("SQL:", s)) # DEBUG: Print all SQL messages.
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
        try:
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS parent_insert_data
                AFTER INSERT ON families
                BEGIN
                    UPDATE individuals
                    SET father_id = NEW.father_id,
                        mother_id = NEW.mother_id
                    WHERE id IN (
                        WITH RECURSIVE split(token, rest) AS (
                            SELECT '', COALESCE(NEW.children, '') || ','
                            UNION ALL
                            SELECT substr(rest, 1, instr(rest, ',') - 1),
                                   substr(rest, instr(rest, ',') + 1)
                            FROM split
                            WHERE rest <> ''
                        )
                        SELECT trim(token) FROM split WHERE token <> ''
                    );
                END;
            ''')
        except sqlite3.DatabaseError as e:
            print(f"failed on insert_data: {e}")
            raise
        # Create parent_update_data
        try:
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS parent_update_data
                AFTER UPDATE OF father_id, mother_id, children ON families
                BEGIN
                    -- Reset old parent relationships
                    UPDATE individuals
                    SET father_id = CASE WHEN father_id = OLD.father_id THEN NULL ELSE father_id END,
                        mother_id = CASE WHEN mother_id = OLD.mother_id THEN NULL ELSE mother_id END
                    WHERE id IN (
                        WITH RECURSIVE split_old(token, rest) AS (
                            SELECT '', COALESCE(OLD.children, '') || ','
                            UNION ALL
                            SELECT substr(rest, 1, instr(rest, ',') - 1),
                                   substr(rest, instr(rest, ',') + 1)
                            FROM split_old
                            WHERE rest <> ''
                        )
                        SELECT trim(token) FROM split_old WHERE token <> ''
                    );
        
                    -- Set new parent relationships
                    UPDATE individuals
                    SET father_id = NEW.father_id,
                        mother_id = NEW.mother_id
                    WHERE id IN (
                        WITH RECURSIVE split_new(token, rest) AS (
                            SELECT '', COALESCE(NEW.children, '') || ','
                            UNION ALL
                            SELECT substr(rest, 1, instr(rest, ',') - 1),
                                   substr(rest, instr(rest, ',') + 1)
                            FROM split_new
                            WHERE rest <> ''
                        )
                        SELECT trim(token) FROM split_new WHERE token <> ''
                    );
                END;
            ''')
        except sqlite3.DatabaseError as e:
            print(f"Failed on update_data: {e}")
            raise
        try:
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS parent_delete_data
                AFTER DELETE ON families
                BEGIN
                    UPDATE individuals
                    SET father_id = CASE WHEN father_id = OLD.father_id THEN NULL ELSE father_id END,
                        mother_id = CASE WHEN mother_id = OLD.mother_id THEN NULL ELSE mother_id END
                    WHERE id IN (
                        WITH RECURSIVE split(token, rest) AS (
                            SELECT '', COALESCE(OLD.children, '') || ','
                            UNION ALL
                            SELECT substr(rest, 1, instr(rest, ',') - 1),
                                   substr(rest, instr(rest, ',') + 1)
                            FROM split
                            WHERE rest <> ''
                        )
                        SELECT trim(token) FROM split WHERE token <> ''
                    );
                END;
            ''')
        except sqlite3.DatabaseError as e:
            print(f"Failed on delete_data: {e}")
            raise
        self.db_conn.commit()

    def add_person_data(self, id, first_name, last_name, sex, birth_date, birth_place, death_date, death_place, occupation):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO individuals (
                id, first_name, last_name, sex, birth_date, birth_place, death_date, death_place, occupation, mother_id, father_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
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
        # print(f"Inserting family: {id}, father={father_id}, mother={mother_id}, children={children_str}")
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

    def backfill_parents(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
           UPDATE individuals
           SET father_id = (
                SELECT f.father_id
                FROM families f
                WHERE ',' || f.children || ',' LIKE '%,' || individuals.id || ',%'
                LIMIT 1
            ),
            mother_id = (
                SELECT f.mother_id
                FROM families f
                WHERE ',' || f.children || ',' LIKE '%,' || individuals.id || ',%'
                LIMIT 1
            )
            WHERE EXISTS (
                SELECT 1 FROM families f
                WHERE ',' || f.children || ',' LIKE '%,' || individuals.id || ',%'
            );
           ''')
        self.db_conn.commit()
# AUTH DATABASE FUNCTIONS
    def create_user_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT,
                pass_hash TEXT
            )  
        ''')
        self.db_conn.commit()

    def new_user(self, username, email, pass_hash):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        
        INSERT INTO users (
            username, email, pass_hash)
        VALUES (?, ?, ?)
        ''',(
            username,
            email,
            pass_hash
        ))
        self.db_conn.commit()

    def delete_user(self, username):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            DELETE FROM users
                WHERE username = ?
        ''',(
            username,
        ))
        self.db_conn.commit()

    def verify_user(self, username):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            SELECT pass_hash
            FROM users
            WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    # SESSIONS MANAGEMENT
    def create_sessions_table(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at TEXT,
            FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_username ON sessions(username)')
        self.db_conn.commit()

    def save_session(self, username, token, expires_at):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO sessions (
            token, username, expires_at)
        VALUES (?, ?, ?)
        ''',(
            token,
            username,
            expires_at
        ))
        self.db_conn.commit()

    def get_session(self, token):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        SELECT token, username, expires_at
        FROM sessions
        WHERE token = ?
        ''', (token,))
        return cursor.fetchone()

    def delete_session(self, token):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        DELETE FROM sessions
        WHERE token = ?
        ''', (token,))
        self.db_conn.commit()

    def close(self):
        self.db_conn.commit()
        self.db_conn.close()