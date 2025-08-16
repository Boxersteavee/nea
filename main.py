import ged2sql
DB_PATH = "family.db"

def main():
    gedcom_path = input("Enter the path to the GEDCOM file: ")
    elements = ged2sql.ParseFile(gedcom_path)

    ged2sql.TestSurnames(elements)

    ged2sql.CreateDB(DB_PATH, elements)
    print(f"Database created at {DB_PATH}.")

main()