{{ config(materialized='table', alias='resources_with_definitions') }}

select
    r.name,
    r.kind,
    r.namespace,
    rd.singular_name,
    rd.name as definition
from {{ source('kubernetes', 'resources') }} r
left join {{ source('kubernetes', 'resource_definitions') }} rd
    on r.kind = rd.kind