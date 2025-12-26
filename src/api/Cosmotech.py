import requests
# import base64
import json


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

