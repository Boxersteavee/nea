from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
import os
import re
from database import Database
from config import get_cfg

cfg = get_cfg()

def parse_file(gedcom_path):
    parser = Parser()
    parser.parse_file(gedcom_path, False)
    elements = parser.get_element_list()
    return elements

def normalise_id(id):
    if id is None:
        return None
    s = str(id).strip()
    nid = s.strip('@')
    nid = re.sub(r'^[A-Za-z]+', '', nid)
    nid = re.sub(r'^[A-Za-z]+', '', nid)
    return nid if nid != "" else None

def add_data(elements, db):
        for element in elements:
            if isinstance(element, IndividualElement): # If the element is an individual (person)
                id = normalise_id(element.get_pointer())

                # Get gender if available, set it to Male or Female
                if element.get_gender() == "M":
                    gender = "male"
                elif element.get_gender() == "F":
                    gender = "female"
                else:
                    gender = ""

                name_data = element.get_name()

                # Check if name_data contains anything. If it does, set the first_name and last_name from it, else leave it blank
                if name_data:
                    first_name, last_name = name_data
                else:
                    first_name, last_name = "", ""

                # Retrieve other data
                birth_date = element.get_birth_date()
                birth_place = element.get_birth_place()
                death_date = element.get_death_date()
                death_place = element.get_death_place()
                occupation = element.get_occupation()

                db.add_person_data(id, first_name, last_name, gender, birth_date, birth_place, death_date, death_place, occupation)

            elif isinstance(element, FamilyElement): # If the element is a Family
                id = None
                mother_id = None
                father_id = None
                marriage_date = ""
                marriage_place = ""
                children = []

                try:
                    mother_id = re.sub(r'^.*?@', '@', str(element.get_wives()[0]))
                    father_id = re.sub(r'^.*?@', '@', str(element.get_husbands()[0]))
                    children = []
                    for child in element.get_children():
                        child_str = str(child).strip()
                        child_id = re.sub(r'^.*?@', '@', child_str)
                        normalised_child_id = normalise_id(child_id)
                        if normalised_child_id:
                            children.append(normalised_child_id)
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

                if father_id == "" or father_id is None:
                    father_id = None
                if mother_id == "" or mother_id is None:
                    mother_id = None

                id = normalise_id(element.get_pointer())
                mother_id = normalise_id(mother_id)
                father_id = normalise_id(father_id)

                db.add_family_data(id, father_id, mother_id, marriage_date, marriage_place)
                for child_id in children:
                    db.add_family_child(id, child_id)

def run(gedcom_path):
    elements = parse_file(gedcom_path)
    db_dir = cfg['db_dir']
    os.makedirs(db_dir, exist_ok=True)
    gedcom_name = os.path.basename(gedcom_path)
    db_path = os.path.join(db_dir, gedcom_name.rsplit('.', 1)[0] + '.db')
    db = Database(db_path)
    db.create_fam_db()
    add_data(elements, db)
    db.close()