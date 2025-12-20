# Cosmo Tech automatic deployments inventory

This program intends to list existing deployments of Cosmo Tech tenants.

It will reach Kubernetes clusters to get the list below:
- Kubernetes clusters (names, versions, regions)
- Cosmo Tech API objects (IDs & names of organizations, solutions & workspaces)
- Helm Chart (names, versions)

<br>

Inventory of the day is stored in a dedicated directory and is available in markdown format.

## How to
### Use from source
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

### Use with Docker
* get docker-compose.yaml
	```
	wget https://raw.githubusercontent.com/Cosmo-Tech/apinventory/refs/heads/main/docker-compose.yaml
	```
	```
	docker compose up -d
	```

### Setup cron job
* to do








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