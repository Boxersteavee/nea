from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
import sqlite3

def ParseFile(Gedcom_Path):
    gedcom_parser = Parser()
    gedcom_parser.parse_file(Gedcom_Path, False)
    elements = gedcom_parser.get_element_list()
    return elements

def TestSurnames(elements):
    for element in elements:
        # Ensure the element is an IndividualElement
        if isinstance(element, IndividualElement):
            # Get the name tuple (first, last)
            name_data = element.get_name()
            if name_data:
                first_name, last_name = name_data
                print(f"ID: {element.get_pointer()} | First Name: {first_name} | Surname: {last_name}")
            else:
                print(f"ID: {element.get_pointer()} | Surname: Not Found")

def CreateDB(db_path, elements):
    import sqlite3
    conn = sqlite3.connect(db_path)
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
            death_place TEXT
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

    for element in elements:
        if isinstance(element, IndividualElement):
            # Extract first and last name using the same logic as TestSurnames
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