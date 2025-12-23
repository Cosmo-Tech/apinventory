import os
import json


# Create a JSON file
# Tips: content is well working with dict type
def create_json_file(file_path, content):
    with open(file_path, 'w') as file:
        json.dump(content, file)

    print(f"file created: {file_path}")


# Merge JSON files from a list
def merge_json_files(file_paths, file_output, delete_originals=False):
    merged_data = []
    for path in file_paths:
        with open(path, 'r') as file:
            data = json.load(file)
            merged_data.append(data)

    with open(file_output, 'w') as output:
        json.dump(merged_data, output)

    print(f"file created: {file_output}")

    # Option to delete original files after have merged them
    if delete_originals == True:
        for file in file_paths:
            delete_file(file)


# Simply rename a file and keeping it in the same directory
def rename_file(file_path, file_name_new):
    directory = os.path.dirname(file_path)
    os.rename(file_path, os.path.join(directory, file_name_new))

    print(f"file renamed: {file_path} -> {file_name_new}")


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"file deleted: {file_path}")
