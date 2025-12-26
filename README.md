# Cosmo Tech automatic deployments inventory

This program intends to list existing deployments of Cosmo Tech tenants.

It will reach Kubernetes clusters to get the list below:
- Kubernetes clusters (names, versions, regions, URL)
- Cosmo Tech API objects (IDs & names of organizations, solutions & workspaces)
- Helm Charts (names, versions, services URL)

<br>

Inventory of the day is stored in a dedicated directory and is available in markdown format.

## How to
### Get Kubernetes clusters contexts
> This program uses a dedicated file `_kubeconfig` file instead of the default $USER/.kube/config file.
* Get contexts
	* AKS
		```
		az aks get-credentials --resource-group CLUSTER_RESOURCE_GROUP --name CLUSTER_NAME --file _kubeconfig
		```

### Run from source
* clone current repo
	```
	git clone git@github.com:Cosmo-Tech/apinventory.git && cd apinventory
	```
* python venv
	* install
		```
		python -m venv .venv
		```
	* activate
		```
		source .venv/bin/activate
		```
	* install requirements
		```
		python -m pip install -r requirements.txt
		```
* run
	```
	python -m main
	```

### Run from Docker
* get docker-compose.yaml
	```
	wget https://raw.githubusercontent.com/Cosmo-Tech/apinventory/refs/heads/main/docker-compose.yaml
	```
	```
	docker compose up -d
	```

## Inventory details
### Kubernetes cluter
> Page name is `[cluster] cluster_name`

#### Cluster properties
| Item     | Value     |
|----------|-----------|
| Name	   | *name*    |
| Version  | *version* |
| Region   | *region*  |
| URL      | *url*     |
| Keycloak | *url*     |
| Grafana  | *url*     |
| Harbor   | *url*     |

#### Cluter-wide Helm Charts
| Namespace      | Name      | Chart version | App version  |
|----------------|-----------|---------------|--------------|
| 1. *namespace* | 1. *name* | 1. *version*  | 1. *version* |
| 1. *namespace* | 2. *name* | 2. *version*  | 2. *version* |
| 1. *namespace* | n. *name* | n. *version*  | n. *version* |

### Tenant
> Page name is `[tenant] tenant_name`

#### Tenant properties
| Item           | Value            |
|----------------|------------------|
| Swagger URL    | *url*            |

#### Tenant Helm Charts
| Namespace      | Name      | Chart version | App version  |
|----------------|-----------|---------------|--------------|
| 1. *namespace* | 1. *name* | 1. *version*  | 1. *version* |
| 1. *namespace* | 2. *name* | 2. *version*  | 2. *version* |
| 1. *namespace* | n. *name* | n. *version*  | n. *version* |

### Workspace
> Page name is `[workspace] workspace_name`

#### Workspace properties
| Item                 | Value        |
|--------------------- |--------------|
| tenant_name          | *name*       |
| organization_id      | *id*         |
| workspace_id         | *id*         |
| solution_id          | *id*         |
| organization_name    | *name*       |
| workspace_name       | *name*       |
| solution_name        | *name*       |
| solution_repository  | *repository* |
| solution_version     | *version*    |
| webapp_url           | *url*        |
| inventory_date       | *date*       |

## Developers
Must be able to read any API, and we filter what we need

Needs:
- Github API (Terraform repositories tags)
- Kubernetes API (cluster name, namespaces)
	- seamless Kubernetes API with contexg+kubectl ?
	OR
	- Azure API for AKS infos ?
	- AWS API for EKS infos ?
	- GCP API for GKE infos ?
- Cosmo Tech API (org, solution, workspaces)

Goal:
- Terraform modules
	- cluster 
		- type (AKS, EKS, GKE, KOB)
		- version
	- common
		- version
		- list components (keycloak, velero, vault, grafana etc)
	- tenant
		- version
		- list components (api, redis, argo, psql, seaweedfs etc)

- Kubernetes cluster
	- cluster name
	- version
	- public IP
	- region
	- provider infos
			- AWS
				- Account ID
				- Resource Group name
				- VPC ID
			- Azure
				- Subscription ID
				- Resource Group name
				- Virtual network ID
			- GCP
				- Organization ID
				- Project ID
				- VPC ID


- Cosmo Tech tenants
	- namespaces
		- name
		- charts (webapp, api etc...)
		- security list ?

- Cosmo Tech API
	- organizations
		- name
		- ACL
	- solutions
		- name
		- ACL
		- simulator version
	- workspaces
		- name
		- ACL
		- superset dashboard id ?
		- superset reports id ?

<br>
<br>
<br>

Made with :heart: by Cosmo Tech DevOps team