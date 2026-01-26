import sqlite3

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db_conn = None
        try:
            self.db_conn = sqlite3.connect(db_path)
            self.db_conn.execute("PRAGMA foreign_keys = ON") # Enforces Foreign Keys
            #self.db_conn.set_trace_callback(lambda s: print("SQL:", s)) # DEBUG: Print all SQL messages.
        except sqlite3.Error as e:
            print(f"SQL Error Occurred: {e}")

    def create_fam_db(self):
        cursor = self.db_conn.cursor()
        # Create individuals table, with mother_id and father_id set as foreign_keys dependent on id (which has a foreign key set by families table)
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
        # Create families table, with mother_id and father_id set to foreign keys linked to individuals(id), linking them to a person.
        # 'children' is a list which exists to make lookups easier, this is why this table is not normalised.
        # Having another table with duplicated of individuals would make things unnecessarily complicated.
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

        ### TRIGGERS ###
        # These triggers are necessary because the data is inserted after the table is created,
        # and as there are crossing over foreign keys, they must be updated after the data was inserted.
        # The triggers ensure that automatically occurs whenever the data is updated.


        # parent_insert_data inserts the mother_id and father_id of children, taken from the mother_id and father_id fields of a family row,
        # and inserted iteratively to each child in the 'children' list of that family
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

        # The parent_update_data trigger is currently unused,
        # It has the same goal as parent_add_data but when data about a family is being changed.
        # This is future-proofing for if I add the ability to edit a tree after uploading it.
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
        # The parent_delete_data trigger is also unused like parent_update_data
        # If editing functionality was implemented, this would be triggered when deleting families,
        # so would remove the mother_id and father_id from those children and set them to null.
        # Create parent_delete_data trigger
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


    # add_person_data takes information about an individual and adds them to the individuals table.
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

    # add_family_data takes information about a family and adds it to the families table
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

    # This method exists as a fallback incase parent_insert_data fails to fire.
    # It iterates through all individuals, finds where they occur in children of the families
    # table and adds the mother_id and father_id of that entry to that individual.
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

    # get_individuals iterates through the individuals table
    # appending each one (including all of their data) to a list
    def get_individuals(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT * FROM individuals")
        individuals = []
        for i in cursor:
            individuals.append(i)
        return individuals

    # get_families iterates through the families table
    # appending each one (including all data) to a list
    def get_families(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, father_id, mother_id FROM families")
        families = []
        for i in cursor:
            families.append(i)
        return families

# AUTH DATABASE FUNCTIONS
    # Create Users Table
    def create_user_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT,
                pass_hash TEXT,
                families TEXT
            )  
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            expires_at TEXT,
            FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE
            )
        ''')

        # This line exists to create a tree for the usernames field of the sessions table.
        # This increases the performance of looking up based on username as looking up through a B-Tree has a time complexity of O(log n),
        # compared to a linear search of O(n)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_username ON sessions(username)')
        self.db_conn.commit()

    # Creates a new user based on the username, email and password hash (salt embedded in hash)
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
    # Gets the families a specific username has by selecting the families field in the users table.
    # Takes this output, splits the string into a list and adds each entry to a list,
    # before returning the list
    # If result is blank, it returns an empty string
    def get_user_families(self, username):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        SELECT families
        FROM users
        WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()

        if result and result[0]:
            families_str = result[0]
            families_list = []

            for family in families_str.split(','):
                stripped_family = family.strip()
                if stripped_family:
                    families_list.append(stripped_family)

            return families_list

        return []

    # Adds a family to a user, first by getting their list of families (by calling get_user_families)
    # and then appending the given family to that list, and commiting it to the db.
    def add_family_to_user(self, username, family_name):
        cursor = self.db_conn.cursor()
        current_families = self.get_user_families(username)
        if family_name not in current_families:
            current_families.append(family_name)

        updated_families = ','.join(current_families)

        cursor.execute('''
        UPDATE users
        SET families = ?
        WHERE username = ?
        ''',(updated_families, username))
        self.db_conn.commit()

    # Deletes a user's family by calling get_user_families,
    # then tries to remove the given family from the list and commit it to the DB.
    # If the given family is not present, it silently continues.
    def delete_user_family(self, username, family_name):
        cursor = self.db_conn.cursor()
        current_families = self.get_user_families(username)

        try:
            current_families.remove(family_name)
        except ValueError:
            print("Family Not found, continuing...")
        updated_families = ','.join(current_families)

        cursor.execute('''
        UPDATE users
        SET families = ?
        WHERE username = ?
        ''', (updated_families, username))
        self.db_conn.commit()

    # Removes a given username from the DB (currently not used, exists in API)
    def delete_user(self, username):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            DELETE FROM users
                WHERE username = ?
        ''',(
            username,
        ))
        self.db_conn.commit()

    # Takes a username and returns their pass_hash
    # This is used in auth.py to verify a user's password.
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

    # Takes a username, a generated token, and the expiry timestamp, commits it to the DB
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

    # Gets the session token of a user, used to check a user is authenticated when making requests.
    def get_session(self, token):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        SELECT token, username, expires_at
        FROM sessions
        WHERE token = ?
        ''', (token,))
        return cursor.fetchone()

    # Deletes a session, which is called when a user attempts to use an invalid session
    def delete_session(self, token):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        DELETE FROM sessions
        WHERE token = ?
        ''', (token,))
        self.db_conn.commit()

    # Clears all sessions when the program restarts.
    # This also serves as a way to clear expired sessions.
    def clear_sessions(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        DELETE FROM sessions
        ''')
        self.db_conn.commit()

    # Commit to the DB and close the connection. This deletes the instance of the class.
    def close(self):
        self.db_conn.commit()
        self.db_conn.close()