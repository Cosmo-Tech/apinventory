
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
    dir_inventory = "_inventory"
    if not os.path.exists(dir_inventory):
        os.makedirs(dir_inventory)

    # Create a the directory of the day
    dir_today_inventory = os.path.join(dir_inventory, now)
    if not os.path.exists(dir_today_inventory):
        os.makedirs(dir_today_inventory)

    dir_today_inventory_json = os.path.join(dir_today_inventory, "json")
    if not os.path.exists(dir_today_inventory_json):
        os.makedirs(dir_today_inventory_json)

    dir_today_inventory_md = os.path.join(dir_today_inventory, "md")
    if not os.path.exists(dir_today_inventory_md):
        os.makedirs(dir_today_inventory_md)


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

    deployments_dict={}
    for organization in cosmotech_api.organizations_json():
        organization_id = f"{organization['id']}"
        for solution in cosmotech_api.solutions_json(organization['id']):
            for workspace in cosmotech_api.workspaces_json(organization['id']):
                workspaces = [
                    ("organization_id",         organization_id),
                    ("workspace_id",            f"{workspace['id']}"),
                    ("solution_id",             f"{solution['id']}"),
                    ("organization_name",       f"{organization['name']}"),
                    ("workspace_name",          f"{workspace['name']}"),
                    ("solution_name",           f"{solution['name']}"),
                    ("solution_repository",     f"{solution['repository']}"),
                    ("solution_version",        f"{solution['version']}"),
                ]
                deployments_dict.update(dict(workspaces))

        print(deployments_dict)

        file_json = os.path.join(dir_today_inventory_json, organization_id + ".json")
        file_md = os.path.join(dir_today_inventory_md, organization_id + ".md")

        # Save inventory of the day to file <date>/workspaces.json
        with open(file_json, 'w') as f:
            json.dump(deployments_dict, f)
            print(f"file created: {f}")

        # Create markdown of the day to file <date>/workspaces.md
        markdown = Markdown(file_json, "Temporary title of the markdown file")
        with open(file_md, "w") as f:
            f.write(markdown.jsonToMarkdown())
            print(f"file created: {f}")


if __name__ == "__main__":
    main()

