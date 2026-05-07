# Mapping Power Apps

| Power Apps/Legacy | Modelo objetivo | Regla |
| --- | --- | --- |
| Employee/User | collaborator | Normalizar contra HR |
| Certification Name | certification | Resolver vendor+nombre |
| Provider | vendor | Crear/validar |
| Issue Date | record.issue_date | ISO date |
| Expiry Date | record.expiration_date | Validar fechas |
| Credential ID | record.credential_id | Mantener si aplica |
| Attachment/Link | evidence.storage_uri | Storage seguro |
| Status | record.status | Mapear dominio |
| Approver | validation_event.validator_id | Resolver identidad |
