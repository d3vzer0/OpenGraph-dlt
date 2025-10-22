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
| BloodHound | Stores all nodes and kinds in a dedicated duckdb database as an efficient lookup for other collectors | 100% |

## Prerequisites
1. Python 3.12+, access to a Kubernetes cluster and optionally BloodHound API tokens (if syncing directly)
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
Configure the dlt config.toml with the apropriate values. Create a config file in <project_root>/.dlt/config.toml with the following contents:

```
[extract]
workers=10 # The amount of parallel workers for collection

[sources.source.kubernetes_resources.cluster]
cluster = "colima" # The name of your kubernetes cluster/name for this collector
```

### 1. Collecting resources
The `collect` CLI pulls raw objects from a kubernetes cluster and stores them as Parquet/JSONL on the local filesystem. The kubernetes collector additionally generates a DuckDB lookup used during graph conversion.

```console
$ collect kubernetes [OPTIONS] OUTPUT_PATH
```
**Arguments**:
* `OUTPUT_PATH`: Where the kubernetes resources will be saved in parquet/jsonl format [required]

This will run the kubernetes collector and writes one file per resource under ./output/kubernetes/<resource>/. Additionally a lookup database is generated, containing key fields (kind, name, namespace) from the raw files.

## 2. Convert to OpenGraph
Once the raw dataset exists, convert it into OpenGraph with the sync or convert CLI:

```console
$ convert kubernetes [OPTIONS] INPUT_PATH OUTPUT_PATH
```
**Arguments**:
* `INPUT_PATH`: Where the kubernetes resources were saved by the collect command (parquet/jsonl) [required]
* `OUTPUT_PATH`: Where the kubernetes graph will be stored in OpenGraph format [required]
This will read the staged dataset from the specified path, generate the OpenGraph format and save the file(s), depending on the batch size, to OUTPUT_PATH/kubernetes-<batch-hash>.json


## Project Layout
```
destinations/opengraph/        # OpenGraph destination + BloodHound client
sources/kubernetes/            # Kubernetes resources, transformers, models
cli/                           # Typer apps for collection and conversion
```

## Configuration Notes
Python's dlt configuration (destination paths, batch sizes, secrets) can live in .dlt/config.toml or environment variables.
Adjust kube_config/cluster arguments in collect.py and sync.py if you target different clusters.
