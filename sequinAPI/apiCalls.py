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

# for now, it will only return the one sync id because there is only one sync in that stream
def getSyncs(stream_id):
    url = "https://api.sequin.io/v1/syncs"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    payload = {"stream_id": stream_id}
    response = requests.request("GET", url, headers=headers, json=payload)

    sync = response.json()
    airtable_sequin_sync_ids = sync['data'][0]['collection_ids']
    sync_id = sync['data'][0]['id']

    return airtable_sequin_sync_ids, sync_id

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

def getConsumer(stream_id):
    url = "https://api.sequin.io/v1/http-consumers"

    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    payload = {"stream_id": stream_id}

    response = requests.request("GET", url, headers=headers, json=payload)

    consumer = response.json()
    consumer_id = consumer['data'][0]['id']

    return consumer_id

def createConsumer(stream_id):
    url = "https://api.sequin.io/v1/http-consumers"
    headers = {"Authorization" : f"Bearer {SEQUIN_API_KEY}", "Content-Type": "application/json"}
    payload = {"stream_id": stream_id}
    response = requests.request("POST", url, headers=headers, json=payload)
    consumer_id = response.json()['data']['id']
    return consumer_id


def deleteConsumer(consumer_id):
    url = f"https://api.sequin.io/v1/http-consumers/{consumer_id}"
    headers = {"Authorization": f"Bearer {SEQUIN_API_KEY}"}
    response = requests.request("DELETE", url, headers=headers)
    return response.status_code

def deleteStream(stream_id):
    airtable_sequin_sync_ids, sync_id = getSyncs(stream_id)
    print(airtable_sequin_sync_ids)
    with open("airtable_sequin_sync_ids.json", 'w') as f:
        json.dump(airtable_sequin_sync_ids, f)

    consumer_id = getConsumer(stream_id)

    deleteSync(sync_id)
    deleteConsumer(consumer_id)

    url = f"https://api.sequin.io/v1/streams/{stream_id}"
    headers = {"Authorization" : f"Bearer {SEQUIN_API_KEY}"}

    response = requests.request("DELETE", url, headers=headers)
    return response.status_code

def createStream():
    url = "https://api.sequin.io/v1/streams"
    headers = {"Authorization" : f"Bearer {SEQUIN_API_KEY}", "Content-Type": "application/json"}
    payload = {"slug":"airtable-stream"}
    response = requests.request("POST", url, headers=headers, json=payload)
    stream_id = response.json()['data']['id']
    return stream_id