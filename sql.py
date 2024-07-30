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
    # foreignKeyCountMap = {} # dictionary of tables with the same number of foreign keys ex: {1: [table1, table2, table3], 2: [table4, table5]}
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
            
            # many to many relation list will NOT be put into sql table
            elif pgFieldName[-3:] == "M2M":
                continue
                

            pgFields.append(pgFieldName)
        
        # if fkCount in foreignKeyCountMap:
        #     foreignKeyCountMap[fkCount].append(pgTable)
        # else:
        #     foreignKeyCountMap[fkCount] = [pgTable]
        
        at_pg_map[airTable] = pgTable
        pg_table_fields[pgTable] = pgFields
        
        # these two columns are needed for the upsert (sequin). 
        # if i already put them in the json, i don't have to add them again
        
        # will always be the name of the table formatted as a field + _id
        
        pgTablePk = formatName.createPrimaryKey(pgTable)
        pg_table_fields[pgTable].append(pgTablePk)
        pg_table_fields[pgTable].append("updated_idx")


    jsonFunctions.overwrite_json("AirtablePGTableMap.json", at_pg_map) # airtable to pg table
    jsonFunctions.overwrite_json("PostgresTableFields.json", pg_table_fields)
    jsonFunctions.overwrite_json("PostgresForeignKeyMap.json", foreignKeyMap)
    # jsonFunctions.overwrite_json("ForeignKeyCountMap.json", foreignKeyCountMap)


PG_TABLE_FIELDS = json.load(open("PostgresTableFields.json"))
AIRTABLE_TO_SQL_MAP = json.load(open("AirtablePGTableMap.json"))
PG_FOREIGN_KEYS = json.load(open("PostgresForeignKeyMap.json"))

# fkTable: Represents the table that contains the foreign key.
# fkField: Represents the foreign key field in the table.
# fkReferenceTable: Represents the table that the foreign key references.
def createFKRelation(fkDict, fkTable, fkField, fkReferenceTable):
    pkOfReference = formatName.createPrimaryKey(fkReferenceTable)
    if fkTable not in fkDict:
        fkDict[fkTable] = {fkField : f'"{fkReferenceTable}"("{pkOfReference}")'}
    else:
        fkDict[fkTable][fkField] = f'"{fkReferenceTable}"("{pkOfReference}")'
     
# # with parameter because expecting to use it in a pipeline.py
# def sortTables(foreignKeyCountMap):
#     sortedTables = []
#     for count in sorted(foreignKeyCountMap.keys()):
#         sortedTables += foreignKeyCountMap[count]
#     return sortedTables


'''
input: string
output: string
fields and tables are surrounded by double quotes to preserve case sensitivity in pgdb
'''
def writeQuery(table, cols):
    pgTablePk = formatName.createPrimaryKey(table)
    columnsQuery = '('
    placeholders = '('
    numOfFields = len(cols)
    for i in range(numOfFields):
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

    # fieldnames / excluded query
    excludedQuery = ''
    first = True

    for i in range(numOfFields):
        col = cols[i]
        if col != pgTablePk:
            if not first:
                excludedQuery += ', '
            excludedQuery += f'"{col}" = excluded."{col}"'
            first = False
            

    # Prepare the SQL query
    query = '''
    INSERT INTO "'''+table+'''" '''+columnsQuery+'''
    VALUES '''+placeholders+'''
    ON CONFLICT ("'''+pgTablePk+'''") DO UPDATE
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
        pgTablePk = formatName.createPrimaryKey(table)
        prefix = ", "
        if i == 0:
            prefix = ""
    
        if field == "updated_idx":
            query += f'{prefix}"{field}" BIGINT'

        elif field == pgTablePk: 
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

    
    table1_pk = formatName.createPrimaryKey(table1)
    table2_pk = formatName.createPrimaryKey(table2)

    junction_table_name = formatName.createJunctionTableName(table1, table2)

    
    query = f'''
    CREATE TABLE IF NOT EXISTS "{junction_table_name}" (
        "{table1_pk}" TEXT,
        "{table2_pk}" TEXT,
        PRIMARY KEY ("{table1_pk}", "{table2_pk}"),
        FOREIGN KEY ("{table1_pk}") REFERENCES "{table1}"("{table1_pk}") ON DELETE CASCADE,
        FOREIGN KEY ("{table2_pk}") REFERENCES "{table2}"("{table2_pk}") ON DELETE CASCADE
    );
    '''
    
    cur.execute(f"SET search_path TO {PG_SCHEMA}")
    cur.execute(query)
    print(f'created {junction_table_name}')
    conn.commit()
    cur.close()
    conn.close()

def populateJunctionTable(table1, table2, table1Id, table2Ids):
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cur = conn.cursor()
    junction_table_name = formatName.createJunctionTableName(table1, table2)
    table1_pk = formatName.createPrimaryKey(table1)
    table2_pk = formatName.createPrimaryKey(table2)

    for table2Id in table2Ids:

        query = f'''
        INSERT INTO "{junction_table_name}" ("{table1_pk}", "{table2_pk}")
        VALUES ('{table1Id}', '{table2Id}')
        '''
        
        cur.execute(f"SET search_path TO {PG_SCHEMA}")
        cur.execute(query)

    print(f'populated {junction_table_name}')
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


def unlinkTables():
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
            constraintName = (tbl+"_"+field).lower() # this is the name of the constraint,
            print(f'constraintName = {constraintName}')
            query = f'ALTER TABLE "{tbl}" DROP CONSTRAINT {constraintName};'
            cur.execute(query)

    conn.commit()
    cur.close()
    conn.close()

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
            constraintName = (tbl+"_"+field).lower() # this is the name of the constraint,
            print(f'constraintName = {constraintName}')
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