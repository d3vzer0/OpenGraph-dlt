{{ config(materialized='table') }}

SELECT distinct(policy_arn) FROM {{ source('aws', 'policy_attachments') }} 