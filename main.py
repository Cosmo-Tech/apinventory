
from datetime import datetime
import os
import json
import jsonschema_markdown

from src.api.Cosmotech import CosmotechAPI, Keycloak
from src.views.Markdown import Markdown

from dotenv import load_dotenv


def main():

    now = datetime.today().strftime('%Y-%m-%d')

    load_dotenv()

    # Create structure to store inventory pages
    dir_inventory = ".inventory"
    if not os.path.exists(dir_inventory):
        os.makedirs(dir_inventory)

    # Create a the directory of the day
    dir_today_inventory = os.path.join(dir_inventory, now)
    if not os.path.exists(dir_today_inventory):
        os.makedirs(dir_today_inventory)

    file_today_workspaces = os.path.join(dir_today_inventory, "workspaces")
    file_today_workspaces_json = file_today_workspaces + ".json"
    file_today_workspaces_md = file_today_workspaces + ".md"

    # Get a token from Keycloak with given credential
    keycloak = Keycloak(
        base_url = os.getenv('keycloak_base_url'),
        realm = os.getenv('keycloak_realm'),
        client_id = os.getenv('keycloak_client_id'),
        client_secret = os.getenv('keycloak_client_secret'),
    )
    keycloak_token = keycloak.get_token()

    # Authenticate on Cosmotech API with Keycloak token
    cosmotech_api = CosmotechAPI(
        url = os.getenv('cosmotech_api_url'),
        token = keycloak_token["access_token"],
    )

    workspaces_dict={}
    for organization in cosmotech_api.organizations_json():
        for solution in cosmotech_api.solutions_json(organization['id']):
            for workspace in cosmotech_api.workspaces_json(organization['id']):
                workspaces_list = [
                    ("organization_id",         f"{organization['id']}"),
                    ("organization_name",       f"{organization['name']}"),
                    ("solution_id",             f"{solution['id']}"),
                    ("solution_name",           f"{solution['name']}"),
                    ("solution_repository",     f"{solution['repository']}"),
                    ("solution_version",        f"{solution['version']}"),
                    ("workspace_id",            f"{workspace['id']}"),
                    ("workspace_name",          f"{workspace['name']}"),
                    # ("workspace_acl",           f"{workspace['security']['accessControlList']}"),        
                ]
                workspaces_dict = dict(workspaces_list)
                print(workspaces_dict)                

    # Save inventory of the day - .inventory/<date>/workspaces.json
    with open(file_today_workspaces_json, "w") as file_json:
        file_json.write(str(workspaces_dict).replace("'", "\""))

    # Create markdown of the day - .inventory/<date>/workspaces.md
    markdown = Markdown(file_today_workspaces_json, "Workspace")
    with open(file_today_workspaces_md, "w") as file_md:
        file_md.write(markdown.jsonToMarkdown())


if __name__ == "__main__":
    main()

