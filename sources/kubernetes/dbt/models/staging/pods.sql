-- models/staging/stg_pods.sql
SELECT 
    CAST(metadata AS STRUCT(
        name VARCHAR, 
        uid VARCHAR,
        namespace VARCHAR,
        creation_timestamp VARCHAR, 
        labels MAP(VARCHAR, VARCHAR),
        owner_references STRUCT(
            api_version VARCHAR,
            controller BOOLEAN,
            kind VARCHAR,
            name VARCHAR,
            uid VARCHAR
        )[]
    )) as metadata,
    
    CAST(spec AS STRUCT(
        node_name VARCHAR, 
        service_account_name VARCHAR, 
        containers STRUCT(
            image VARCHAR, 
            security_context STRUCT(
                allow_privilege_escalation BOOLEAN, 
                privileged BOOLEAN
            ), 
            volume_mounts STRUCT(
                mount_path VARCHAR, 
                name VARCHAR
            )[]
        )[]
    )) as spec,
    
    kind,
    _dlt_load_id,
    _dlt_id
    
FROM {{ source('k8s_raw', 'pods') }}