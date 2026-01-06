
import os
import sys
import shutil
import json
import yaml # useful for kubeconfig files
import time
import schedule
from datetime import datetime
from dotenv import load_dotenv

from src.api.Kubernetes import KubeCluster
from src.api.Keycloak import Keycloak
from src.api.Azure import Azure
from src.api.Cosmotech import CosmotechAPI
from src.views.Markdown import Markdown

import src.helper as helper


load_dotenv()

today = datetime.today().strftime('%Y-%m-%d')

dir_inventory            = "_inventory"
dir_today_inventory      = os.path.join(dir_inventory, today)
dir_today_inventory_json = os.path.join(dir_today_inventory, "json")
dir_inventory_md   = os.path.join(dir_inventory, "markdown")

kubeconfig_file = str(os.getenv('APINV_KUBECONFIG_PATH'))


def main():

    # Prepare structure of the day
    for dir_to_delete in [dir_today_inventory, dir_inventory_md]:
        if os.path.exists(dir_to_delete):
            shutil.rmtree(dir_to_delete)
    for dir_to_create in [dir_inventory, dir_today_inventory, dir_today_inventory_json, dir_inventory_md]:
        if not os.path.exists(dir_to_create):
            os.makedirs(dir_to_create)


    # Ensure cluster is reachable to avoid killing program
    available_clusters = []
    for context in get_all_contexts(kubeconfig_file):
        cluster = KubeCluster(kubeconfig_file, context)
        try:
            # If the version is returned, it mean the cluster is up (and if not, it means the cluster is down or not reachable)
            cluster.get_cluster_version()
            available_clusters.append(cluster)
        except:
            print(f"error: failed to connect to context '{context}'. Is cluster down ?")


    for cluster in available_clusters:
        cluster_name = cluster.get_cluster_name()

        # JSON structure of the day for clusters
        dir_cluster = os.path.join(dir_today_inventory_json, cluster_name)
        if not os.path.exists(dir_cluster):
            os.makedirs(dir_cluster)

        # Generate inventories
        cluster_properties(cluster, dir_cluster)
        all_helmcharts(cluster, dir_cluster)
        tenants_properties(cluster, dir_cluster)

        # Markdown structure of the day for clusters
        dir_cluster_md = os.path.join(dir_inventory_md, cluster_name)
        if not os.path.exists(dir_cluster_md):
            os.makedirs(dir_cluster_md)

        # Create Markdown files from JSON for clusters
        create_file_markdown_itemvalue(dir_cluster_md, os.path.join(dir_cluster, 'cluster-properties.json'), f"Cluster properties")
        create_file_markdown_helmcharts(dir_cluster_md, os.path.join(dir_cluster, 'cluster-helmcharts.json'), f"Cluster-wide Helm Charts")
        helper.merge_files(os.path.join(dir_cluster_md, 'cluster-helmcharts.md'), os.path.join(dir_cluster_md, 'cluster-properties.md'))
        helper.delete_file(os.path.join(dir_cluster_md, 'cluster-helmcharts.md'))

        # JSON structure of the day for tenants (which host workspaces files)
        for namespace in cluster.get_namespaces():
            if cluster.is_namespace_tenant(namespace):
                dir_tenant = os.path.join(dir_today_inventory_json, cluster_name, namespace)
                if not os.path.exists(dir_tenant):
                    os.makedirs(dir_tenant)

                dir_tenant_md = os.path.join(dir_inventory_md, cluster_name, namespace)
                if not os.path.exists(dir_tenant_md):
                    os.makedirs(dir_tenant_md)

                # Tenants Markdown
                try:
                    # Properties
                    create_file_markdown_itemvalue(dir_cluster_md, os.path.join(dir_cluster, f"{namespace}-properties.json"), f"Tenant properties")
                    try:
                        # Helmcharts
                        create_file_markdown_helmcharts(dir_cluster_md, os.path.join(dir_cluster, f"{namespace}-helmcharts.json"), f"Tenant Helm Charts")
                        helper.merge_files(os.path.join(dir_cluster_md, f"{namespace}-helmcharts.md"), os.path.join(dir_cluster_md, f"{namespace}-properties.md"))
                        helper.delete_file(os.path.join(dir_cluster_md, f"{namespace}-helmcharts.md"))
                    except:
                        print(f"error: unable to list helmcharts of {namespace}")
                except:
                    print(f"error: unable to list properties of {namespace}")

                # Workspaces
                try:
                    # JSON
                    workspaces_properties(cluster, dir_tenant, namespace)

                    # Markdown
                    for workspace_file in os.listdir(dir_tenant):
                        workspace_name = workspace_file.replace('.json', '')
                        create_file_markdown_itemvalue(dir_tenant_md, os.path.join(dir_tenant, workspace_file), f"Workspace properties")
                except:
                    print(f"error: unable to list workspaces from {namespace}")


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
def cluster_properties(cluster, dir_output):
    # Get:
    # - Cluster name
    # - Cluster region
    # - Cluster version

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
        ("inventory_date",  today),
    ]
    cluster_dict.update(dict(properties))

    # Save to JSON file of the day
    helper.create_json_file(os.path.join(dir_output, 'cluster-properties.json'), cluster_dict)


