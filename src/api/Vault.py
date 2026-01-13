import hvac
import sys

class Vault:

    def __init__(self, cluster):
        base_url = 'https://' + cluster.get_cluster_url()
        self.client = hvac.Client(
            url = base_url,
            token = self.get_root_token(cluster),
        )


    # Get root token to connect to Vault
    def get_root_token(self, cluster):
        try:
            for namespace in cluster.get_namespaces():
                if "vault" in namespace:
                    token = cluster.get_secret_decoded("vault", "vault-token-secret")['ROOT_TOKEN']
                    return token
        except Exception as e:
            print(f"error: {e}")


    # Get secret from Vault (try kv2 engine, fallback on kv1 engine)
    def get_secret(self, path):
        if '/' in path:
            mount_point, secret_path = path.split('/', 1)
        else:
            print(f"error: missing part in path: '{path}'")
            return None

        try:
            # print(f"info: trying to get secret for vault kv2 engine")
            response = self.client.secrets.kv.v2.read_secret_version(
                path=secret_path,
                mount_point=mount_point
            )
            return response['data']['data']

        except (hvac.exceptions.InvalidPath, hvac.exceptions.Forbidden):
            # print(f"error: failed to get secret from vault kv2 engine, trying with kv1...")
            try:
                # print(f"info: trying to get secret for vault kv1 engine")
                response = self.client.secrets.kv.v1.read_secret(
                    path=secret_path,
                    mount_point=mount_point
                )
                return response['data']

            except Exception as e:
                print(f"error: secret not found: {e}")
                return None


    # List mount points of the Vault
    def list_mounts(self):
        mounts_list = []
        try:
            r = self.client.sys.list_mounted_secrets_engines()
            data = r['data']
            for item in data:
                if item not in ['cubbyhole/', 'sys/', 'identity/', 'organization/']:
                    mounts_list.append(str(item))

        except Exception as e:
            print(f"error: {e}")

        return mounts_list


    # Dynamically test if secret exists to get its content
    # Goal is to be able to find where a secret is stored when missing unpredictable mount point
    def get_secret_from_unknown_mount(self, path):
        try:
            mounts = self.list_mounts()
            for mount in mounts:
                    secret = self.get_secret(mount + path)
                    return secret
        except Exception as e:
            print(f"error: {e}")

