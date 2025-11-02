{{ config(materialized='table') }}

SELECT
    r.arn,
    r.role_name,
    r.role_id,
    r.account_id,
    CAST(stmt.key AS INTEGER) AS statement_index,
    json_extract_string(stmt.value, '$.Effect') as effect,
    json_extract_string(stmt.value, '$.Action') as action,
    CAST(json_extract(stmt.value, '$.Condition') AS MAP(VARCHAR, MAP(VARCHAR, VARCHAR))) as condition,
    CAST(json_extract(stmt.value, '$.Principal') AS MAP(VARCHAR, VARCHAR)) as principal
FROM {{ source('aws', 'roles') }} r,
     json_each(r.assume_role_policy_document, '$.Statement') AS stmt
