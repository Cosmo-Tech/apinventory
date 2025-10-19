import json

class Markdown:

    def __init__(self, file_json, title):
        self.file_json = file_json
        self.title = title

    def jsonToMarkdown(self):
        with open(self.file_json, 'r') as file:
            json_data = json.load(file)

        markdown = f"### {self.title}\n"
        markdown +=  "| Item | Value |\n"
        markdown +=  "|------|-------|\n"

        for key, item in json_data.items():
            markdown += f"|{key}|{item}|\n"
   
        return markdown

