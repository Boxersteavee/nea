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
            if isinstance(element, IndividualElement):
                id = normalise_id(element.get_pointer())

                # Get gender if available, set it to Male of Female
                if element.get_gender() == "M":
                    sex = "male"
                elif element.get_gender() == "F":
                    sex = "female"
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

        for element in elements:
            if isinstance(element, FamilyElement):
                id = normalise_id(element.get_pointer())
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
                        normalized_child_id = re.sub(r'^.*?@', '@', child_str)
                        normalized_child_id = normalise_id(normalized_child_id)
                        if normalized_child_id:
                            children.append(normalized_child_id)
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

                mother_id = normalise_id(mother_id)
                father_id = normalise_id(father_id)

                db.add_family_data(id, father_id, mother_id, marriage_date, marriage_place, children)

                children = []
        # print("Data Successfully Added to Database")

def run(gedcom_path):
    elements = parse_file(gedcom_path)
    db_dir = cfg['db_dir']
    os.makedirs(db_dir, exist_ok=True)
    gedcom_name = os.path.basename(gedcom_path)
    db_path = os.path.join(db_dir, gedcom_name.rsplit('.', 1)[0] + '.db')
    db = Database(db_path)
    db.create_fam_db()
    add_data(elements, db)
    db.backfill_parents()
    db.close()

