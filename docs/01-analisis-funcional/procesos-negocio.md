# Procesos de negocio

## Mapa

```mermaid
flowchart TD
  C[Catalogo] --> R[Requerimientos]
  H[Colaboradores HR] --> A[Asignaciones]
  R --> A
  A --> E[Evidencia]
  E --> V[Validacion]
  V --> W[Vigencia y vencimientos]
  W --> N[Notificaciones]
  W --> BI[Reporting]
  V --> AUD[Auditoria]
```

## Estados

Asignacion: DRAFT, ASSIGNED, IN_PROGRESS, SUBMITTED, COMPLETED, REJECTED, CANCELLED. Registro: REPORTED, PENDING_VALIDATION, VALIDATED, REJECTED, ACTIVE, EXPIRING_SOON, EXPIRED, REVOKED, RENEWED.
