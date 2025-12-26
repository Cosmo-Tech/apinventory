import requests
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
