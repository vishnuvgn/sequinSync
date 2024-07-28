import json
import os

# Directory containing the individual JSON files
directory = 'tables'

# List to hold all table objects
combined_data = []

# Iterate through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.json'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as file:
            table_data = json.load(file)
            combined_data.append(table_data)

# Write the combined data to a single JSON file
with open('combined_tables.json', 'w') as outfile:
    json.dump(combined_data, outfile, indent=4)

print("Combined JSON file created successfully.")
