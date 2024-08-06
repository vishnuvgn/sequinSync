import requests, os, json, sys
from dotenv import load_dotenv, set_key
load_dotenv()


# stream_id = input("Enter the stream id: ")
SEQUIN_API_KEY=os.getenv('SEQUIN_API_KEY')
AIRTABLE_SEQUIN_SYNC_IDS = {}

def getCredential():
    url = "https://api.sequin.io/v1/credentials/0d5cf3d1-12a1-4795-a235-4e60c561493b"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    response = requests.request("GET", url, headers=headers)
    return response.text
    # credential = response.json()
    # return credential["properties"]

# SYNC FUNCTIONS

def listSyncs(stream_id=None):
    url = "https://api.sequin.io/v1/syncs"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    if stream_id == None:
        payload = {"stream_id": stream_id}
        response = requests.request("GET", url, headers=headers, json=payload)
    else:
        response = requests.request("GET", url, headers=headers)
    syncs = response.json()['data']
    sync_ids = []
    for sync in syncs:
        # print(sync['id'])
        sync_ids.append(sync['id'])
    print(sync_ids)
    return sync_ids

def createSync(stream_id):
    url = "https://api.sequin.io/v1/syncs"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}", "Content-Type": "application/json"}
    # file = open("airtable_sequin_sync_ids.json", "r")
    payload = {
        "provider" : "airtable",
        "stream_id": stream_id,
        "name": "Airtable Sync",
        "collection_ids": ['airtable:gcSyR6LfxbXo7iART4m1vcLu', 'airtable:eujMtBaNfSAsMvI2kF7F2nSi', 'airtable:NpJbSblRDdKgJosRbZSBCtve', 'airtable:NkmWXvTPqbybAkcE4IGm0dn6', 'airtable:G4imjysVDOOH5ofUbCWwXryx', 'airtable:f4eki9HRwU2imQWdDnFJV7rS', 'airtable:3X4IbiTRF9f03YjZakTicWEV', 'airtable:dVa6dpvaGo9saVuXuN3hrjxJ', 'airtable:Zj1i1yilXiqXjgJfTOtq3BdD', 'airtable:uG2YwEsUrEFVKk5KC4VnN8gh', 'airtable:eHqBtzxb7xC1pYcfrcZf3j1G', 'airtable:2szPY7DQDWxpueAyU4JT8OWQ', 'airtable:QRjRBK74dypRkjVNxSMSac29', 'airtable:NiSyJM9Od17YXRObYJwlzWr2', 'airtable:6su7Wmk9nQYYgiYtDZ82LXgi', 'airtable:EbxuQyg8nltoV4AaWf4ZzoFY', 'airtable:s9lQTLDSVZeTxaLOD5KU8jAP', 'airtable:GdI0mjcwUsdjxg49DBPU5yih', 'airtable:K71pCFJE5gmXYnNf81eBCJKa'],
        "credential_id" : "0d5cf3d1-12a1-4795-a235-4e60c561493b",
        "max_age_days" : 7
    }   

    response = requests.request("POST", url, headers=headers, json=payload)
    print(response.text)

    # file.close() airtable:97GJsnvkaOhooMCsDgBBYUd7

def deleteSync(sync_id):
    url = f"https://api.sequin.io/v1/syncs/{sync_id}"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}

    response = requests.request("DELETE", url, headers=headers)
    return response.status_code


def listCollections(credential_id="0d5cf3d1-12a1-4795-a235-4e60c561493b"):

    url = f"https://api.sequin.io/v1/collections/{credential_id}"

    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}

    response = requests.request("GET", url, headers=headers)
    data = response.json()

    # Write the data to a JSON file
    with open('collections.json', 'w') as file:
        json.dump(data, file, indent=4)
    return data

def getTableIds():
    # Load collections from the JSON file
    with open('collections.json', 'r') as file:
        collections = json.load(file)
    
    # Load AirTable fields from the JSON file
    with open('/Users/vishnuvenugopal/Downloads/sequinSync/AirTableFields.json', 'r') as file:
        ats = json.load(file).keys()
    
    # Extract table IDs from the collections
    tables = collections['data']
    tblIds = [tbl['id'] for tbl in tables if tbl['name'] in ats]
    
    print(tblIds)



# CONSUMER FUNCTIONS

def listConsumers():
    url = "https://api.sequin.io/v1/http-consumers"

    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    
    response = requests.request("GET", url, headers=headers)

    consumers = response.json()['data']
    # print(consumers)
    consumer_ids = []
    for consumer in consumers:
        # print(consumer['id'])
        consumer_ids.append(consumer['id'])
    print(consumer_ids)
    return consumer_ids

def createConsumer(stream_id):
    url = "https://api.sequin.io/v1/http-consumers"
    headers = {"Authorization" : f"Bearer {SEQUIN_API_KEY}", "Content-Type": "application/json"}
    payload = {"stream_id": stream_id}
    response = requests.request("POST", url, headers=headers, json=payload)
    consumer_id = response.json()['id']
    return consumer_id

def resetConsumer(consumer_id, stream_id):
    # url = f"https://api.sequin.io/v1/http-consumers/{consumer_id}/reset"
    # headers = {"Authorization" : f"Bearer {SEQUIN_API_KEY}", "Content-Type" : "application/json"}

    # response = requests.request("POST", url, headers=headers)
    # return response.text

    deleteConsumer(consumer_id)
    new_consumer_id = createConsumer(stream_id)
    set_key("../.env", "SEQUIN_CONSUMER_ID", new_consumer_id, quote_mode='never')
    print(new_consumer_id)
    return new_consumer_id

def deleteConsumer(consumer_id):
    url = f"https://api.sequin.io/v1/http-consumers/{consumer_id}"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    response = requests.request("DELETE", url, headers=headers)
    return response.status_code

# STREAM FUNCTIONS

def listStreams():
    url = "https://api.sequin.io/v1/streams"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    response = requests.request("GET", url, headers=headers)
    streams = response.json()
    print(streams)
    return streams

def createStream():
    url = "https://api.sequin.io/v1/streams"
    headers = {"Authorization" : f"Bearer {SEQUIN_API_KEY}", "Content-Type": "application/json"}
    payload = {"slug":"airtable-stream"}
    response = requests.request("POST", url, headers=headers, json=payload)
    stream_id = response.json()['data']['id']
    return stream_id


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 apiCalls.py <function_name> [arguments...]")
        sys.exit(1)

    function_name = sys.argv[1]
    arguments = sys.argv[2:]

    if function_name == "listStreams":
        listStreams()
    elif function_name == "listConsumers":
        listConsumers()
    elif function_name == "resetConsumer":
        resetConsumer(*arguments)
    elif function_name == "listSyncs":
        listSyncs(*arguments)