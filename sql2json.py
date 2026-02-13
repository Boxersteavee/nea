from database import Database
from config import get_cfg
import os

# Get db_dir from the config and set it as global variable
cfg = get_cfg()
DB_DIR = cfg['db_dir']

# Get the data for each individual from the database
def get_individuals_data(db):
    # Get individuals and families from DB into a list
    individuals = db.get_individuals()
    families = db.get_families()

    # Build a map of all partners from the mother_id and father_id in each family
    partner_map = {}
    for family in families:
        family_id, father_id, mother_id = family
        if father_id and mother_id:
            partner_map[father_id] = mother_id
            partner_map[mother_id] = father_id

    # Build a list of individuals
    raw_individuals = []
    # Iterate through individuals,
    # get parents from DB function,
    # get partners from the partner_map,
    # then add their data to the list
    for individual in individuals:
        id = individual[0]
        mother_id, father_id = db.get_individual_parents(id)
        partner_id = partner_map.get(id)
        raw_individuals.append(individual + (mother_id, father_id, partner_id))
    return raw_individuals

# Convert the list into a json list
def jsonify(individuals):
    jsonified = []
    # Iterate through individuals to add data to the new list
    for i in individuals:
        # Check if they have a partner, if not then set pids to be an empty list
        if i[11] is not None:
            pids = [i[11]]
        else:
            pids = []
        # Add all of the data from the individual to a labeled section, then append it to the jsonified list
        entry = {
            "id": i[0],
            "Name": f"{i[1]} {i[2]}",
            "gender": i[3],
            "Birth Date": i[4],
            "Birth Place": i[5],
            "Death Date": i[6],
            "Death Place": i[7],
            "Occupation": i[8],
            "mid": i[9],
            "fid": i[10],
            "pids": pids
        }
        jsonified.append(entry)
    return jsonified

# Sometimes, gedcom files contain people which have no connections.
# These should not be displayed as they have no connections, and cause clutter when rendered.
# This function exists to filter them out.
def remove_isolated_individuals(individuals):
    # Builds a list of parents
    # If someone ends up in this list then they have
    # at least one child,so should not be filtered
    parent_ids = []
    for individual in individuals:
        if individual['mid'] is not None:
            if individual['mid'] not in parent_ids:
                parent_ids.append(individual['mid'])

        if individual['fid'] is not None:
            if individual['fid'] not in parent_ids:
                parent_ids.append(individual['fid'])

    # Builds a list of all people who has a parent,
    # has a partner or is a parent.
    filtered = []
    for individual in individuals:
        has_parents = False
        has_partners = False
        is_parent = False
        # Checks their mother_id or father_id field is not empty.
        # If one of them is not, they are a child!
        if individual['mid'] is not None or individual['fid'] is not None:
            has_parents = True

        # Checks if their list of Partner IDs is not empty.
        # If it isn't, they have a partner connection
        if len(individual['pids']) > 0:
            has_partners = True

        # Checks if their ID is in parent_ids,
        # if it is, they have a child.
        if individual['id'] in parent_ids:
            is_parent = True

        # If any of the above checks return true,
        # they have at least one connection so are okay to display.
        if has_parents or has_partners or is_parent:
            filtered.append(individual)

    return filtered

# This function is called by the API
# to create the json response from a tree.
def run(tree):
    # Form the path to the database file by concatenating
    # the db_dir from config, the provided tree name, and appending .db
    db_path = DB_DIR + "/" + tree + ".db"
    # If the file does not exist, return None,
    # which the API interprets as 404 not found
    if not os.path.isfile(db_path):
        return None

    # Initialise a connection to the DB,
    # then run the above functions to collect
    # and filter the data before returning the JSON list to the API.
    db = Database(db_path)
    raw_individuals = get_individuals_data(db)
    jsonified = jsonify(raw_individuals)
    output = remove_isolated_individuals(jsonified)
    db.close()
    return output