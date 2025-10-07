SELECT 
    CAST(metadata AS STRUCT(
        name VARCHAR, 
        uid VARCHAR, 
        namespace VARCHAR, 
        creation_timestamp VARCHAR, 
        labels MAP(VARCHAR, VARCHAR)
    )) as metadata,
    
    CAST(subjects AS STRUCT(
        api_group VARCHAR, 
        kind VARCHAR, 
        name VARCHAR, 
        namespace VARCHAR
    )[]) as subjects,
    
    CAST(role_ref AS STRUCT(
        api_group VARCHAR, 
        kind VARCHAR, 
        name VARCHAR
    )) as role_ref,
    
    kind,
    _dlt_load_id,
    _dlt_id
    
FROM {{ source('k8s_raw', 'role_bindings') }}