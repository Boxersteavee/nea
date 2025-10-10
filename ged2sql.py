from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
import sqlite3
import os
import re
from database import Database

def parse_file(gedcom_path):
    parser = Parser()
    parser.parse_file(gedcom_path, False)
    elements = parser.get_element_list()
    return elements

def add_data(db_path, elements, db):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        children = []
        for element in elements:
            if isinstance(element, IndividualElement):
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

                db.add_person_data(id, first_name, last_name, sex, birth_date, birth_place, death_date, death_place, occupation)

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

                db.add_family_data(id, husband_id, wife_id, marriage_date, marriage_place, children)

                children = []
        conn.commit()
        print("Data Successfully Added to Database")

def run(gedcom_path):
    elements = parse_file(gedcom_path)
    db_dir = "user_data/sql"
    os.makedirs(db_dir, exist_ok=True)
    gedcom_name = os.path.basename(gedcom_path)
    db_path = os.path.join(db_dir, gedcom_name.rsplit('.', 1)[0] + '.db')
    print(db_path)
    db = Database(db_path)
    db.create_fam_db()
    print(f"Adding data from {gedcom_path}")
    add_data(db_path, elements, db)
    db.close()