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
            print(f"error: failed to load context '{context}' from file {kubeconfig_file}")

        self.client_CoreV1Api = client.CoreV1Api()
        self.client_VersionApi = client.VersionApi()
        self.client_NetworkingV1Api = client.NetworkingV1Api()


    # Get info from current loaded context
    # Trick here is to get from the cluster URL that is already getted from this class
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
            field_selector = 'type=helm.sh/release.v1',   # Get only secrets that contains the Helm releases
            )

        for secret in secrets.items:
            if not secret.data or 'release' not in secret.data:
                continue

            release_data = self.decode_helmchart_secret(secret.data['release'])
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


    # A namespace is a tenant if it contains a Cosmo Tech API
    def is_namespace_tenant(self, namespace):
        is_tenant = False

        for pod in self.client_CoreV1Api.list_namespaced_pod(namespace).items:
            for container in pod.spec.containers:
                container_dict = container.to_dict()

                # Get the value from the deployed image (because it's the most stable information we can rely on)
                image = container_dict.get('image')
                if 'cosmo-tech/cosmotech-api' in image:
                    is_tenant = True

        return is_tenant


    # # Get all pods from a given namespace
    # def get_namespaced_pods(self, namespace):
    #     pods_list = []
    #     for pod in self.client_CoreV1Api.list_namespaced_pod(namespace).items:
    #         pods_list.append(pod.metadata.name)
    #     return pods_list


    # Get all Helm releases from a given namespace
    # Get them from the Helm secrets
    def get_helmchart_releases_list(self, namespace):
        secrets = self.client_CoreV1Api.list_namespaced_secret(
            namespace = namespace,
            label_selector = f'status=deployed',            # Get only the latest revision
            field_selector = f'type=helm.sh/release.v1',    # Get only secrets that contains the Helm releases
            )

        releases_list = []
        for secret in secrets.items:
            secret_name = secret.metadata.name
            release_name = secret_name.split('.')[4]        # Get the release name from the secret name itself
            releases_list.append(release_name)

        return releases_list


    # Decode Helm Chart release from its secret
    def decode_helmchart_secret(self, secret_to_decode):
        secret_decoded = base64.b64decode(secret_to_decode)     # Get the secret from base64
        helm_decoded = base64.b64decode(secret_decoded)         # Helm also encode the release in base64
        unzipped = gzip.decompress(helm_decoded)                # And finally, Helm is compressing the release
        release_data = json.loads(unzipped)

        return release_data

    # Get a deployed Helm Chart release
    def get_helmchart_release(self, namespace, helmchart):
        secrets = self.client_CoreV1Api.list_namespaced_secret(
            namespace = namespace,
            label_selector = f'status=deployed, name={helmchart}',  # Get only the latest revision
            field_selector = f'type=helm.sh/release.v1',            # Get only secrets that contains the Helm releases
            )

        for secret in secrets.items:
            if not secret.data or 'release' not in secret.data:
                continue

            release_data = self.decode_helmchart_secret(secret.data['release'])
            if release_data:
                chart_meta = release_data

        return chart_meta


    # Get values from a deployed Helm Chart release
    def get_helmchart_values(self, namespace, helmchart):
        release = self.get_helmchart_release(namespace, helmchart)
        values = release.get('config') # 'config' correspond to configured values of the chart in the release

        return values


    # Get and decode a given secret from Kubernetes
    def get_secret_decoded(self, namespace, secret_name):
        try:
            secret = self.client_CoreV1Api.read_namespaced_secret(
                namespace = namespace,
                name = secret_name,
                )

            utf8_decoded = {}
            for key, value in secret.data.items():
                base64_decoded = base64.b64decode(value)
                utf8_decoded[key] = base64_decoded.decode('utf-8')

            return utf8_decoded
        except:
            return ''


    # Get Azure subscription ID from a Kubernetes node (AKS)
    def get_azure_subcription_id(self):
        # Get all nodes to be sure having the information
        nodes = self.client_CoreV1Api.list_node()
        for node in nodes.items:
            try:
                subscription_id = (node.spec.provider_id).split('/')[4]
            except:
                subscription_id = 'n/a'
        return subscription_id


    # Get Cosmo Tech API version from its Helm Chart release
    def get_cosmotech_api_helmchart(self, namespace):
        for helm_release in self.get_helmchart_releases_list(namespace):

            # Get the release name of the Cosmo Tech API chart
            if 'cosmo' in helm_release and 'api' in helm_release:
                return helm_release


    # Get Cosmo Tech API URL
    def get_cosmotech_api_url(self, namespace):
        api_helm_release = self.get_cosmotech_api_helmchart(namespace)
        api_path = self.get_helmchart_values(namespace, api_helm_release)['api']['version']
        api_url = f"https://{self.get_cluster_url()}/{namespace}/{api_path}/"
        return api_url


    # Get Cosmo Tech API version from its Helm Chart release
    def get_cosmotech_api_version(self, namespace):
        api_helm_release_name = self.get_cosmotech_api_helmchart(namespace)
        api_helm_release_data = self.get_helmchart_release(namespace, api_helm_release_name)
        api_version = api_helm_release_data.get('chart').get('metadata').get('appVersion')
        return api_version
