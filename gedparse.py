from gedcom.parser import Parser

file_path = input("Enter the path to the GEDCOM file: ")

def parsefile(file_path):
    gedcom_parser = Parser()
    gedcom_parser.parse_file(file_path, False)
    elements = gedcom_parser.get_element_list()
    return elements

def get_names(elements):
    names = []
    for element in elements:
        if element.get_tag() == 'INDI':
            name = element.get_name()
            if name:
                first, last = name
                names.append(f"{first} {last}")
    return names

print(get_names(parsefile(file_path)))