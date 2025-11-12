{{ config(materialized='table') }}

WITH kind_lookup AS (
    SELECT id, "name" FROM {{ source('bloodhound_pg', 'kind') }}
)
SELECT 
    n._dlt_load_id,
    n._dlt_id,
    n.id,
    n.graph_id,
    n.kind_ids,
    CAST(n.properties AS MAP(VARCHAR, VARCHAR)) as properties,
    (
        SELECT array_agg(k.name ORDER BY k.id)
        FROM kind_lookup k
        WHERE k.id = ANY(CAST(n.kind_ids AS BIGINT[]))
    ) as kind_names
FROM {{ source('bloodhound_pg', 'node') }} n