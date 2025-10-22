{{ config(materialized='table') }}

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