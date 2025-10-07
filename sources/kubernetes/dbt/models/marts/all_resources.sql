{{
  config(
    materialized='table'
  )
}}

SELECT 
    kind,
    metadata.name as name,
    metadata.namespace as namespace
FROM {{ ref('pods') }}

UNION ALL

SELECT 
    kind,
    metadata.name as name,
    metadata.namespace as namespace
FROM {{ ref('roles') }}

UNION ALL

SELECT 
    kind,
    metadata.name as name,
    metadata.namespace as namespace
FROM {{ ref('role_bindings') }}

UNION ALL

SELECT 
    kind,
    metadata.name as name,
    metadata.namespace as namespace
FROM {{ ref('unmapped') }}

UNION ALL

SELECT 
    kind,
    metadata.name as name,
    metadata.namespace as namespace
FROM {{ ref('cluster_roles') }}

UNION ALL

SELECT 
    kind,
    metadata.name as name,
    metadata.namespace as namespace
FROM {{ ref('cluster_role_bindings') }}

UNION ALL

SELECT 
    kind,
    metadata.name as name,
    metadata.namespace as namespace
FROM {{ ref('service_accounts') }}