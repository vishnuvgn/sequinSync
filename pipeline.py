import airtables, sql

import time
import logging
logging.basicConfig(level=logging.INFO)
import requests

from dotenv import load_dotenv
import os
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

def upsert_record(record):
    
    # think more about the implication of this "ignore" logic
    # was a short term fix but could be a potential solution
    if record["collection_id"] not in airtables.TABLE_SEQUIN_SYNC_IDS:
        return
    
    # keys of the mapping table have to be the records expected in the sync
    airtableTable = airtables.TABLE_SEQUIN_SYNC_IDS[record["collection_id"]] 
    # print(airtableTable)
    sqlTable = sql.AIRTABLE_TO_SQL_MAP[airtableTable]
    
    # these two are inputed in every table
    upstream_id = record["upstream_id"] # (string) primary key, record key in airtable
    updated_idx = record["updated_idx"] # bigint

    airtableFields = airtables.AT_TABLE_FIELDS[airtableTable]
    # fields = [upstream_id, updated_idx] + [record["data"]["fields"][field] if field in record["data"]["fields"] else "" for field in airtableFields]
    
    
    # look up fields are always sent as individual json objects in list : (['a', 'b', ['rec...']])
    # have to extract the actual text from the one element list
    fields = [upstream_id, updated_idx]
    for field in airtableFields:
        if field in record["data"]["fields"]:
            if type(record["data"]["fields"][field]) == list and len(record["data"]["fields"][field]) == 1:
                fields.append(record["data"]["fields"][field][0])
            # psycopg2 doesn't like dictionaries --> the only dictionary passed in right now is an error message. Have to think about this a bit more if we will ever pass a dict.
            elif type(record["data"]["fields"][field]) == dict:
                fields.append("")

            else:
                fields.append(record["data"]["fields"][field])
        else:
            fields.append("")
    
    # print(f'fields = {fields}')




    
    
    query = sql.writeQuery(sqlTable)
    # print(f'query = {query}')
    
    cur.execute(f"SET search_path TO {PG_SCHEMA}")

    # Execute the query with the record data
    cur.execute(query, tuple(fields))

    # Commit the transaction
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
                logging.info("No more messages to pull, sleeping for 5 seconds")
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

# 11:24.79