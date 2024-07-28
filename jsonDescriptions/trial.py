import os
import json

# Directory containing the JSON files
directory = 'tables'

# Iterate through each file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.json'):
        filepath = os.path.join(directory, filename)
        
        # Load the JSON data from the file
        with open(filepath, 'r') as file:
            data = json.load(file)
        
        # Add the schemaName key-value pair
        data['schemaName'] = 'ingestion_test'
        
        # Save the updated JSON data back to the file
        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4)

print("Schema name added to all files successfully.")
