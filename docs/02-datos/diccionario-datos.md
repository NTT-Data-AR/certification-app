# Diccionario de datos

## collaborator

| Campo | Tipo | Clasificacion |
| --- | --- | --- |
| collaborator_id | uuid | Interno |
| employee_number | text | Personal |
| email | text | Personal |
| display_name | text | Personal |
| business_unit_id | uuid | Interno |
| manager_id | uuid | Personal |
| employment_status | text | Interno |

## certification_record

| Campo | Tipo | Clasificacion |
| --- | --- | --- |
| record_id | uuid | Interno |
| collaborator_id | uuid | Personal |
| certification_id | uuid | Interno |
| credential_id | text | Personal/Interno |
| issue_date | date | Personal |
| expiration_date | date | Personal |
| status | text | Interno |
| source_system | text | Interno |

## audit_log

| Campo | Tipo | Clasificacion |
| --- | --- | --- |
| actor_id | text | Personal/Interno |
| action | text | Interno |
| entity_type | text | Interno |
| before_data | jsonb | Confidencial |
| after_data | jsonb | Confidencial |
