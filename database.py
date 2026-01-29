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

    ### ADDING TREE DATA ###

    def create_family_db(self):
        cursor = self.db_conn.cursor()
        # Create individuals table
        cursor.execute('''
           CREATE TABLE IF NOT EXISTS individuals (
              id TEXT PRIMARY KEY,
              first_name TEXT,
              last_name TEXT,
              gender TEXT,
              birth_date TEXT,
              birth_place TEXT,
              death_date TEXT,
              death_place TEXT,
              occupation TEXT            
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
               FOREIGN KEY(mother_id) REFERENCES individuals(id) ON DELETE SET NULL,
               FOREIGN KEY(father_id) REFERENCES individuals(id) ON DELETE SET NULL
           )    
           ''')

        # Creates linked table of family_children, which exists to keep track of the children each family has.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS family_children (
                family_id TEXT NOT NULL,
                child_id TEXT NOT NULL,
                PRIMARY KEY (family_id, child_id),
                FOREIGN KEY(family_id) REFERENCES families(id) ON DELETE CASCADE,
                FOREIGN KEY(child_id) REFERENCES individuals(id) ON DELETE CASCADE
                )
        ''')
        self.db_conn.commit()


    # add_person_data takes information about an individual and adds them to the individuals table.
    def add_person_data(self, id, first_name, last_name, gender, birth_date, birth_place, death_date, death_place, occupation):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO individuals (
                id, first_name, last_name, gender, birth_date, birth_place, death_date, death_place, occupation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
            id,
            first_name,
            last_name,
            gender,
            birth_date,
            birth_place,
            death_date,
            death_place,
            occupation
        ))
        self.db_conn.commit()

    # add_family_data takes information about a family and adds it to the families table
    def add_family_data(self, id, father_id, mother_id, marriage_date, marriage_place):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO families (
                id, father_id, mother_id, marriage_date, marriage_place)
            VALUES (?, ?, ?, ?, ?)
           ''', (
               id,
               father_id,
               mother_id,
               marriage_date,
               marriage_place,
           ))
        self.db_conn.commit()

    def add_family_child(self, family_id, child_id):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO family_children (family_id, child_id)
            VALUES (?, ?)
        ''', (family_id, child_id))
        self.db_conn.commit()

    ### RETRIEVING TREE DATA ###

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

    def get_individual_parents(self, child_id):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            SELECT families.mother_id, families.father_id
            FROM family_children
            JOIN families ON family_children.family_id = families.id
            WHERE family_children.child_id = ?
        ''', (child_id,))
        result = cursor.fetchone()
        if result:
            return result
        else:
            return (None, None)

    ##### AUTH DATABASE FUNCTIONS #####

    # Create Users Table
    def create_auth_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT,
                pass_hash TEXT
            )  
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trees (
                tree_name TEXT PRIMARY KEY
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_trees (
                username TEXT NOT NULL,
                tree_name TEXT NOT NULL,
                PRIMARY KEY (username, tree_name),
                FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE,
                FOREIGN KEY(tree_name) REFERENCES trees(tree_name) ON DELETE CASCADE
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
    # Gets the trees a specific username has access to by selecting the trees field in the users table.
    # Takes this output, splits the string into a list and adds each entry to a list,
    # before returning the list
    # If result is blank, it returns an empty string
    def get_user_trees(self, username):
        cursor = self.db_conn.cursor()
        cursor.execute('''
        SELECT tree_name
        FROM user_trees
        WHERE username = ?
        ''', (username,))
        result = cursor.fetchall()

        trees_list = []
        for row in result:
            trees_list.append(row[0])

        return trees_list

    # Adds a trees to a user, first by getting their list of trees (by calling get_user_trees)
    # and then appending the given trees to that list, and commiting it to the db.
    def add_tree_to_user(self, username, tree_name):
        cursor = self.db_conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO trees (tree_name)
            VALUES (?)
        ''', (tree_name,))

        cursor.execute('''
            INSERT OR IGNORE INTO user_trees (username, tree_name)
            VALUES (?,?)
        ''', (username, tree_name))

        self.db_conn.commit()

    # Deletes a user's trees by calling get_user_trees,
    # then tries to remove the given trees from the list and commit it to the DB.
    # If the given trees is not present, it silently continues.
    def delete_user_tree(self, username, tree_name):
        cursor = self.db_conn.cursor()

        cursor.execute('''
            DELETE FROM user_trees
            WHERE username = ? AND tree_name = ?
        ''', (username, tree_name))

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

    # Commit to the DB and close the connection.
    def close(self):
        self.db_conn.commit()
        self.db_conn.close()