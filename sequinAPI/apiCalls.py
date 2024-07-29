import requests, os, json
from dotenv import load_dotenv
load_dotenv()


# stream_id = input("Enter the stream id: ")
SEQUIN_API_KEY=os.getenv('SEQUIN_API_KEY')
AIRTABLE_SEQUIN_SYNC_IDS = {}

def getCredential():
    url = "https://api.sequin.io/v1/credentials/0d5cf3d1-12a1-4795-a235-4e60c561493b"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    response = requests.request("GET", url, headers=headers)
    credential = response.json()
    return credential["properties"]

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
    return sync_ids

def createSync(stream_id):
    url = "https://api.sequin.io/v1/syncs"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}", "Content-Type": "application/json"}
    file = open("airtable_sequin_sync_ids.json", "r")
    payload = {
        "stream_id": stream_id,
        "name": "Airtable Sync",
        "collection_ids": json.loads(file),
        "credential": {
            "properties": getCredential()
        } 
    }

    response = requests.request("POST", url, headers=headers, json=payload)
    print(response.status_code)

    file.close()

def deleteSync(sync_id):
    url = f"https://api.sequin.io/v1/syncs/{sync_id}"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}

    response = requests.request("DELETE", url, headers=headers)
    return response.status_code

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
    return consumer_ids

def createConsumer(stream_id):
    url = "https://api.sequin.io/v1/http-consumers"
    headers = {"Authorization" : f"Bearer {SEQUIN_API_KEY}", "Content-Type": "application/json"}
    payload = {"stream_id": stream_id}
    response = requests.request("POST", url, headers=headers, json=payload)
    consumer_id = response.json()['id']
    return consumer_id

def resetConsumer(consumer_id, stream_id):
    deleteConsumer(consumer_id)
    new_consumer_id = createConsumer(stream_id)
    return new_consumer_id
    
    
    # url = f"https://api.sequin.io/v1/http-consumers/{consumer_id}/reset"
    # headers = {"Authorization" : f"Bearer {SEQUIN_API_KEY}", "Content-Type" : "application/json"}

    # response = requests.request("POST", url, headers=headers)
    # return response.text

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

def createStream():
    url = "https://api.sequin.io/v1/streams"
    headers = {"Authorization" : f"Bearer {SEQUIN_API_KEY}", "Content-Type": "application/json"}
    payload = {"slug":"airtable-stream"}
    response = requests.request("POST", url, headers=headers, json=payload)
    stream_id = response.json()['data']['id']
    return stream_id