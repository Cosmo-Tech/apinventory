# from azure.identity import DefaultAzureCredential
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
import requests


class Azure:

    def __init__(self, subscription_id, tenant_id, client_id, client_secret):
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        try:
            # self.credential = DefaultAzureCredential()
            self.credential = ClientSecretCredential(self.tenant_id, self.client_id, self.client_secret)
            self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        except Exception as e:
            print(f"error: {e}")


    # def get_token(self):
    #     token = self.credential.get_token("https://management.azure.com/.default")
    #     return token


    # List resources groups
    def list_resource_groups(self):
        rg_list = self.resource_client.resource_groups.list()
        for rg in rg_list:
            print(rg.name)


    # Get all resources from a given resource group
    def get_resource_group_resources(self, resource_group_name):
        resources_list = []
        try:
            resources = self.resource_client.resources.list_by_resource_group(resource_group_name)
        except Exception as e:
            print(f"error: unable to read resource group {resource_group_name}: {e}")
            return []

        for resource in resources:
            # print(resource)
            resource_info = {
                "name": resource.name,
                "type": resource.type,
                # "location": resource.location,
                # "id": resource.id,
                # "tags": resource.tags,
            }
            resources_list.append(resource_info)

        return resources_list


    # Get resource group name of a Storage Account
    # This is meant to be used to get the resource group of a tenant by using the storage account which can be found in Cosmo Tech API Helm Chart values
    def get_resource_group_from_storage_name(self, storage_account_name):
        storage_account_name_clean = storage_account_name.lower()
        query_filter = f"name eq '{storage_account_name_clean}' and resourceType eq 'Microsoft.Storage/storageAccounts'"
        resources_list = list(self.resource_client.resources.list(filter=query_filter))

        if not resources_list:
            print(f"Erreur : Le Storage Account '{storage_account_name_clean}' est introuvable.")
            return None

        rg_name = resources_list[0].id.split('/')[4]
        return rg_name


    # Get App registration list based on filters list
    # Based on Microsoft Graph API
    def get_apps_registration_list(self, criteria_list, match_all=True):
        if not criteria_list:
            return []

        token_graph = self.credential.get_token("https://graph.microsoft.com/.default")
        headers = {
            "Authorization": f"Bearer {token_graph.token}",
            "Content-Type": "application/json",
            "ConsistencyLevel": "eventual",
        }

        # Build KQL search request
        # Syntax: "displayName:Keyword1" AND "displayName:Keyword2"
        search_parts = []
        for term in criteria_list:
            term_clean = term.replace('"', '').strip()
            search_parts.append(f'"displayName:{term_clean}"')
        operator = " AND " if match_all else " OR "
        search_query = operator.join(search_parts)
        params = {
            '$search': search_query,
            '$select': 'displayName,appId,createdDateTime',
            '$count': 'true',
        }

        graph_api_url = "https://graph.microsoft.com/v1.0/applications"
        apps_list = []
        try:
            response = requests.get(graph_api_url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"error: Azure Microsoft Graph API {response.status_code}: {response.text}")
                return []

            data = response.json()
            if 'value' in data:
                for app in data['value']:
                    apps_list.append({
                        "name": app.get('displayName'),
                        "client_id": app.get('appId')
                    })
        except Exception as e:
            print(f"error: {e}")

        return apps_list

