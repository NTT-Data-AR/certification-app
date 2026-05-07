# Arquitectura backend

## Componentes

| Componente | Responsabilidad |
| --- | --- |
| API/BFF | Entrada, auth, rate limit |
| Certification Service | Catalogo y registros |
| Validation Service | Aprobacion/rechazo |
| Notification Service | Alertas |
| Reporting Service | Agregados |
| Data Quality Service | Reglas DQ |
| Audit Service | Eventos |
| AI Tool Adapter | Tools seguras |

## Patrones

Transacciones atomicas, idempotencia, auditoria transversal, validacion backend y storage separado para evidencias.
