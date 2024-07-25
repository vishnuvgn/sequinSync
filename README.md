# sequinSync

Roadmap rq:

1) add table links to airtables.py
2) run the web scraper (fillTableFields) to get each table's fields
3) go to sql.py and run mapAirtableToSQL
4) if you want a complete restart, delete the tables and then create them. else, just run the createTbls() func
it will create the newly added tables only
5) run pipeline.py once you've updated the sync on sequin -- make sure to update the TABLE_SEQUIN_SYNC_IDS in airtables.py









## Description:
This project utilizes Sequin, a data synchronization tool, to sync data from Airtable to a Postgres database. Sequin provides a seamless integration between the two platforms, allowing for efficient and automated data transfer.

## Python Installations
`pip3 install python-dotenv`

`pip3 install psycopg2-binary`    

Note: use `pip3` if on Mac and running python3. If on windows `pip`

### SQL Important Columns

All the fields listed above which make up the columns in the Postgres database are of type TEXT. This is subject to change, however.

There are two more columns in every table:

1) upstream_id (TEXT, primary key)
    * The upstream_id represents the unique identifier of the record in the upstream API. It is used to map the records in your database to the corresponding records in the external API. Typically, this field is used as the primary key in your database table, ensuring that each record corresponds to a unique entity from the API.

2) updated_idx (BIGINT)
    * The updated_idx is a sequential index that increments every time a record is created, updated, or deleted in the upstream API. It helps maintain the version of the record. It is used to guard against race conditions during upserts. By including a condition in your upsert logic that compares the updated_idx values, you ensure that only the most recent version of a record is written to your database.

These two will be the first two columns of every table.

### Sequin Breakdown

We use Sequin to pull data from our Airtables without having to directly interact with Airtable's APIs. Sequin uses the idea of a stream, a data flow from one or many sources to a destination. Each stream has two parts: a sync, which extracts data and pushes into the stream, and a consumer, which pulls data down from the stream.


### How to Run

1) Clone this repo
2) Install the necessary packages
3) Configure your .env file -- ask me (vishnu) for the Sequin Key and Id
4) Visit sql.py and run the `createTbls()` function
5) Visit pipeline.py and run the file -- let it run until it says `No more messages to pull, sleeping for 5 seconds` in the terminal. You can Ctrl-C at this point -- for now, no need to have continuous sync
    * initially, the output will be `Pulled 0 messages` -- that is alright and expected