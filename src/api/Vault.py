import hvac
import sys
from src.api.Kubernetes import KubeCluster


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
                print(f"error: secret not found. Does mount point '{mount_point}' exist? {e}")
                return None
