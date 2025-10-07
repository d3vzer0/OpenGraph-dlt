SELECT
    CAST(metadata AS STRUCT(
        name VARCHAR, 
        uid VARCHAR, 
        labels MAP(VARCHAR, VARCHAR)
    )) as metadata,
    kind,
    _dlt_load_id,
    _dlt_id
    
FROM {{ source('k8s_raw', 'nodes') }}