# Save all Helm Charts
# - one file for cluster-wide
# - one file for each tenants
def all_helmcharts(cluster, dir_output):
    # Get:
    # - Cluster-wide Helm Charts names
    # - Cluster-wide Helm Charts versions
    # - Cluster-wide Helm Charts App versions
    # - Tenant Helm Charts names
    # - Tenant Helm Charts versions
    # - Tenant Helm Charts App versions

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
                if cluster.is_namespace_tenant(namespace):
                    helper.rename_file(file_json, namespace + '-helmcharts.json')
                else:
                    files_json_to_merge.append(file_json)

    # Merge all cluster-wide in one single file
    helper.merge_json_files(files_json_to_merge, os.path.join(dir_output, 'cluster-helmcharts.json'), delete_originals=True)


# Get properties of all tenants in a cluster
def tenants_properties(cluster, dir_output):
    # Get:
    # - Tenant name
    # - Cosmo Tech API Swagger URL

    tenant_dict = {}
    namespaces = cluster.get_namespaces()
    for namespace in namespaces:
        if cluster.is_namespace_tenant(namespace):
            tenant_dict.clear()
            properties = [
                ("tenant_name",     namespace),
                ("swagger_url",     cluster.get_cosmotech_api_url(namespace)),
                ("inventory_date",  today),
            ]
            tenant_dict.update(dict(properties))

            # Add Azure resources if it's a platform < v5
            # Get API version to know if authentication is Keycloak or Azure
            cosmotech_api_version = cluster.get_cosmotech_api_version(namespace)
            platform_version = cosmotech_api_version.split('.')[0]
            if int(platform_version) < 5:
                azure = Azure(cluster.get_azure_subcription_id())

                rg = azure.get_resource_group_from_storage_name(cluster.get_cosmotech_api_storage_account(namespace))
                rg_ressources = azure.get_resource_group_resources(rg)
                if rg_ressources:
                    for rg_ressource in rg_ressources:
                        if rg_ressource['type'] == 'Microsoft.Storage/storageAccounts':
                            tenant_dict.update(dict([('Azure Storage Account', rg_ressource['name'])]))

                        if rg_ressource['type'] == 'Microsoft.ContainerRegistry/registries':
                            tenant_dict.update(dict([('Azure ACR', rg_ressource['name'])]))

                        if rg_ressource['type'] == 'Microsoft.Kusto/clusters':
                            tenant_dict.update(dict([('Azure ADX', rg_ressource['name'])]))
                else:
                    print(f"error: empty resource group {resource_group}")

                # Get App Registration list by filtering in their names
                app_registrations_list = azure.get_apps_registration_list([namespace], match_all=True)
                for app_registration in app_registrations_list:
                    app_registration_name = app_registration['name']
                    if namespace in app_registration_name and 'Platform' in app_registration_name:
                        tenant_dict.update(dict([(app_registration_name, app_registration['client_id'])]))

                    if namespace in app_registration_name and 'Swagger' in app_registration_name:
                        tenant_dict.update(dict([(app_registration_name, app_registration['client_id'])]))

                    if namespace in app_registration_name and 'Babylon' in app_registration_name:
                        tenant_dict.update(dict([(app_registration_name, app_registration['client_id'])]))

            # Save to JSON file of the day
            helper.create_json_file(os.path.join(dir_output, namespace + '-properties.json'), tenant_dict)


