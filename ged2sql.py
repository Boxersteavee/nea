from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
import sqlite3
import os
import re

def parse_file(gedcom_path):
    parser = Parser()
    parser.parse_file(gedcom_path, False)
    elements = parser.get_element_list()
    return elements

# define CreateDB with db_path and elements as inputs
def create_db(db_path):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

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
            conn.commit()
            print("Database and Tables successfully Created.")
    except sqlite3.Error as e:
        print(f"An SQL error occurred: {e}")

def add_data(db_path, elements):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        children = []
        for element in elements:
            if isinstance(element, IndividualElement):
                id = ""
                sex = ""
                first_name = ""
                last_name = ""
                birth_date = ""
                birth_place = ""
                death_date = ""
                death_place = ""
                occupation = ""

                id = element.get_pointer()

                # Get Sex if available, set it to Male of Female
                if element.get_gender() == "M":
                    sex = "Male"
                elif element.get_gender() == "F":
                    sex = "Female"
                else:
                    sex = ""

                name_data = element.get_name()
                if name_data:
                    first_name, last_name = name_data
                else:
                    first_name, last_name = "", ""

                birth_date = element.get_birth_date()
                birth_place = element.get_birth_place()
                death_date = element.get_death_date()
                death_place = element.get_death_place()
                occupation = element.get_occupation()

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

            elif isinstance(element, FamilyElement):
                id = element.get_pointer()
                try:
                    wife_id = re.sub(r'^.*?@', '@', str(element.get_wives()[0]))
                    husband_id = re.sub(r'^.*?@', '@', str(element.get_husbands()[0]))
                    for child in element.get_children():
                        child_str = str(child).strip()
                        children.append(re.sub(r'^.*?@', '@', child_str))
                except IndexError:
                    pass
                for child in element.get_child_elements():
                     tag = child.get_tag()
                     if tag == 'MARR':
                         for fam_data in child.get_child_elements():
                             if fam_data.get_tag() == 'DATE':
                                 marriage_date = fam_data.get_value() or ""
                             elif fam_data.get_tag() == 'PLAC':
                                 marriage_place = fam_data.get_value() or ""

                cursor.execute('''
                    INSERT OR IGNORE INTO families (id, husband_id, wife_id, marriage_date, marriage_place, children)
                        VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    id,
                    husband_id,
                    wife_id,
                    marriage_date,
                    marriage_place,
                    ','.join(children)
                ))

                children = []
        conn.commit()
        print("Data Successfully Added to Database")

def run(gedcom_path):
    elements = parse_file(gedcom_path)
    db_dir = "database"
    os.makedirs(db_dir, exist_ok=True)
    gedcom_name = os.path.basename(gedcom_path)
    db_path = os.path.join(db_dir, gedcom_name.rsplit('.', 1)[0] + '.db')
    print(db_path)
    if not os.path.isfile(db_path):
        print(f"Database does not exist. Creating Database at {db_path}")
        create_db(db_path)
        print(f"Database created at {db_path}")
    print(f"Adding data from {gedcom_path}")
    add_data(db_path, elements)

if __name__ == "__main__":
    db_path = "database/test.db"
    gedcom_path = "gedcom/36rm6c_290955k3v36ed7wt2f46dc_A.ged"
    if not os.path.isfile(db_path):
        create_db(db_path)
    add_data(db_path, parse_file(gedcom_path))