from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
import sqlite3
import os

def ParseFile(gedcom_path):
    gedcom_parser = Parser() # Initialise parser
    gedcom_parser.parse_file(gedcom_path, False) # Parse gedcom file given from path.
    elements = gedcom_parser.get_element_list() # Extract all elements from the file and save them to elements as a list
    return elements

def CreateDB(db_path, elements):
    # Create and connect to an SQL DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a table called individuals, with fields for information about each individual.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS individuals (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            sex TEXT,
            birth_date TEXT,
            birth_place TEXT,
            death_date TEXT,
            death_place TEXT
        )
    ''')

    # Create a table called families, with fields for information about each family.
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

    # Iterate through every element in the elements list.
    for element in elements:
        # if the element is an Individual (person), extract their information
        if isinstance(element, IndividualElement):
            name_data = element.get_name()
            if name_data:
                first_name, last_name = name_data
            else:
                first_name, last_name = "", ""

            sex = ""
            birth_date = ""
            birth_place = ""
            death_date = ""
            death_place = ""
            # If that individual has children, get their IDs and save that
            for child in element.get_child_elements():
                tag = child.get_tag()
                if tag == 'SEX':
                    sex = child.get_value() or ""
                elif tag == 'BIRT':
                    for b_child in child.get_child_elements():
                        if b_child.get_tag() == 'DATE':
                            birth_date = b_child.get_value() or ""
                        elif b_child.get_tag() == 'PLAC':
                            birth_place = b_child.get_value() or ""
                elif tag == 'DEAT':
                    for d_child in child.get_child_elements():
                        if d_child.get_tag() == 'DATE':
                            death_date = d_child.get_value() or ""
                        elif d_child.get_tag() == 'PLAC':
                            death_place = d_child.get_value() or ""
                elif tag == '_MARNM':
                    last_name = child.get_value() or last_name
            # Save the information about this individual to the database into the individuals table.
            cursor.execute('''
                INSERT OR IGNORE INTO individuals (id, first_name, last_name, sex, birth_date, birth_place, death_date, death_place)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                element.get_pointer(),
                first_name,
                last_name,
                sex,
                birth_date,
                birth_place,
                death_date,
                death_place
            ))

        elif element.get_tag() == 'FAM':
            husband_id = ""
            wife_id = ""
            marriage_date = ""
            marriage_place = ""
            children_ids = []
            for child in element.get_child_elements():
                tag = child.get_tag()
                if tag == 'HUSB':
                    husband_id = child.get_value() or ""
                elif tag == 'WIFE':
                    wife_id = child.get_value() or ""
                elif tag == 'CHIL':
                    children_ids.append(child.get_value() or "")
                elif tag == 'MARR':
                    for marr_child in child.get_child_elements():
                        if marr_child.get_tag() == 'DATE':
                            marriage_date = marr_child.get_value() or ""
                        elif marr_child.get_tag() == 'PLAC':
                            marriage_place = marr_child.get_value() or ""
            cursor.execute('''
                INSERT OR IGNORE INTO families (id, husband_id, wife_id, marriage_date, marriage_place, children)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                element.get_pointer(),
                husband_id,
                wife_id,
                marriage_date,
                marriage_place,
                ','.join(children_ids)
            ))

    conn.commit()
    conn.close()

def run(gedcom_path):
    elements = ParseFile(gedcom_path)
    db_dir = "database"
    os.makedirs(db_dir, exist_ok=True)
    gedcom_name = os.path.basename(gedcom_path)
    db_path = os.path.join(db_dir, gedcom_name.rsplit('.', 1)[0] + '.db')
    print(db_path)
    CreateDB(db_path, elements)
    print(f"Database created at {db_path}.")