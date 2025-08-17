import ged2sql

def main():
    gedcom_path = input("Enter the path to the GEDCOM file: ")
    ged2sql.run(gedcom_path) # Execute "run" function from ged2sql module with the provided path.

main()