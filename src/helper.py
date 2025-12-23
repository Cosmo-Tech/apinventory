import os
import json


# Create a JSON file
# content is well working with dict type
def create_json_file(directory, filename, content):
    file_json = os.path.join(directory, filename + ".json")
    with open(file_json, 'w') as file:
        json.dump(content, file)

    print(f"file created: {file}")
