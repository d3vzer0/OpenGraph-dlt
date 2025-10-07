{{
  config(
    enabled=if_table_exists('k8s_raw', 'statefulsets')
  )
}}

SELECT 
    TRY_CAST(metadata AS STRUCT(
        name VARCHAR, 
        uid VARCHAR,
        namespace VARCHAR,
        creation_timestamp VARCHAR, 
        labels MAP(VARCHAR, VARCHAR)
    )) as metadata,
    TRY_CAST(spec AS STRUCT(
        template STRUCT(
            spec STRUCT(
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
                )[],
                volumes STRUCT(
                    name VARCHAR,
                    host_path STRUCT(
                        path VARCHAR
                    )
                )[]
            )
        )
    )) as spec,
    kind,
    _dlt_load_id,
    _dlt_id
FROM {{ source('k8s_raw', 'statefulsets') }}