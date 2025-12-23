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


    # Get all Helm Charts in a given namespace
    # The trick here is to retrieve Helm Charts from secrets (all Helm Charts releases are automatically stored in dedicated secrets)
    def get_helmcharts(self, namespace):
        helmcharts_list = []
        helmchart_object = {
            'namespace': namespace,
            'charts': []
        }

        secrets = self.client_CoreV1Api.list_namespaced_secret(
            namespace = namespace,
            label_selector = 'status=deployed',           # Get only the latest revision
            field_selector = 'type=helm.sh/release.v1',   # Get only Helm secrets that contains the releases
            )

        for secret in secrets.items:
            if not secret.data or 'release' not in secret.data:
                continue

            k8s_decoded = base64.b64decode(secret.data['release'])  # Get the secret in base64
            helm_decoded = base64.b64decode(k8s_decoded)            # Helm also encode the release
            unzipped = gzip.decompress(helm_decoded)                # And finally, Helm is compressing the release
            release_data = json.loads(unzipped)
            
            if release_data:
                chart_meta = release_data.get('chart', {}).get('metadata', {})
                chart_info = {
                    'name':             chart_meta.get('name', 'n/a'),
                    'chart_version':    chart_meta.get('version', 'n/a'),
                    'app_version':      chart_meta.get('appVersion', 'n/a')
                }
                helmchart_object['charts'].append(chart_info)

        # Add to list only if not empty
        if len(helmchart_object.get('charts')) > 0:
            helmcharts_list.append(helmchart_object)

        return helmcharts_list