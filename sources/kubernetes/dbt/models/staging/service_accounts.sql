SELECT 
    CAST(metadata AS STRUCT(
        name VARCHAR, 
        uid VARCHAR, 
        namespace VARCHAR, 
        creation_timestamp VARCHAR, 
        labels MAP(VARCHAR, VARCHAR)
    )) as metadata,
    
    CAST(secrets AS STRUCT(
        name VARCHAR
    )[]) as secrets,
    
    automount_service_account_token,
    exists,
    kind,
    _dlt_load_id,
    _dlt_id
    
FROM {{ source('k8s_raw', 'service_accounts') }}