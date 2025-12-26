
from datetime import datetime
import os
import json
import jsonschema_markdown
import yaml # useful for kubeconfig files
import shutil

# from dotenv import load_dotenv

from src.api.Kubernetes import KubeCluster
from src.api.Keycloak import Keycloak
from src.api.Cosmotech import CosmotechAPI
from src.views.Markdown import Markdown

import src.helper as helper


now = datetime.today().strftime('%Y-%m-%d')

dir_inventory            = "_inventory"
dir_today_inventory      = os.path.join(dir_inventory, now)
dir_today_inventory_json = os.path.join(dir_today_inventory, "json")
dir_today_inventory_md   = os.path.join(dir_today_inventory, "md")

kubeconfig_file = '_kubeconfig'


def main():

    # load_dotenv()

    # Prepare structure of the day
    if os.path.exists(dir_today_inventory):
        shutil.rmtree(dir_today_inventory)
    for dir in [dir_inventory, dir_today_inventory, dir_today_inventory_json, dir_today_inventory_md]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    for context in get_all_contexts(kubeconfig_file):
        # Structure JSON of the day for clusters
        dir_cluster = os.path.join(dir_today_inventory_json, context)
        if not os.path.exists(dir_cluster):
            os.makedirs(dir_cluster)

        # Generate inventories
        cluster_properties(kubeconfig_file, context, dir_cluster)
        all_helmcharts(kubeconfig_file, context, dir_cluster)
        tenants_properties(kubeconfig_file, context, dir_cluster)


        # Structure JSON of the day for tenants (which host workspaces files)
        cluster = KubeCluster(kubeconfig_file, context)
        for namespace in cluster.get_namespaces():
            if cluster.is_namespace_tenant(namespace):
                dir_tenant = os.path.join(dir_today_inventory_json, cluster.get_cluster_name(), namespace)
                if not os.path.exists(dir_tenant):
                    os.makedirs(dir_tenant)

                # Generate inventories
                workspaces_properties(kubeconfig_file, context, dir_tenant, namespace)



        # # Structure Markdown of the day
        # dir_cluster    = os.path.join(dir_today_inventory_md, context)
        # dir_tenants = os.path.join(dir_today_inventory_md, context, "namespaces")
        # dir_workspaces = os.path.join(dir_tenants, "workspaces")
        # for dir in [dir_cluster, dir_tenants, dir_workspaces]:
        #     if not os.path.exists(dir):
        #         os.makedirs(dir)



    # create_all_markdown() # Create all markdown files of the day


# Get all Kubernetes contexts from a given kubeconfig file
# - Input is YAML (because kubeconfig files are mainly YAML by default)
# - Output is JSON
def get_all_contexts(kubeconfig_file):
    with open(kubeconfig_file) as file:
        kubeconfig = yaml.load(file, Loader=yaml.FullLoader)

    contexts = []
    for context in kubeconfig['contexts']:
        contexts.append(context['name'])

    return contexts


# Save cluster properties in a file
def cluster_properties(kubeconfig_file, context, dir_output):
    # Get:
    # - Cluster name
    # - Cluster region
    # - Cluster version

    cluster = KubeCluster(kubeconfig_file, context)
    name    = cluster.get_cluster_name()
    region  = cluster.get_cluster_region()
    version = cluster.get_cluster_version()
    url     = f"https://{cluster.get_cluster_url()}"

    cluster_dict={}
    properties = [
        ("name",            name),
        ("region",          region),
        ("version",         version),
        ("url",             url),
        ("keycloak_url",    url + '/keycloak/'),
        ("monitoring_url",  url + '/monitoring/'),
        ("harbor_url",      url + '/harbor/'),
        ("inventory_date",  now),
    ]
    cluster_dict.update(dict(properties))

    # Save to JSON file of the day
    helper.create_json_file(os.path.join(dir_output, 'cluster-properties.json'), cluster_dict)


