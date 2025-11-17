# WIP: OpenGraph-dlt (Data Load Tool) collectors
A lightweight CLI for collecting service-specific resources and turning it into OpenGraph/BloodHound datasets. The long–term goal is to plug in multiple collectors; Kubernetes was the first source and serves as the reference implementation for future integrations. The kubernetes collector makes use of an (embedded) DuckDB database, which may not be needed for your usecase :) 

[<img src="https://github.com/user-attachments/assets/542d70b6-52ea-49ee-b700-447d55704982">](https://github.com/d3vzer0/OpenGraph-dlt) 


## What’s in the box?
- Python dlt-powered extract pipelines – exposes both raw resources and the OpenGraph transformer set;
- Reusable OpenGraph destination – can either batch results into local (OpenGraph) JSON files or push them straight into BloodHound via its upload API;
- Typer CLI – commands under cli/orchestrate the typical collect → lookup → convert workflow.

| Service | Scope | State |
|---|---|---|
| Kubernetes | Collects all (custom) resources types with additional node enrichment for specific resources (see sources/kubernets/models/k8s/*) | 90% |
| AWS | Primarily IAM, with generic nodes for common resource types discovered via AWS Resource Explorer | 60% |
| Rapid7 InsightVM | Collects assets + their vulnerabilties and vulnerability details. Sync vulnerabilities as nodes and uses the BloodHound source to match with existing hostnames to connect edges to computers | 100% |
| BloodHound| Stores all nodes and kinds in a dedicated duckdb database as an efficient lookup for other collectors, can be synced via a direct PG connection or using Cypher queries via the API| 100% |


## Installation
```bash
pipx install git+https://github.com/d3vzer0/OpenGraph-dlt.git
```

## Dev prerequisites
1. Python 3.12+
2. Option 1: Install dependencies manually
```bash
# Create a virtual environment
python -m venv .venv
# Activiate venv
source .venv/bin/activate
# Install dependencies
pip install
```
3. Option 2: Use UV to initiate the project/dependenceis

## Getting started
### 0. Configure config.toml
Configure the dlt config.toml with the apropriate values. Each source collector has it's own requirements, these will be displayed by DLT when running a collector. Create a config file in <project_root>/.dlt/config.toml with at least the following contents:

```
[extract]
workers=10 # The amount of parallel workers for collection
```

### 1. Configure required secrets
#### 1.1 Kubernetes
Kubernetes authentication is handled via the system's kubeconfig.

#### 1.2 AWS
AWS authentication is handled via the system's AWS CLI session

#### 1.3 Rapid7
Apply the following configuration to <project_root>/.dlt/secrets.toml
```bash
[sources.source.rapid7_source]
username = "your_user_here"
password = "your_password_here"
host = "https://ip_here:3780"
```

Or set the source config as environment variables via
```bash
SOURCES__SOURCE__RAPID7_SOURCE__PASSWORD=...
SOURCES__SOURCE__RAPID7_SOURCE__USERNAME=...
SOURCES__SOURCE__RAPID7_SOURCE__HOST=....
```
#### 1.4 BloodHound (API-based sync)
Apply the following configuration to  <project_root>/.dlt/secrets.toml
```bash
[sources.source.bloodhound_source]
token_key = "your_api_token_here"
token_id = "your_token_id_here"
host = "your_bh_url_here, ex. http://localhost:8080"
```

Or set the source config as environment variables via
```bash
SOURCES__SOURCE__BLOODHOUND_SOURCE__TOKEN_KEY=...
SOURCES__SOURCE__BLOODHOUND_SOURCE__TOKEN_ID=...
SOURCES__SOURCE__BLOODHOUND_SOURCE__HOST=....
```

### 1. Collecting resources
The `collect` CLI pulls raw objects from the source and stores them as Parquet/JSONL on the local filesystem. The service-specific collector additionally generates a DuckDB lookup used during graph conversion.

```console
# If opengraph-dlt was build/installed as a package
$ opengraph collect <service> [OPTIONS] OUTPUT_PATH

# If you're running opengraph-dlt directly from the source
$ python -m opengraph_dlt.main collect <service> OUTPUT_PATH 
```
**Arguments**:
* `OUTPUT_PATH`: Where the <service> resources will be saved in parquet/jsonl format [required]

This will run the <service> collector and writes one file per resource under ./output/<service>/<resource>/. Additionally a lookup database is generated, containing key fields from the raw files.

## 2. Convert to OpenGraph
Once the raw dataset exists, convert it into OpenGraph with the sync or convert CLI:

```console
# If opengraph-dlt was build/installed as a package
$ convert <service> [OPTIONS] INPUT_PATH OUTPUT_PATH

# If you're running opengraph-dlt directly from the source
$ python -m opengraph_dlt.main convert <service> INPUT_PATH OUTPUT_PATH
```
**Arguments**:
* `INPUT_PATH`: Where the <service> resources were saved by the collect command (parquet/jsonl) [required]
* `OUTPUT_PATH`: Where the <service> graph will be stored in OpenGraph format [required]
This will read the staged dataset from the specified path, generate the OpenGraph format and save the file(s), depending on the batch size, to OUTPUT_PATH/kubernetes-<batch-hash>.json


## Project Layout
```
destinations/opengraph/        # OpenGraph destination + BloodHound client
sources/kubernetes/            # Kubernetes resources, transformers, models
sources/rapid7/                # InsightVM resources, transformers, models
sources/aws/                   # AWS resources, transformers, models
sources/bloodhound/            # BloodHound resources to generate lookup(s)
cli/                           # Typer apps for collection and conversion
```

## Configuration Notes
Python's dlt configuration (destination paths, batch sizes, secrets) can live in .dlt/config.toml or environment variables.
