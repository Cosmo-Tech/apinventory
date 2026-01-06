from azure.identity import DefaultAzureCredential

class Azure:

    def __init__(self, subscription_id):
        self.subscription_id = subscription_id
        self.credential = DefaultAzureCredential()

    def get_token(self):
        token = self.credential.get_token("https://management.azure.com/.default")
        return token

    # def get_token_info(self):
    #     token = self.credential.get_token("https://management.azure.com/.default")
    #     return token
