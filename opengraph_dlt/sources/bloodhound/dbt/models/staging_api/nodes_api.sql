{{ config(
    materialized='table',
    post_hook = [
        "{{ ensure_embeddings_table() }}",
        "INSTALL vss;",
        "LOAD vss;",
        "SET GLOBAL hnsw_enable_experimental_persistence = true;",
        "CREATE INDEX IF NOT EXISTS ip_idx ON {{ source('bloodhound_api', 'embeddings') }} USING HNSW (embedding) WITH (metric = 'ip');"
    ]
    ) 
}}

SELECT 
    n._dlt_load_id,
    n._dlt_id,
    n.object_id,
    n.kind,
    n.label,
    n.last_seen,
    CAST(n.kinds AS VARCHAR[]) as kind_names,
    CAST(n.properties AS MAP(VARCHAR, VARCHAR)) as properties
FROM {{ source('bloodhound_api', 'nodes') }} n