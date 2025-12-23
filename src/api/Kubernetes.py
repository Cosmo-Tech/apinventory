import kubernetes.client as client
import kubernetes.config as config
import base64
import gzip
import json


class KubeCluster:

    # Load a config with Kubernetes context from a given kubeconfig file
    def __init__(self, kubeconfig_file, context):
        try:
            config.load_kube_config(kubeconfig_file, context)
        except:
            print("error: failed to load context '" + context + "' from file" + kubeconfig_file)
        self.client_CoreV1Api = client.CoreV1Api()
        self.client_VersionApi = client.VersionApi()
        self.client_NetworkingV1Api = client.NetworkingV1Api()


    # Get info from current loaded context
    # Trick here is to get from the cluster URL that is already getted in this class 
    def get_cluster_name(self):
        try:
            name = self.get_cluster_url().split(".")[0]
        except:
            name = 'n/a'
        return name


    # Get info from current loaded context 
    # The trick here is to retrieve region from nodes, or return N/A if not a cloud-based cluster
    def get_cluster_region(self):
        # Get all nodes to be sure having the information
        nodes = self.client_CoreV1Api.list_node()
        for node in nodes.items:
            try:
                region = node.metadata.labels['topology.kubernetes.io/region']
            except:
                region = 'n/a'
        return region

        # # Get all nodes
        # nodes = self.client_CoreV1Api.list_node()
        # nodes_dict = {}
        # for node in nodes.items:
        #     labels = node.metadata.labels
        #     region = labels.get('topology.kubernetes.io/region')
        #     print(region)


    # Get info from current loaded context 
    def get_cluster_version(self):
        code = self.client_VersionApi.get_code().to_dict()
        try:
            version = code.get('git_version')
        except:
            version = 'n/a'
        return version


    # Get info from current loaded context
    # Trick here is to get the URL from a stable cluster-wide endpoint over Cosmo Tech platforms versions, and the winner is... Keycloak
    def get_cluster_url(self):
        ingress = self.client_NetworkingV1Api.read_namespaced_ingress('keycloak', 'keycloak').to_dict()
        try:
            rules = ingress.get('spec').get('rules')
            for rule in rules:
                url = rule['host']
        except:
            url = 'n/a'
        return url


    # Get all namespaces from the current loaded context
    def get_namespaces(self):
        namespaces = []
        for namespace in self.client_CoreV1Api.list_namespace().items:
            namespaces.append(namespace.metadata.name)
        return namespaces


    # # Get all pods in a given namespace
    # def get_pods(self, namespace):
    #     list_pods = []
    #     for pod in self.client_CoreV1Api.list_namespaced_pod(namespace).items:
    #         list_pods.append(pod.metadata.name)
    #     return list_pods


    # Get all Helm Charts in a given namespace
    # The trick here is to retrieve Helm Charts from secrets (all Helm Charts releases are automatically stored in dedicated secrets)
    def get_helmcharts(self, namespace):

        secrets = self.client_CoreV1Api.list_namespaced_secret(namespace, field_selector="type=helm.sh/release.v1")
        releases_latest = {}
        helmcharts_dict = {}
        for secret in secrets.items:

            # Check if latest revision (="chart release version") from secret labels
            labels = secret.metadata.labels
            name = labels.get('name')
            revision = int(labels.get('version', 0))
            if name in releases_latest and revision <= releases_latest[name]['revision']:
                continue

            secret_raw = secret.data['release']                             # Get the secret in base64
            secret_decoded = base64.b64decode(base64.b64decode(secret_raw)) # Decode the secret (twice because Kubernetes secrets are always encoded and Helm is also encoding the release)
            secret_uncompressed = gzip.decompress(secret_decoded)           # Uncompress the secret as Helm is gzipping it

            release = json.loads(secret_uncompressed)
            release_metadata = release.get('chart', {}).get('metadata', {})
            release_namespace = release.get('namespace', 'n/a')

            releases_latest[name] = {
                "revision": revision, # used to retrieve latest revision
                "data": {
                    "namespace":     release.get('namespace', 'n/a'),
                    "chart_name":    release_metadata.get('name', 'n/a'),
                    "chart_version": release_metadata.get('version', 'n/a'),
                    "app_version":   release_metadata.get('appVersion', 'n/a'),
                }
            }

        helmcharts_list = [item['data'] for item in releases_latest.values()]
        helmcharts_dict = {key: value['data'] for key, value in releases_latest.items()}

        # return helmcharts_list

        #     for helmchart in release:
        #         helmchart_data = [
        #             ("revision",        revision),
        #             ("namespace",       release.get('namespace', 'n/a')),
        #             ("chart_name",      release_metadata.get('name', 'n/a')),
        #             ("chart_version",   release_metadata.get('version', 'n/a')),
        #             ("app_version",     release_metadata.get('appVersion', 'n/a')),
        #         ]
        #         helmcharts_dict.update(dict(helmchart_data))
        # print(helmcharts_dict)

        return helmcharts_dict


    # # Look for namespaces where a Cosmo Tech API is installed, if there is one it means it's a tenant
    # def namespace_is_tenant(self, namespace):
    #     is_tenant = false
    #     return is_tenant


