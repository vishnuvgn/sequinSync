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
    foreignKeyCountMap = {} # dictionary of tables with the same number of foreign keys ex: {1: [table1, table2, table3], 2: [table4, table5]}
    foreignKeyMap = {} 
    at_pg_map = {}
    pg_table_fields = {}
    for airTable, airFields in tables.items():
        pgFields = []
        pgTable = formatName.changeName(airTable, False)
        fkCount = 0
        for field in airFields:

            pgFieldName = formatName.changeName(field, True)
            
            if pgFieldName[-2:] == "Fk":
# NOTE: SUPER IMPORTANT -- the foreign key referece field MUST 
# contain the EXACT spelling of the table it references I am NOT doing any error
# checking for this. This just needs to be done right in airtable.
           
            # -3 because there will be an undersore btw the table title and the letters Fk
                fkReferenceTable = formatName.changeName(field[:-3], False) 
                createFKRelation(foreignKeyMap, pgTable, pgFieldName, fkReferenceTable)

                # count how many foreign keys there are
                fkCount += 1

            pgFields.append(pgFieldName)
        
        if fkCount in foreignKeyCountMap:
            foreignKeyCountMap[fkCount].append(pgTable)
        else:
            foreignKeyCountMap[fkCount] = [pgTable]
        
        at_pg_map[airTable] = pgTable
        pg_table_fields[pgTable] = pgFields
        
        # these two columns are needed for the upsert (sequin). 
        # if i already put them in the json, i don't have to add them again
        pg_table_fields[pgTable].append("upstream_id")
        pg_table_fields[pgTable].append("updated_idx")


    jsonFunctions.overwrite_json("AirtablePGTableMap.json", at_pg_map) # airtable to pg table
    jsonFunctions.overwrite_json("PostgresTableFields.json", pg_table_fields)
    jsonFunctions.overwrite_json("PostgresForeignKeyMap.json", foreignKeyMap)
    jsonFunctions.overwrite_json("ForeignKeyCountMap.json", foreignKeyCountMap)


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
     
# with parameter because expecting to use it in a pipeline.py
def sortTables(foreignKeyCountMap):
    sortedTables = []
    for count in sorted(foreignKeyCountMap.keys()):
        sortedTables += foreignKeyCountMap[count]
    return sortedTables



'''
input: string
output: string
fields and tables are surrounded by double quotes to preserve case sensitivity in pgdb
'''
def writeQuery(table, cols):
    
    # columnsQuery = '(upstream_id, updated_idx'
    # numOfFields = len(PG_TABLE_FIELDS[table])
    
    columnsQuery = '('
    placeholders = '('
    numOfFields = len(cols)
    for i in range(numOfFields):
        # field = PG_TABLE_FIELDS[table][i]
        col = cols[i]
        if i == numOfFields - 1: # last field
            columnsQuery += f', "{col}")'
            placeholders += '%s)'
        elif i == 0: # first field
            columnsQuery += f'"{col}"'
            placeholders += '%s, '
        else:
            columnsQuery += f', "{col}"'
            placeholders += '%s, '

    # numOfCols = numOfFields + 2 # plus two because of upstream_id and updated_idx

    
    # for i in range(numOfFields):
    #     if i == numOfFields - 1: # last col
    #         placeholders += '%s)'
    #     else:
    #         placeholders += '%s, '


    # fieldnames / excluded query
    excludedQuery = ''
    first = True

    for i in range(numOfFields):
        col = cols[i]
        if col != "upstream_id":
            if not first:
                excludedQuery += ', '
            excludedQuery += f'"{col}" = excluded."{col}"'
            first = False
            

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
            query += f'{prefix}"{field}" TEXT'# PRIMARY KEY'

        # elif field[-2:] == "Fk":
        #     query += f'{prefix}"{field}" TEXT, '
        #     query += f'FOREIGN KEY ("{field}") REFERENCES {PG_FOREIGN_KEYS[table][field]}'

        elif field == "updated_idx":
            query += f'{prefix}"{field}" BIGINT'

        elif field == "upstream_id":
            query += f'{prefix}"{field}" TEXT PRIMARY KEY'

        else:
            query += f'{prefix}"{field}" TEXT'
    
    query += ');'
    
    cur.execute(f"SET search_path TO {PG_SCHEMA}")
    cur.execute(query)
    print(f'created {table}')
    conn.commit()
    cur.close()
    conn.close()

def createJunctionTable(table1, table2):
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cur = conn.cursor()

    table1_pk = formatName.changeName(table1, False)  # Primary key for table1
    table2_pk = formatName.changeName(table2, False)  # Primary key for table2

    junction_table_name = f"{table1}_{table2}"

    query = f'''
    CREATE TABLE IF NOT EXISTS "{junction_table_name}" (
        "{table1_pk}" TEXT,
        "{table2_pk}" TEXT,
        PRIMARY KEY ("{table1_pk}", "{table2_pk}"),
        FOREIGN KEY ("{table1_pk}") REFERENCES "{table1}"("recordid_Pk") ON DELETE CASCADE,
        FOREIGN KEY ("{table2_pk}") REFERENCES "{table2}"("recordid_Pk") ON DELETE CASCADE
    );
    '''
    
    cur.execute(f"SET search_path TO {PG_SCHEMA}")
    cur.execute(query)
    print(f'created {table1}{table2}')
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
    # foreignKeyCountMap = json.load(open("ForeignKeyCountMap.json"))
    # tablesQueue = sortTables(foreignKeyCountMap)
    # tablesEntered = set()
    # while len(tablesQueue) != 0:
    #     # print(f'tablesEntered = {tablesEntered}')
    #     tbl = tablesQueue.pop(0) # deque
    #     # print(tbl)
    #     # print(f'table = {tbl}')
    #     if tbl in PG_FOREIGN_KEYS: # if there are foreign keys
    #         boolFlag = True
    #         for foreignField in PG_FOREIGN_KEYS[tbl].keys():
    #             refTable = foreignField[:-3].upper()
    #             # print(f'refTable = {refTable}')

    #             if refTable not in tablesEntered:
    #                 boolFlag = False
    #                 break
    #         if boolFlag == True:
    #             createTable(tbl)
    #             tablesEntered.add(tbl.upper())
    #         else:
    #             tablesQueue.append(tbl)
                    
        
    #     else: # if there are no foreign keys
    #         createTable(tbl)
    #         tablesEntered.add(tbl.upper())



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

def restart():
    deleteTables()
    createTables()