# Save all Helm Charts
# - one file for cluster-wide
# - one file for each tenants
def all_helmcharts(kubeconfig_file, context, dir_output):
    # Get:
    # - Cluster-wide Helm Charts names
    # - Cluster-wide Helm Charts versions
    # - Cluster-wide Helm Charts App versions
    # - Tenant Helm Charts names
    # - Tenant Helm Charts versions
    # - Tenant Helm Charts App versions

    cluster = KubeCluster(kubeconfig_file, context)
    files_json_to_merge = []
    helmcharts_dict = {}

    for namespace in cluster.get_namespaces():

        # Namespaces to avoid (filtered from their name)
        filters = ['kube-', '-system', 'default', 'tigera-operator']
        if namespace not in filters and not namespace.startswith(tuple(filters)) and not namespace.endswith(tuple(filters)):

            # Save to JSON file of the day
            file_json = os.path.join(dir_output, "ns-" + namespace + '.json')
            helmcharts_list = cluster.get_helmcharts(namespace)

            # Avoid namespaces without Helm Charts installed
            if len(helmcharts_list) > 0:
                helper.create_json_file(file_json, helmcharts_list)

                # Keep only separated namespaces files and merge cluster-wide helmcharts in a single file
                if 'tenant' in os.path.basename(file_json):
                    helper.rename_file(file_json, namespace + '-helmcharts.json')
                else:
                    files_json_to_merge.append(file_json)

    # Merge all cluster-wide in one single file
    helper.merge_json_files(files_json_to_merge, os.path.join(dir_output, 'cluster-helmcharts.json'), delete_originals=True)


def tenants_properties(kubeconfig_file, context, dir_output):
    # Get:
    # - Tenant name
    # - Cosmo Tech API Swagger URL

    tenant_dict = {}
    cluster = KubeCluster(kubeconfig_file, context)

    namespaces = cluster.get_namespaces()
    for namespace in namespaces:
        if cluster.is_namespace_tenant(namespace):

            properties = [
                ("tenant_name",     namespace),
                ("swagger_url",     get_cosmotech_api_url(kubeconfig_file, context, namespace)),
                ("inventory_date",  now),
            ]
            tenant_dict.update(dict(properties))

            # Save to JSON file of the day
            helper.create_json_file(os.path.join(dir_output, namespace + '-properties.json'), tenant_dict)



# def workspaces_properties():
#     # Get:
#     # - Organizations id
#     # - Organizations name
#     # - Solutions id
#     # - Solutions name
#     # - Solutions repository
#     # - Solutions version
#     # - Workspaces id
#     # - Workspaces name

#     # Get a token from Keycloak with given credential
#     keycloak = Keycloak(
#         base_url = os.getenv('keycloak_base_url'),
#         realm = os.getenv('keycloak_realm'),
#         client_id = os.getenv('keycloak_client_id'),
#         client_secret = os.getenv('keycloak_client_secret'),
#     )
#     keycloak_token = keycloak.get_token()

#     # Authenticate on Cosmo Tech API with Keycloak token
#     cosmotech_api = CosmotechAPI(
#         url = os.getenv('cosmotech_api_url'),
#         token = keycloak_token["access_token"],
#     )

#     deployments_dict={}
#     for organization in cosmotech_api.organizations_json():
#         for solution in cosmotech_api.solutions_json(organization['id']):
#             for workspace in cosmotech_api.workspaces_json(organization['id']):
#                 workspace_id = f"{workspace['id']}"
#                 properties = [
#                     ("organization_id",         organization.get('id', 'n/a')),
#                     ("workspace_id",            workspace.get('id', 'n/a')),
#                     ("solution_id",             solution.get('id', 'n/a')),
#                     ("organization_name",       organization.get('name', 'n/a')),
#                     ("workspace_name",          workspace.get('name', 'n/a')),
#                     ("solution_name",           solution.get('name', 'n/a')),
#                     ("solution_repository",     solution.get('repository', 'n/a')),
#                     ("solution_version",        solution.get('version', 'n/a')),
#                     ("inventory_date",          now),
#                 ]
#                 deployments_dict.update(dict(properties))

