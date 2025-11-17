{{ config(materialized='table') }}

SELECT * FROM {{ source('aws', 'resources') }} 
UNION ALL
SELECT arn, account_id AS owning_account_id, 'global' AS region, 'iam:group' AS resource_type, 'iam' AS service, '{}' AS properties, create_date AS last_reported_at, group_name AS name, _dlt_id, _dlt_load_id FROM {{ source('aws', 'groups') }}
UNION ALL
SELECT arn, account_id AS owning_account_id, 'global' AS region, 'iam:user' AS resource_type, 'iam' AS service, '{}' AS properties, create_date AS last_reported_at, user_name AS name, _dlt_id, _dlt_load_id FROM {{ source('aws', 'users') }}
UNION ALL
SELECT arn, account_id AS owning_account_id, 'global' AS region, 'iam:role' AS resource_type, 'iam' AS service, '{}' AS properties, create_date AS last_reported_at, role_name AS name, _dlt_id, _dlt_load_id FROM {{ source('aws', 'roles') }}
UNION ALL
SELECT arn, account_id AS owning_account_id, 'global' AS region, 'iam:policy' AS resource_type, 'iam' AS service, '{}' AS properties, create_date AS last_reported_at, policy_name AS name, _dlt_id, _dlt_load_id FROM {{ source('aws', 'policies') }}
