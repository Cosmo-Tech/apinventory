
from datetime import datetime
import os
import json
import yaml # useful for kubeconfig files
import shutil
import schedule
import time
from dotenv import load_dotenv

from src.api.Kubernetes import KubeCluster
from src.api.Keycloak import Keycloak
from src.api.Cosmotech import CosmotechAPI
from src.views.Markdown import Markdown

import src.helper as helper


now = datetime.today().strftime('%Y-%m-%d')
now_detailed = datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

dir_inventory            = "_inventory"
dir_today_inventory      = os.path.join(dir_inventory, now)
dir_today_inventory_json = os.path.join(dir_today_inventory, "json")
dir_today_inventory_md   = os.path.join(dir_inventory, "markdown")

kubeconfig_file = '_kubeconfig'


def main():

    # Prepare structure of the day
    if os.path.exists(dir_today_inventory):
        shutil.rmtree(dir_today_inventory)
    for dir in [dir_inventory, dir_today_inventory, dir_today_inventory_json, dir_today_inventory_md]:
        if not os.path.exists(dir):
            os.makedirs(dir)

    for context in get_all_contexts(kubeconfig_file):
        cluster = KubeCluster(kubeconfig_file, context)
        cluster_name = cluster.get_cluster_name()

        # JSON structure of the day for clusters
        dir_cluster = os.path.join(dir_today_inventory_json, cluster_name)
        if not os.path.exists(dir_cluster):
            os.makedirs(dir_cluster)

        # Generate inventories
        cluster_properties(kubeconfig_file, context, dir_cluster)
        all_helmcharts(kubeconfig_file, context, dir_cluster)
        tenants_properties(kubeconfig_file, context, dir_cluster)

        # Markdown structure of the day for clusters
        dir_cluster_md = os.path.join(dir_today_inventory_md, cluster_name)
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

                # Generate inventories
                workspaces_properties(kubeconfig_file, context, dir_tenant, namespace)

                dir_tenant_md = os.path.join(dir_today_inventory_md, cluster_name, namespace)
                if not os.path.exists(dir_tenant_md):
                    os.makedirs(dir_tenant_md)

                # Create Markdown files from JSON for tenants
                create_file_markdown_itemvalue(dir_cluster_md, os.path.join(dir_cluster, f"{namespace}-properties.json"), f"Tenant properties")
                create_file_markdown_helmcharts(dir_cluster_md, os.path.join(dir_cluster, f"{namespace}-helmcharts.json"), f"Tenant Helm Charts")
                helper.merge_files(os.path.join(dir_cluster_md, f"{namespace}-helmcharts.md"), os.path.join(dir_cluster_md, f"{namespace}-properties.md"))
                helper.delete_file(os.path.join(dir_cluster_md, f"{namespace}-helmcharts.md"))

                # Create Markdown files from JSON for workspaces
                for workspace_file in os.listdir(dir_tenant):
                    workspace_name = workspace_file.replace('.json', '')
                    create_file_markdown_itemvalue(dir_tenant_md, os.path.join(dir_tenant, workspace_file), f"Workspace properties")


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


# Get properties of all tenants in a cluster
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


# Get properties of all Workspaces in a given tenant
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
    # - Webapps url

    cluster = KubeCluster(kubeconfig_file, context)
    if cluster.is_namespace_tenant(namespace):

        # Get Keycloak credentials from dedicated Kubernetes secret
        keycloak_secret = cluster.get_secret_decoded(namespace, 'keycloak-babylon')

        # Get a token from Keycloak with given credentials
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
                        ("webapp_url",              "to do"),
                        ("inventory_date",          now),
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


def job():
    print(f"task started {now_detailed}")
    main()
    print(f"task finished {now_detailed}")


if __name__ == "__main__":

    load_dotenv()
    run_minutes_frequence = int(os.getenv('run_minutes_frequence', 1440)) # default is 24 hours

    min_run_allowed = 15
    if run_minutes_frequence >= min_run_allowed:
        schedule.every(run_minutes_frequence).minutes.do(job)
    else:
        print(f"error: job frequence has been set as {run_minutes_frequence} but cannot be inferior as {min_run_allowed} minutes")
        exit()

    print('inventory job started')
    main() # launch inventory a first time
    while True:
        # Get next job timer
        job_time_of_next_run = schedule.next_run()
        job_time_now = datetime.now()
        job_time_remaining = job_time_of_next_run - job_time_now

        print(f"next job will run in {job_time_remaining}")

        schedule.run_pending()
        time.sleep(60)

