# Modelo logico

## Principios

UUIDs, catalogos controlados, soft delete por estado, auditoria separada, linaje obligatorio, normalizacion de catalogo y registros.

## Entidades

| Entidad | Proposito |
| --- | --- |
| business_unit | Unidad organizativa |
| collaborator | Colaborador y datos minimos |
| professional_role | Rol profesional |
| vendor | Proveedor de certificacion |
| certification | Catalogo |
| role_certification_requirement | Requerimientos por rol |
| certification_assignment | Asignacion objetivo |
| certification_record | Certificacion obtenida |
| evidence_document | Evidencia |
| validation_event | Decision |
| exception_waiver | Excepcion |
| notification | Alerta |
| audit_log | Auditoria |
| migration_batch | Lote de migracion |
| data_quality_issue | Incidencia de calidad |
| ai_conversation | Sesion IA |
| ai_tool_invocation | Tool ejecutada |

## Indices

email, employee_number, certification vendor/name, record collaborator/status, expiration_date, assignment assignee/status/due_date, audit entity/date, tool conversation/date.
