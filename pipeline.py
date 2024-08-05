import airtables, sql, formatName
import time, json, logging, os, requests
logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
import psycopg2

load_dotenv()

PG_HOST=os.getenv('PG_HOST')
PG_DATABASE=os.getenv('PG_DATABASE')
PG_USER=os.getenv('PG_USER')
PG_PASSWORD=os.getenv('PG_PASSWORD')
PG_SCHEMA=os.getenv('PG_SCHEMA')
SEQUIN_API_KEY=os.getenv('SEQUIN_API_KEY')
SEQUIN_CONSUMER_ID=os.getenv('SEQUIN_CONSUMER_ID')

# Establish a connection to the PostgreSQL database
conn = psycopg2.connect(
    host=PG_HOST,
    database=PG_DATABASE,
    user=PG_USER,
    password=PG_PASSWORD
)

# Create a cursor object
cur = conn.cursor()

# TODO: will write explanation. this is important
# {
#     (memberTable, skillTable) : {
#         "mem1" : ["skill1", "skill2"]
#     }
# }

M2M_MAPS = {}
# M2M_POPULATED = False
WAIT = 0



def upsert_record(record):
    print(record)
    
    # think more about the implication of this "ignore" logic
    # was a short term fix but could be a potential solution
    if record["collection_id"] not in airtables.TABLE_SEQUIN_SYNC_IDS:
        return
    
    # keys of the mapping table have to be the records expected in the sync
    airtableTable = airtables.TABLE_SEQUIN_SYNC_IDS[record["collection_id"]] 
    # if airtableTable == "Squadrons":
    #     print("Squadrons")
    #     with open("error.txt", "w") as f:
    #         f.write(f'Squadrons: {record}')
    # print(airtableTable)
    airtable2sqlMap = json.load(open("AirtablePGTableMap.json"))
    
    sqlTable = airtable2sqlMap[airtableTable]
    
    # these two are inputed in every table
    upstream_id = record["upstream_id"] # (string) primary key, record key in airtable
    updated_idx = record["updated_idx"] # bigint

    airtableTableFieldsMap = json.load(open("AirTableFields.json"))
    airtableFields = airtableTableFieldsMap[airtableTable]

    fieldsSent = record["data"]["fields"].keys()
    # print(fieldsSent)
    
    pgTablePk = formatName.createPrimaryKey(sqlTable) # upstream_id val will go here
    PGCols = [pgTablePk, "updated_idx"]

    values = (upstream_id, updated_idx)
    for field in fieldsSent:
        # print(f'field = {field}')
        if field in airtableFields:

            value = record["data"]["fields"][field]
            M2M_flag = False

            if field[-3:] == "M2M": # value is a list
                M2M_flag = True
                print(f'found M2M: {field}')
                refTable = field[:-4] # has to be spelled right in airtable
                junctionTables = (sqlTable, formatName.changeName(refTable, False)) # tuple is key in dict
                if junctionTables not in M2M_MAPS:
                    M2M_MAPS[junctionTables] = {
                        upstream_id : value # will be list of rec ids for the ref table
                    }
                else:
                    M2M_MAPS[junctionTables][upstream_id] = value

                print(value)

                
            if type(value) == list and len(value) == 1:
                value = value[0]
            elif type(value) == dict:
                with open("error.txt", "w") as f:
                    f.write(f'error {field}: {value}')
                value = ""

            if M2M_flag == False: # M2M not a field in pg sql table. will be handled in the junction table which can only be populated after all tables populated
                values += (value, )

                PGField = formatName.changeName(field, True)
                # print(f'PGField = {PGField}')
                PGCols.append(PGField)
            
    # print(f'PGCols = {PGCols}')
    # print(f'values = {values}')
    
    query = sql.writeQuery(sqlTable, PGCols)
    
    cur.execute(f"SET search_path TO {PG_SCHEMA}")
    cur.execute(query, values)
    conn.commit()

def run():
    consumer_id = SEQUIN_CONSUMER_ID  
    while True:
        try:
            response = pull_messages(consumer_id)
            messages = response["data"]
            info = response["info"]
            logging.info(f"Pulled {len(messages)} messages")

            # First, process the messages and verify success
            process_messages(messages)

            # Then, acknowledge the messages
            ack_messages(consumer_id, [msg["ack_token"] for msg in messages])

            # If there are no more messages to pull, wait for 5 seconds before trying again
            if not has_more(info):
                logging.info("No more messages to pull")#, sleeping for 5 seconds")
                # global M2M_POPULATED, WAIT
                global WAIT, M2M_MAPS
                # if M2M_POPULATED == False and WAIT >= 15:
                if WAIT >= 2:
                    # junctionTables is the tuple key for the dict
                    for junctionTables, recordMap in list(M2M_MAPS.items()):
                        # tbl1Id is the upstream_id of the record in the main table
                        # tbl2Ids is a list of upstream_ids of the records in the ref table
                        for tbl1Id, tbl2Ids in recordMap.items():
                            tbl1, tbl2 = junctionTables
                            # EX: "Members", "Skills", "mem1", ["skill1", "skill2"] (these will obviously be real upstream ids)
                            sql.populateJunctionTable(tbl1, tbl2, tbl1Id, tbl2Ids)
                        
                        del M2M_MAPS[junctionTables]
                    # M2M_POPULATED = True
                else:
                    WAIT += 1
                    logging.info("sleeping for 5 seconds")

                time.sleep(5)

        except Exception as e:
            logging.error(f"Failed to pull messages: {e}")
            # Wait for 5 seconds before trying again
            time.sleep(5)

def pull_messages(consumer_id):
    url = f"https://api.sequin.io/v1/http-consumers/{consumer_id}/next"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    params = {"batch_size": 20}

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    return response.json()

def process_messages(messages):
    records = []
    for message in messages:
        records.append(message["record"])
    upsert_records(records)
        
def ack_messages(consumer_id, ack_tokens):
    if not ack_tokens:
        return

    url = f"https://api.sequin.io/v1/http-consumers/{consumer_id}/ack"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    data = {"ack_tokens": ack_tokens}

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

def has_more(info):
    return info.get("num_pending", 0) > 0

def upsert_records(records):
    for record in records:
        upsert_record(record)

run()

# Close the cursor and connection
cur.close()
conn.close()
