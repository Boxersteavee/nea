# Import database and create connection
from types import new_class

# for each row in individuals table:
#    get id, conc(first_name,last_name), gender, birth_date, birth_place, death_date,
#    death_place, occupation, mother_id and father_id
# get data from families, assign partner IDs to who has one
# children list is not needed because familytree.js works that out on its own based on MID and FID

from database import Database
from config import get_cfg
import os

cfg = get_cfg()

def get_individuals_data(db):
    individuals = db.get_individuals()
    families = db.get_families()

    partner_map = {}
    for family in families:
        family_id, father_id, mother_id = family
        if father_id and mother_id:
            partner_map[father_id] = mother_id
            partner_map[mother_id] = father_id

    new_individuals = []
    for individual in individuals:
        id = individual[0]
        mother_id, father_id = db.get_individual_parents(id)
        partner_id = partner_map.get(id)
        individual_updated = individual + (mother_id, father_id, partner_id)
        new_individuals.append(individual_updated)

    return new_individuals

def jsonify(individuals):
    jsonified = []
    for i in individuals:
        if i[11] is not None:
            pids = [i[11]]
        else:
            pids = []
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


def run(tree):
    db_path = cfg['db_dir'] + "/" + tree + ".db"
    if not os.path.isfile(db_path):
        return 404
    db = Database(db_path)
    individuals = get_individuals_data(db)
    output = jsonify(individuals)
    return output

if __name__ == "__main__":
    output = run("HarrisWeb")
    print(output)