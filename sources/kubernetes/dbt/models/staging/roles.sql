SELECT 
    CAST(metadata AS STRUCT(
        name VARCHAR, 
        uid VARCHAR, 
        namespace VARCHAR,
        creation_timestamp VARCHAR, 
        labels MAP(VARCHAR, VARCHAR)
    )) as metadata,
    
    CAST(rules AS STRUCT(
        api_groups VARCHAR[], 
        resources VARCHAR[], 
        verbs VARCHAR[], 
        resource_names VARCHAR[]
    )[]) as rules,
    
    kind,
    _dlt_load_id,
    _dlt_id
    
FROM {{ source('k8s_raw', 'roles') }}