{{ config(materialized='table', alias='resources_with_definitions') }}

select
    r.name,
    r.kind,
    r.namespace,
    rd.singular_name,
    rd.name as definition
from {{ source('k8s_raw', 'resources') }} r
left join {{ source('k8s_raw', 'resource_definitions') }} rd
    on r.kind = rd.kind