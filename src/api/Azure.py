from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

class Azure:

    def __init__(self, subscription_id):
        self.subscription_id = subscription_id
        self.credential = DefaultAzureCredential()
        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)


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

