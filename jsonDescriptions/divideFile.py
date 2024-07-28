import json

# Load the combined JSON file
with open('combined_tables.json', 'r') as file:
    data = json.load(file)

# Iterate through each table object and write to its own JSON file
for table in data:
    file_name = f"tables/{table['tableName']}.json"
    with open(file_name, 'w') as outfile:
        json.dump(table, outfile, indent=4)

print("Individual JSON files created successfully.")
