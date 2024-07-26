import psycopg2
from dotenv import load_dotenv
import os, json
import formatName, jsonFunctions, airtables # i dont like this structure all that much...

load_dotenv()
PG_HOST=os.getenv('PG_HOST')
PG_DATABASE=os.getenv('PG_DATABASE')
PG_USER=os.getenv('PG_USER')
PG_PASSWORD=os.getenv('PG_PASSWORD')
PG_SCHEMA=os.getenv('PG_SCHEMA')

def mapAirtableToSQL(tables = airtables.AT_TABLE_FIELDS): 
    foreignKeyMap = {} 
    at_pg_map = {}
    pg_table_fields = {}
    for airTable, airFields in tables.items():
        pgFields = []
        pgTable = formatName.changeName(airTable, False)
        for field in airFields:

            pgFieldName = formatName.changeName(field, True)
            
            if pgFieldName[-2:] == "Fk":
# NOTE: SUPER IMPORTANT -- the foreign key referece field MUST 
# contain the EXACT spelling of the table it references I am NOT doing any error
# checking for this. This just needs to be done right in airtable.
           
            # -3 because there will be an undersore btw the table title and the letters Fk
                fkReferenceTable = formatName.changeName(field[:-3], False) 
                createFKRelation(foreignKeyMap, pgTable, pgFieldName, fkReferenceTable)

            pgFields.append(pgFieldName)
        
        at_pg_map[airTable] = pgTable
        pg_table_fields[pgTable] = pgFields
        
        # these two columns are needed for the upsert (sequin). 
        # if i already put them in the json, i don't have to add them again
        pg_table_fields[pgTable].append("upstream_id")
        pg_table_fields[pgTable].append("updated_idx")


    jsonFunctions.overwrite_json("AirtablePGTableMap.json", at_pg_map) # airtable to pg table
    jsonFunctions.overwrite_json("PostgresTableFields.json", pg_table_fields)
    jsonFunctions.overwrite_json("PostgresForeignKeyMap.json", foreignKeyMap)


PG_TABLE_FIELDS = json.load(open("PostgresTableFields.json"))
AIRTABLE_TO_SQL_MAP = json.load(open("AirtablePGTableMap.json"))
PG_FOREIGN_KEYS = json.load(open("PostgresForeignKeyMap.json"))

# fkTable: Represents the table that contains the foreign key.
# fkField: Represents the foreign key field in the table.
# fkReferenceTable: Represents the table that the foreign key references.
def createFKRelation(fkDict, fkTable, fkField, fkReferenceTable):
    if fkTable not in fkDict:
        fkDict[fkTable] = {fkField : f'"{fkReferenceTable}"("recordid_Pk")'}
    else:
        fkDict[fkTable][fkField] = f'"{fkReferenceTable}"("recordid_Pk")'
     

'''
input: string
output: string
fields and tables are surrounded by double quotes to preserve case sensitivity in pgdb
'''
def writeQuery(table):
    
    columnsQuery = '(upstream_id, updated_idx'
    numOfFields = len(PG_TABLE_FIELDS[table])

    for i in range(numOfFields):
        field = PG_TABLE_FIELDS[table][i]
        if i == numOfFields - 1: # last field
            columnsQuery += f', "{field}")'
        else:
            columnsQuery += f', "{field}"'

    numOfCols = numOfFields + 2 # plus two because of upstream_id and updated_idx

    placeholders = '('
    for i in range(numOfCols):
        if i == numOfCols - 1: # last col
            placeholders += '%s)'
        else:
            placeholders += '%s, '


    # fieldnames / excluded query
    excludedQuery = '"updated_idx" = excluded."updated_idx"'
    for i in range(numOfFields):
        field = PG_TABLE_FIELDS[table][i]
        excludedQuery += f', "{field}" = excluded."{field}"'
        

    # Prepare the SQL query
    query = '''
    INSERT INTO "'''+table+'''" '''+columnsQuery+'''
    VALUES '''+placeholders+'''
    ON CONFLICT (upstream_id) DO UPDATE
    SET '''+excludedQuery+'''
    WHERE "'''+table+'''"."updated_idx" <= excluded."updated_idx";
    '''

    return query
    
def createTable(table):
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cur = conn.cursor()

    query = f'CREATE TABLE IF NOT EXISTS "{table}" ('
    
    for i in range(len(PG_TABLE_FIELDS[table])):
        field = PG_TABLE_FIELDS[table][i]
        prefix = ", "
        if i == 0:
            prefix = ""
    
    # if the last two letters of the field is Pk, then it is a primary key
        if field[-2:] == "Pk":
            query += f'{prefix}"{field}" TEXT PRIMARY KEY'
        
        elif field == "updated_idx":
            query += f'{prefix}"{field}" BIGINT'

        else:
            query += f'{prefix}"{field}" TEXT'
    
    query += ');'
    
    cur.execute(f"SET search_path TO {PG_SCHEMA}")
    cur.execute(query)
    print(f'created {table}')
    conn.commit()
    cur.close()
    conn.close()

# be fucking careful
def deleteTable(table):
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cur = conn.cursor()

    query = f'DROP TABLE IF EXISTS "{table}" CASCADE'
    
    cur.execute(f"SET search_path TO {PG_SCHEMA}")
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()
    print(f'deleted {table}') 
    
def clearTable(table):
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cur = conn.cursor()

    query = f'DELETE FROM "{table}"'
    
    cur.execute(f"SET search_path TO {PG_SCHEMA}")
    cur.execute(query)
    conn.commit()
    cur.close()
    conn.close()

def createTables():
    tbls = list(PG_TABLE_FIELDS.keys())
    for tbl in tbls:
        createTable(tbl)

def linkTables():
    conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DATABASE,
            user=PG_USER,
            password=PG_PASSWORD
        )
    cur = conn.cursor()
    cur.execute(f"SET search_path TO {PG_SCHEMA}")
    for tbl in PG_FOREIGN_KEYS:
        for field, reference in PG_FOREIGN_KEYS[tbl].items():
            constraintName = tbl+"_"+field
            # print(f'constraintName = {constraintName}')
            query = f'ALTER TABLE "{tbl}" ADD CONSTRAINT {constraintName} FOREIGN KEY ("{field}") REFERENCES {reference};'
            # print(query)
            cur.execute(query)
    
    conn.commit()
    cur.close()
    conn.close()
        
def deleteTables():
    print(f'DB: {PG_DATABASE}')
    validation = input("Are you sure this is the database you want to clear (Y/n): ")
    if validation == "y" or validation == "Y":

        tbls = list(PG_TABLE_FIELDS.keys())
        for tbl in tbls:
            deleteTable(tbl)
    else:
        return "aborted"

def clearTables():
    tbls = list(PG_TABLE_FIELDS.keys())
    for tbl in tbls:
        clearTable(tbl)