#         print(deployments_dict)

#         # Save to JSON file of the day
#         file_json = os.path.join(dir_today_inventory_json, workspace_id + ".json")
#         with open(file_json, 'w') as f:
#             json.dump(deployments_dict, f)
#             print(f"file created: {f}")


# Get properties of all Workspaces in a given Tenant
def workspaces_properties(kubeconfig_file, context, dir_output, namespace):
    # Get:
    # - Organizations id
    # - Organizations name
    # - Solutions id
    # - Solutions name
    # - Solutions repository
    # - Solutions version
    # - Workspaces id
    # - Workspaces name

    cluster = KubeCluster(kubeconfig_file, context)
    if cluster.is_namespace_tenant(namespace):

        # Get Keycloak credentials from dedicated Kubernetes secret
        keycloak_secret = cluster.get_secret_decoded(namespace, 'keycloak-babylon')

        # Get a token from Keycloak with given credential
        keycloak = Keycloak(
            base_url        = 'https://' + cluster.get_cluster_url() + '/keycloak',
            realm           = namespace,
            client_id       = keycloak_secret.get('client_id', ''),
            client_secret   = keycloak_secret.get('client_secret', ''),
        )
        keycloak_token = keycloak.get_token()

        # Authenticate on Cosmo Tech API with Keycloak token
        cosmotech_api = CosmotechAPI(
            url = get_cosmotech_api_url(kubeconfig_file, context, namespace),
            token = keycloak_token["access_token"],
        )

        workspaces_dict={}
        for organization in cosmotech_api.organizations_json():
            for solution in cosmotech_api.solutions_json(organization['id']):
                for workspace in cosmotech_api.workspaces_json(organization['id']):
                    workspace_id = f"{workspace['id']}"
                    properties = [
                        ("tenant_name",             namespace),
                        ("organization_id",         organization.get('id', 'n/a')),
                        ("workspace_id",            workspace.get('id', 'n/a')),
                        ("solution_id",             solution.get('id', 'n/a')),
                        ("organization_name",       organization.get('name', 'n/a')),
                        ("workspace_name",          workspace.get('name', 'n/a')),
                        ("solution_name",           solution.get('name', 'n/a')),
                        ("solution_repository",     solution.get('repository', 'n/a')),
                        ("solution_version",        solution.get('version', 'n/a')),
                        ("inventory_date",          now),
                    ]
                    workspaces_dict.update(dict(properties))

            # Save to JSON file of the day
            helper.create_json_file(os.path.join(dir_output, workspace_id + '.json'), workspaces_dict)



# def create_all_markdown():
#     print("creating markdown files...")
#     for file_json in os.scandir(dir_today_inventory_json):  
#         if file_json.is_file():
#             markdown = Markdown(file_json, "Temporary title of the markdown file")
#             file_md = os.path.join(dir_today_inventory_md, os.path.basename(file_json).replace("json", "md"))
#             with open(file_md, "w") as f:
#                 f.write(markdown.json_to_markdown_itemvalue())
#                 print(f"file created: {f}")



# Get Cosmo Tech API URL
def get_cosmotech_api_url(kubeconfig_file, context, namespace):
    cluster = KubeCluster(kubeconfig_file, context)

    if cluster.is_namespace_tenant(namespace):
        for helm_release in cluster.get_namespaced_releases(namespace):

            # Get the release name of the Cosmo Tech API chart
            if 'cosmo' in helm_release and 'api' in helm_release:

                # Cosmo Tech API URL
                csm_api_path = cluster.get_helmchart_values(namespace, helm_release)['api']['version']
                csm_api_url = f"https://{cluster.get_cluster_url()}/{namespace}/{csm_api_path}/"

                return csm_api_url


if __name__ == "__main__":
    main()