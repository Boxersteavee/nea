from gedcom.parser import Parser
from gedcom.element.individual import IndividualElement
from gedcom.element.family import FamilyElement
import os
import re
from database import Database
from config import get_cfg

#
cfg = get_cfg()
DB_DIR = cfg['db_dir']

# Use python-gedcom to parse the gedcom file and compile a list of all elements
def parse_file(gedcom_path):
    parser = Parser()
    parser.parse_file(gedcom_path, False)
    elements = parser.get_element_list()
    return elements

# Function to normalise IDs, removing the surrounding @ symbols and the I/F prefix.
def normalise_id(id):
    if id is None:
        return None
    s = str(id).strip()
    nid = s.strip('@')
    nid = re.sub(r'^[A-Za-z]+', '', nid)
    nid = re.sub(r'^[A-Za-z]+', '', nid)
    return nid if nid != "" else None

# Function to iterate through all elements, collecting their data and adding it to the database.
def add_data(elements, db):
        # Iterate through all elements
        for element in elements:
            # Check if the element is an Individual (person), then process the data as such
            if isinstance(element, IndividualElement):
                id = normalise_id(element.get_pointer())

                # Get gender if available, set it to Male or Female
                if element.get_gender() == "M":
                    gender = "male"
                elif element.get_gender() == "F":
                    gender = "female"
                else:
                    gender = ""

                name_data = element.get_name()

                # Check if name_data contains anything.
                # If it does, set the first_name and last_name from it,
                # else leave it blank
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

                # Add all of this data to the database.
                db.add_person_data(id, first_name, last_name, gender, birth_date, birth_place, death_date, death_place, occupation)
            # Check if the element is a Family
            elif isinstance(element, FamilyElement):
                # Initially set values to None/Empty
                mother_id = None
                father_id = None
                marriage_date = ""
                marriage_place = ""
                children = []

                try:
                    # Try to set mother_id and father_id
                    # re.sub exists to strip text before the ID
                    mother_id = re.sub(r'^.*?@', '@', str(element.get_wives()[0]))
                    father_id = re.sub(r'^.*?@', '@', str(element.get_husbands()[0]))

                    # Iterate through the children in the family,
                    # cut the child name out of the string,
                    # retrieve their ID and normalise id,
                    # then append it to the children list
                    for child in element.get_children():
                        child_str = str(child).strip()
                        child_id = re.sub(r'^.*?@', '@', child_str)
                        normalised_child_id = normalise_id(child_id)
                        if normalised_child_id:
                            children.append(normalised_child_id)
                # If there's an IndexError (no data), allow it to pass and use the empty results.
                except IndexError:
                    pass

                # Iterate through the child elements (sub-elements, not elements of children) to get marriage information.
                for child in element.get_child_elements():
                     tag = child.get_tag()
                     if tag == 'MARR':
                         for fam_data in child.get_child_elements():
                             if fam_data.get_tag() == 'DATE':
                                 marriage_date = fam_data.get_value() or ""
                             elif fam_data.get_tag() == 'PLAC':
                                 marriage_place = fam_data.get_value() or ""

                # If mother_id or father_id are blank, set None
                if father_id == "":
                    father_id = None
                if mother_id == "":
                    mother_id = None

                # Normalise the IDs (remove '@' prefix and suffix)
                id = normalise_id(element.get_pointer())
                mother_id = normalise_id(mother_id)
                father_id = normalise_id(father_id)

                # Add family data and the children to the database
                db.add_family_data(id, father_id, mother_id, marriage_date, marriage_place)
                for child_id in children:
                    db.add_family_child(id, child_id)

# Function called by API to process uploaded gedcom file.
# Parse the file, create DB, create tables in DB, add data to DB, then close and commit.
def run(gedcom_path):
    elements = parse_file(gedcom_path)
    os.makedirs(DB_DIR, exist_ok=True)
    gedcom_name = os.path.basename(gedcom_path)
    db_path = os.path.join(DB_DIR, gedcom_name.rsplit('.', 1)[0] + '.db')
    db = Database(db_path)
    db.create_family_db()
    add_data(elements, db)
    db.close()