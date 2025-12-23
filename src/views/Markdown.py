import json

class Markdown:

    def __init__(self, file_json, title):
        self.file_json = file_json
        self.title = title

    # JSON input must be type a dict
    def json_to_markdown_itemvalue(self):
        with open(self.file_json, 'r') as file:
            json_data = json.load(file)

        markdown = f"### {self.title}\n"
        markdown +=  "| Item | Value |\n"
        markdown +=  "|------|-------|\n"

        for item, value in json_data.items():
            markdown += f"|{item}|{value}|\n"
   
        return markdown


    # JSON input must be type a dict
    def json_to_markdown_helmchart(self):
        with open(self.file_json, 'r') as file:
            json_data = json.load(file)

        markdown = f"### {self.title}\n"
        markdown +=  "| Chart name | Chart version | App version |\n"
        markdown +=  "|------------|---------------|-------------|\n"

        for chart_name, chart_version, app_version in json_data.items():
            markdown += f"|{chart_name}|{chart_version}||{app_version}|\n"
   
        return markdown