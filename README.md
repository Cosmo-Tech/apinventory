# Automatic inventory of Cosmo Tech platforms

This program intends to list existing deployments of Cosmo Tech platforms.

It will reach Kubernetes clusters to informations from:
* Kubernetes clusters
* Cosmo Tech API
* Azure resources

> [Inventory details are listed below](#inventory-details)

Inventory of the day is stored in a dedicated directory, in JSON format, and converted to Markdown format to a unique directory.

## How to
### Get Kubernetes clusters contexts
> This program uses a dedicated file instead of the default `$USER/.kube/config` file. \
> It can be configured in `.env` file (configured as `_kubeconfig` in `.env.example`)
* Get contexts
	* Azure AKS
		```
		az aks get-credentials --resource-group CLUSTER_RESOURCE_GROUP --name CLUSTER_NAME --file _kubeconfig
		```
	* AWS EKS
		```
		sh -c 'aws eks update-kubeconfig --name $0 --alias $0 --kubeconfig _kubeconfig' CLUSTER_NAME
		```

### Run from source
* Clone current repo
	```
	git clone git@github.com:Cosmo-Tech/apinventory.git && cd apinventory
	```
* Get `.env`
	```
	curl https://raw.githubusercontent.com/Cosmo-Tech/apinventory/refs/heads/main/.env.example -o .env
	```
* Python venv
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
* Start
	```
	python -m main
	```

### Run from Docker
* Get `docker-compose.yaml`
	```
	curl -O https://raw.githubusercontent.com/Cosmo-Tech/apinventory/refs/heads/main/docker-compose.yaml
	```
* Get `.env`
	```
	curl https://raw.githubusercontent.com/Cosmo-Tech/apinventory/refs/heads/main/.env.example -o .env
	```
* Fill `.env` according to your needs
* Start
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
| Item               | Value            |
|--------------------|------------------|
| Swagger URL        | *url*            |
| *Azure resource 1* | *name*           |
| *Azure resource 2* | *name*           |
| *Azure resource n* | *name*           |

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



## Developpers
### Classes
* src/api/Cosmotech/CosmotechAPI
  * all platforms versions
  * connect to a Cosmo Tech API and list objects from it
* src/api/Kubernetes/KubeCluster
  * all platforms versions
  * connect to a Kubernetes cluster and list differents resources from it
* src/api/Keycloak/Keycloak
  * v4/5 platforms only
  * generate a token from the platform Keycloak to use on Cosmo Tech API
* src/api/Azure/Azure
  * v3 platforms only
  * connect to Azure and list SaaS resoruces
* src/api/Vault/Vault
  * v3 platforms only
  * connect to the Vault of the platform to retrieve access for Azure

<br>
<br>
<br>

Made with :heart: by Cosmo Tech DevOps team
