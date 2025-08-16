from gedcom.parser import Parser
import sqlite3

def ParseFile(Gedcom_Path):
    gedcom_parser = Parser()
    gedcom_parser.parse_file(Gedcom_Path, False)
    elements = gedcom_parser.get_element_list()
    return elements

# Other plans for file:
# parsefile runs, gets all the data
# Creates SQLite3 database and adds all of the data from the .ged file

def CreateDB(elements):