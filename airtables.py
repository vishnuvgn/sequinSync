import extractFields, jsonFunctions
import os, json


TABLE_SEQUIN_SYNC_IDS = {
    "airtable:2szPY7DQDWxpueAyU4JT8OWQ": "Vehicle Equipment",
    "airtable:3X4IbiTRF9f03YjZakTicWEV": "Squadrons",
    "airtable:6su7Wmk9nQYYgiYtDZ82LXgi": "Roles",
    "airtable:EbxuQyg8nltoV4AaWf4ZzoFY": "Rifle Training",
    "airtable:G4imjysVDOOH5ofUbCWwXryx": "M4 Training",
    "airtable:K71pCFJE5gmXYnNf81eBCJKa": "Requirements",
    "airtable:NiSyJM9Od17YXRObYJwlzWr2": "Skills",
    "airtable:NkmWXvTPqbybAkcE4IGm0dn6": "M249 Training",
    "airtable:NpJbSblRDdKgJosRbZSBCtve": "AppointmentType",
    "airtable:QRjRBK74dypRkjVNxSMSac29": "Slots",
    "airtable:Zj1i1yilXiqXjgJfTOtq3BdD": "M240 Training",
    "airtable:dVa6dpvaGo9saVuXuN3hrjxJ": "Communications Equipment",
    "airtable:eHqBtzxb7xC1pYcfrcZf3j1G": "Aircraft Equipment",
    "airtable:eujMtBaNfSAsMvI2kF7F2nSi": "Members",
    "airtable:f4eki9HRwU2imQWdDnFJV7rS": "Grenade Training",
    "airtable:gcSyR6LfxbXo7iART4m1vcLu": "Maintenance Equipment",
    "airtable:s9lQTLDSVZeTxaLOD5KU8jAP": "Jobs",
    "airtable:uG2YwEsUrEFVKk5KC4VnN8gh": "Groups"
}

'''
Fields in use for each table mentioned above
'''

# human input -- all views are titled Sync Fields
TABLE_URLS = {
  "Members" : "https://airtable.com/app03GWdFHFCFlo9u/tblyIeCi2GxlIAG49/viwRpq5VEnQboWjJV?blocks=hide", 
  "Requirements" : "https://airtable.com/app03GWdFHFCFlo9u/tblekjtTS5jgzlaOf/viwzYSqVBFQHj3VI0?blocks=hide",
  "Squadrons" : "https://airtable.com/app03GWdFHFCFlo9u/tblb2XprFTBTuaFxs/viwMoYR6NnrmBhXZ2?blocks=hide",
  "Groups" : "https://airtable.com/app03GWdFHFCFlo9u/tbl9bBfgnpZ4TayI2/viw7CSt71Lxw2FdIH?blocks=hide",
  "AppointmentType" : "https://airtable.com/app03GWdFHFCFlo9u/tblNbT8qOYf025FeM/viw7isa0MUmN30NsV?blocks=hide",
  "Rifle Training" : "https://airtable.com/app03GWdFHFCFlo9u/tblO5KfZ3ftqs5YDK/viwUqYPkuuCIAw8aW?blocks=hide",
  "M249 Training" : "https://airtable.com/app03GWdFHFCFlo9u/tblJruRooZJFuEZCD/viwadAzHeXXZjgbrO?blocks=hide",
  "M4 Training" : "https://airtable.com/app03GWdFHFCFlo9u/tblUpb4DjsyBpurUg/viwYfTfgDGIdXSj6a?blocks=hide",
  "Grenade Training" : "https://airtable.com/app03GWdFHFCFlo9u/tbleavKIXnAlF8OrK/viwW1P53dZZmho8VX?blocks=hide",
  "M240 Training" : "https://airtable.com/app03GWdFHFCFlo9u/tbli4bZDcPs7mIbnZ/viwWu9osY2YvUACvV?blocks=hide",
  "Roles" : "https://airtable.com/app03GWdFHFCFlo9u/tblysjQlQLUIATTMe/viwRyQhJYgkvDLqGy?blocks=hide",
  "Jobs" : "https://airtable.com/app03GWdFHFCFlo9u/tblrEzbWHpayymtsb/viwIQcSMEOW8FQK4s?blocks=hide",
  "Vehicle Equipment" : "https://airtable.com/app03GWdFHFCFlo9u/tbldnEsi6tuEtcvbp/viwu3EELPSho0KBoO?blocks=hide",
  "Maintenance Equipment" : "https://airtable.com/app03GWdFHFCFlo9u/tblgkK8NOV6MJI5JN/viwew83ONwC1miy3y?blocks=hide",
  "Communications Equipment" : "https://airtable.com/app03GWdFHFCFlo9u/tblSEx6VFXXwqSSL0/viw9DgmGD9xKlHN3n?blocks=hide",
  "Aircraft Equipment" : "https://airtable.com/app03GWdFHFCFlo9u/tblUoJWnEcObkoOIY/viwj2mUKBVJ1XMohQ?blocks=hide",
  "Slots" : "https://airtable.com/app03GWdFHFCFlo9u/tblcOInOa2VmKBTO4/viwGThlqYZNK6V4BX?blocks=hide",
  "Skills" : "https://airtable.com/app03GWdFHFCFlo9u/tblUczxW6cEIp6Hv1/viwU9EtFwgzGHSzKA?blocks=hide"
}


def fillTableFields(overwrite=True): 
    # selenium can be stupid sometimes... works sometimes, doesn't work other times
    completed = False
    while completed == False:
        try: 
            tableFields = extractFields.compileFieldList(TABLE_URLS)
        except:
            print("will try again")
        else:
            completed = True

    if overwrite:
        jsonFunctions.overwrite_json("AirTableFields.json", tableFields)
    else:
        for table, fields in tableFields.items():
            jsonFunctions.append_to_json("AirTableFields.json", table, fields)


AT_TABLE_FIELDS = json.load(open("AirTableFields.json"))