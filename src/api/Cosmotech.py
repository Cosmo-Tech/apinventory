import requests
import base64
import json


class Keycloak():

    def __init__(self, base_url, realm, client_id, client_secret):
        self.base_url = base_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret

    def get_token(self):
        data = {
            "grant_type": "client_credentials",
            # "scope": "openid",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        r = requests.post(f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token", data=data)
        return r.json()
        # Get bearer token from Keycloak example:
        # curl \
        # -d "grant_type=client_credentials" \
        # -d "client_id=CLIENT_ID" \
        # -d "client_secret=CLIENT_SECRET" \
        # "BASE_URL/realms/REALM/protocol/openid-connect/token"


class CosmotechAPI():

    def __init__(self, url, token):
        self.url = url
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

    # All organizations
    def organizations_json(self):
        r = requests.get(self.url + '/organizations', headers=self.headers)
        # if r.status_code != "200":
        #     print('Cosmo Tech API authentication error: check client access')
        #     return
        data = r.json()
        return data

    # All solutions in a given organization
    def solutions_json(self, organization_id):
        r = requests.get(self.url + '/organizations/' + organization_id + '/solutions', headers=self.headers)
        # if r.status_code != "200":
        #     print('Cosmo Tech API authentication error: check client access')
        #     return
        data = r.json()
        return data

    # All workspaces in a given organization
    def workspaces_json(self, organization_id):
        r = requests.get(self.url + '/organizations/' + organization_id + '/workspaces', headers=self.headers)
        # if r.status_code != "200":
        #     print('Cosmo Tech API authentication error: check client access')
        #     return
        data = r.json()
        return data

