import re

def changeName(input_string, isField: bool):
    # Remove text within parentheses
    input_string = re.sub(r'\([^)]*\)', '', input_string)
    
    # Convert to CapitalCase
    input_string = input_string.title()
    
    # Remove leading and trailing whitespace
    input_string = input_string.strip()
    
    # Replace spaces with empty string
    input_string = input_string.replace(" ", "")


    if isField == True:
        input_string = input_string[0].lower() + input_string[1:]

    
    return input_string

def createJunctionTableName(table1, table2):
    return f'{table1}_{table2}'

def createPrimaryKey(table):
    return f'{changeName(table, True)}_id'
