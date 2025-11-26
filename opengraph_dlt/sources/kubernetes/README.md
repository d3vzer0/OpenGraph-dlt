# Kubernetes Collector

This module turns a Kubernetes cluster into OpenGraph assets. It can
dump raw API objects, build a DuckDB lookup used for graph enrichment and convert
resources to OpenGraph for BloodHound.

## Components

- `collect.py` – DLT source which collect resources from a Kubernetes cluster using the Kubernetes API (e.g., `kubernetes_resources`);
- `transform.py` - DLT source which loads the collected resource files and runs the OpenGraph transformation (eg. `kubernetes_opengraph`);
- `lookup.py` – DuckDB database used to look up resource metadata during graph generation (`KubernetesLookup`);
- `models/` – Pydantic schemas that normalize Kubernetes API responses and describe graph nodes/edges;
- `dbt/` – Models that transform/normalize the lookup database;
- `icons.py` Contains the icons used for each node type in BloodHound.


## Workflow
1. **Collect raw resources** – call the collector to save cluster data to
   filesystem storage (JSONL gz files).
2. **Build lookup (ie. preprocess)** – ingest raw files into DuckDB + dbt models for resolving
   names, namespaces, and resource definitions.
3. **Convert or sync** – turn collected data into OpenGraph graph entries for
   local inspection or direct sync to a destination.

### 1. Collect raw data
```
opengraph collect kubernetes ./output
```

- Reads the active kubeconfig context to discover the cluster name + auth settings
- Runs `kubernetes_resources()` (see `source.py`) which queries:
  Pods, Nodes, Namespaces, Deployments, ReplicaSets, StatefulSets, DaemonSets,
  Roles/RoleBindings, ClusterRoles/ClusterRoleBindings, ServiceAccounts, custom
  resource definitions, discovered API groups, inferred volumes etc
- Writes resources to `./<specified_path>/kubernetes/<resource>/<timestamp>/*.jsonl.gz`.
- You can re-run; use `write_disposition="replace"` to refresh the dataset.


### 2a. Convert to OpenGraph files
```
opengraph convert kubernetes ./output/kubernetes ./graph
```

- Requires an up-to-date `lookup.duckdb`.
- Uses `kubernetes_opengraph` to read the collected files (`bucket_url` argument) and yields `GraphEntries` into the file destination created by the `destinations/opengraph` methods

### 3b. Sync directly to BloodHound
```
opengraph sync kubernetes ./output/kubernetes
```

- Similar to converting, but the `dlt.pipeline` destination is `bloodhound()`
  which pushes nodes/edges via the configured BloodHound API

## Tips

- The collector assumes the kubeconfig context’s cluster name;
- For offline troubleshooting, inspect the JSONL files directly and/or query `lookup.duckdb` with DuckDB CLI or UI. You can use the following SQL query to import the JSON files directly: `SELECT * FROM read_json('output/kubernetes/<resource_type>/**/*.jsonl.gz');`.