# Get properties of all Workspaces in a given tenant
def workspaces_properties(cluster, dir_output, namespace):
    # Get:
    # - Organizations id
    # - Organizations name
    # - Solutions id
    # - Solutions name
    # - Solutions repository
    # - Solutions version
    # - Workspaces id
    # - Workspaces name
    # - Webapps url

    if cluster.is_namespace_tenant(namespace):

        # Get API version to know if authentication is Keycloak or Azure
        cosmotech_api_version = cluster.get_cosmotech_api_version(namespace)
        platform_version = cosmotech_api_version.split('.')[0]

        if int(platform_version) < 4:
            # Azure authentication

            azure_subcription_id = cluster.get_azure_subcription_id()
            print(azure_subcription_id)

            # azure = Azure(azure_subcription_id)

            # resource_group = azure.get_resource_group_from_storage_name(cluster.get_cosmotech_api_storage_account(namespace))

            # print(resource_group)
            # rg_ressources = azure.get_resource_group_resources(resource_group)
            # if not rg_ressources:
            #     print(f"error: empty resource group {resource_group}")
            # else:
            #     for rg_ressource in rg_ressources:
            #         print(f"{rg_ressource['type']} -> {rg_ressource['name']}")


        else:
            # Keyloak authentication
            # Get Keycloak credentials from dedicated Kubernetes secret
            keycloak_secret = cluster.get_secret_decoded(namespace, 'keycloak-babylon')
            keycloak = Keycloak(
                base_url        = 'https://' + cluster.get_cluster_url() + '/keycloak',
                realm           = namespace,
                client_id       = keycloak_secret.get('client_id', ''),
                client_secret   = keycloak_secret.get('client_secret', ''),
            )
            keycloak_token = keycloak.get_token()
            token = keycloak_token["access_token"]

        cosmotech_api = CosmotechAPI(
            url = cluster.get_cosmotech_api_url(namespace),
            token = token,
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
                        ("webapp_url",              "to do"),
                        ("inventory_date",          today),
                    ]
                    workspaces_dict.update(dict(properties))

            # Save to JSON file of the day
            helper.create_json_file(os.path.join(dir_output, workspace_id + '.json'), workspaces_dict)


# Create Markdown file containing a simple key/value table
def create_file_markdown_itemvalue(destination_dir, file_json, title):
    if os.path.exists(file_json):
        markdown = Markdown(file_json, title)
        file_md = os.path.join(destination_dir, os.path.basename(file_json).replace("json", "md"))
        with open(file_md, "w") as f:
            f.write(markdown.json_to_markdown_itemvalue())
            print(f"file created: {file_md}")


# Create Markdown file containing Helm Charts informations table
def create_file_markdown_helmcharts(destination_dir, file_json, title):
    if os.path.exists(file_json):
        markdown = Markdown(file_json, title)
        file_md = os.path.join(destination_dir, os.path.basename(file_json).replace("json", "md"))
        with open(file_md, "w") as f:
            f.write(markdown.json_to_markdown_helmchart())
            print(f"file created: {file_md}")


# Print help
def help():
    text = """
Automatic inventory of Cosmo Tech platforms

Usage: python -m main [OPTION]

    --once      run a single inventory
    --job       run job based inventories (every APINV_RUN_FREQUENCY minutes)
-h, --help      display this help message
"""
    print(text)


# Launch a job
def job():
    print(f"job started {datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}")
    main()
    print(f"job finished {datetime.today().strftime('%Y-%m-%d_%H-%M-%S')}")


if __name__ == "__main__":
    # Ensure an argument is provided
    try:
        option = sys.argv[1]
    except:
        option = ''
        print("missing operand\nTry with '--help' for more information.")

    # Run a single inventory
    if option in ['--once']:
        main()

    # Run job based inventories
    elif option in ['--job']:
        APINV_RUN_FREQUENCY = int(os.getenv('APINV_RUN_FREQUENCY', 1440)) # default is 24 hours
        min_run_allowed = 10

        if APINV_RUN_FREQUENCY >= min_run_allowed:
            schedule.every(APINV_RUN_FREQUENCY).minutes.do(job)
        else:
            print(f"error: job frequency has been set as {APINV_RUN_FREQUENCY} but cannot be inferior as {min_run_allowed} minutes")
            exit()

        print('inventory job started')

        # launch inventory a first time
        main()

        while True:
            # Get next job timer
            job_time_of_next_run = schedule.next_run()
            job_time_now = datetime.now()
            job_time_remaining = job_time_of_next_run - job_time_now

            print(f"next job will run in {job_time_remaining}")

            schedule.run_pending()
            time.sleep(10)

    elif option in ['-h','--help']:
        help()
