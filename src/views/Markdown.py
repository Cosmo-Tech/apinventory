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


    # # JSON input must be type a dict
    # def json_to_markdown_helmchart(self):
    #     with open(self.file_json, 'r') as file:
    #         json_data = json.load(file)

    #     markdown = f"### {self.title}\n"
    #     markdown +=  "| Chart name | Chart version | App version |\n"
    #     markdown +=  "|------------|---------------|-------------|\n"

    #     for chart_name, chart_version, app_version in json_data.items():
    #         markdown += f"|{chart_name}|{chart_version}||{app_version}|\n"
   
    #     return markdown


    # JSON input must be type a dict
    def json_to_markdown_helmchart(self):
        with open(self.file_json, 'r') as file:
            json_data = json.load(file)

        markdown = f"### {self.title}\n"
        markdown +=  "| Namespace | Chart name | Chart version | App version |\n"
        markdown +=  "|-----------|------------|---------------|-------------|\n"


        # Try/catch here is to get values from differents JSON structures (sometimes there's a list in a list and sometimes not)
        for data_level_1 in json_data:
            try:
                namespace   = data_level_1.get('namespace')
                charts      = data_level_1.get('charts')
            except:
                for data_level_2 in data_level_1:
                    namespace   = data_level_2.get('namespace')
                    charts      = data_level_2.get('charts')

            for chart in charts:
                markdown += f"|{namespace}|{chart['name']}|{chart['chart_version']}|{chart['app_version']}|\n"

        return markdown