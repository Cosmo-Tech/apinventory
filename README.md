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
