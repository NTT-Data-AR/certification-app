# Glosario de Términos

Definiciones de términos clave del dominio y abreviaturas del proyecto.

---

## A

### ABAC (Attribute-Based Access Control)
Modelo de autorización basado en atributos (usuario, recurso, contexto). Más flexible que RBAC pero más complejo.
- **No usado en este proyecto.** Usamos RBAC (ver).

### Actor
Persona o sistema que ejecuta acciones en el sistema.
- Ejemplos: collaborator, manager, validator, owner, auditor, agente IA.

### Assignment (Asignación)
Certificación asignada a un colaborador por cumplir.
- **Tabla:** certification_assignment
- **Estados:** pending, completed, rejected, expired, waivered
- **Ejemplo:** "Manager asigna AWS SAA a John con vencimiento 2026-12-31"

### Auditoría
Log completo de todas las mutaciones (quién, qué, cuándo, por qué).
- **Tabla:** audit_log (append-only)
- **Immutable:** No se puede borrar ni modificar.

---

## B

### Backend
Servidor API REST que valida, persiste y audita.
- **Ubicación:** backend/
- **APIs:** POST, GET (REST)
- **DB:** PostgreSQL

### Business Unit (Unidad Organizativa)
Departamento, área o filial (ej: "Cloud Services", "Data Analytics").
- **Tabla:** business_unit
- **Jerárquica:** Puede tener parent_business_unit_id (relación con otra unidad).

---

## C

### Catálogo
Lista de certificaciones disponibles para asignar a colaboradores.
- **Tabla:** certification
- **Unique:** (vendor_id, name) - no pueden existir 2 certs iguales del mismo vendor.
- **Ejemplo:** "AWS Solutions Architect Associate" de vendor "Amazon".

### Certification Owner (Owner)
Rol responsable de mantener catálogo, reglas, requerimientos por rol.
- **Permisos:** certification:write:all, rules:write:all
- **Responsabilidad:** Decisiones sobre qué certs son requeridas.

### Colaborador
Empleado de NTT DATA.
- **Tabla:** collaborator
- **Unique:** employee_number, email
- **Fuente:** Sincronización desde HR.

### Confirmación (Confirmation)
Aprobación humana antes de que agente IA ejecute acción crítica.
- **Aplicable a:** Crear asignación, validar certificación, crear waiver.
- **Mecanismo:** Tool retorna status='pending_human_review', humano aprueba/rechaza.

### Correlation ID
UUID único por request HTTP que permite rastrear request → logs → auditoría.
- **Header:** X-Correlation-ID
- **Almacenado:** En audit_log.

---

## D

### Dashboard
Interfaz para visualizar estado de certificaciones.
- **Roles:** collaborator (sus certs), manager (equipo), owner (todas).
- **Métricas:** Activas, vencidas, próximas, pendientes.

### Data Quality Issue
Registro de dato inconsistente o problemático.
- **Tabla:** data_quality_issue
- **Ejemplo:** "email_duplicado para 2 colaboradores", "fecha expiración en futuro".

---

## E

### Evidence (Evidencia)
Documento que prueba que certificación fue obtenida.
- **Tabla:** evidence_document
- **Tipos:** PDF, JPG, PNG (archivo <= 50MB).
- **Almacenamiento:** S3 con presigned URLs.
- **Clasificación:** proof_of_completion, credential_id, registry_verification, other.

### Exception Waiver
Excepción: Certificación no es requerida para este colaborador.
- **Tabla:** exception_waiver
- **Razón:** "Experiencia equivalente", "Role cambió", etc.
- **Validez:** Período (valid_from, valid_to).

---

## F

### Fecha de Expiración (Expiration Date)
Cuándo vence una certificación.
- **Cálculo:** issue_date + (validity_months meses).
- **Estados:** active (hoy está en rango), expired (hoy > expiration_date).

### Fecha de Emisión (Issue Date)
Cuándo fue otorgada la certificación.
- **Validación:** Debe ser <= hoy.
- **Relación:** expiration_date >= issue_date.

---

## G

### Guardrail
Control de seguridad del agente IA.
- **Ejemplos:** PII minimization, prompt injection detection, tool allowlist, rate limiting.
- **Objetivo:** Evitar que agente haga daño.

---

## H

### Human-in-the-Loop
Humano aprueba acciones críticas del agente IA.
- **No aplica:** Lecturas (queries)
- **Aplica:** Escrituras (crear asignación, validar certificación)

---

## I

### Idempotencia
Acción que, si se ejecuta N veces, es equivalente a ejecutarla 1 vez.
- **Mecanismo:** Idempotency keys (UUID) en client.
- **Beneficio:** No hay duplicados si hay retries.

---

## J

### JWT (JSON Web Token)
Token de autenticación.
- **Formato:** header.payload.signature
- **Claims:** user_id, roles[], permissions[]
- **Expiry:** 1 hora máximo.

---

## K

### Knowledge Base
Datos aprobados para que agente IA acceda.
- **Incluye:** Procesos, reglas, FAQ, señales de mercado, reemplazos de certs.
- **Excluye:** PII, secretos, evidencias, datos personales.

---

## L

### Linaje de Datos
Rastrabilidad: de dónde vienen los datos.
- **Campos:** source_system (HR_IMPORT, MANUAL, RENEWAL, LEGACY_MIGRATION)
- **Auditoría:** Quién cambió, cuándo, por qué.

---

## M

### Manager
Rol que gestiona certificaciones de su equipo.
- **Permisos:** Ver equipo, crear asignaciones, NO validar.
- **Alcance:** Solo sus reportes directos.

### Minimización de PII
No exponer datos personales en APIs.
- **Ejemplos:**
  - Ocultar: email → "John D."
  - Ocultar: employee_number → solo en admin
  - Ocultar: credential_id → ocultar totalmente
  - Mostrar: nombre, rol, unidad.

### Migracion
Importar datos históricos desde Power Apps / web anterior.
- **Tabla:** migration_batch
- **Tracking:** Qué batch, cuándo, status.

---

## N

### Notificación
Alerta enviada a usuario (email, Teams, SMS).
- **Tabla:** notification
- **Tipos:** Asignación, validación, vencimiento, renovación.

---

## O

### Object Authorization
Validación: ¿El usuario puede acceder ESTE objeto específico?
- **Ejemplo:** Manager puede ver asignaciones de SU equipo, no de otros.
- **Diferente a:** Role authorization (¿tiene el rol?)

---

## P

### Permisos (Permissions)
Qué acciones puede hacer un rol.
- **Ejemplos:** certification:read:self, certification:write:all, validation:write.
- **Tabla:** Implícita en código (no BD).

### Presigned URL
URL temporal (15 minutos) para subir/descargar evidencias en S3.
- **Seguridad:** No exponemos credenciales AWS en cliente.
- **Flow:** Client solicita presigned → sube a URL → notifica backend.

### Proceso
Flujo de negocio documentado.
- **Ejemplos:** alta-certificacion, renovacion, validacion.
- **Ubicación:** docs/04-procesos/

---

## R

### RBAC (Role-Based Access Control)
Modelo de autorización por rol.
- **5 Roles:** collaborator, manager, validator, owner, auditor.
- **Permisos:** Cada rol tiene lista explícita de permisos.

### Record (Registro de Certificación)
Certificación obtenida por un colaborador.
- **Tabla:** certification_record
- **Diferente a:** Assignment (lo que se espera) vs Record (lo que se logró)
- **Estados:** active, expired, pending_validation, rejected, waivered

### Requerimiento Funcional (RF)
Feature que debe implementarse.
- **Formato:** RF-001, RF-002, ...
- **Ejemplo:** RF-006 = "Registrar certificación obtenida"

### Renovación
Obtener nueva versión de certificación próxima a vencer.
- **Precondición:** < 90 días para vencer, >= 14 días restantes.
- **Proceso:** 4 fases (detección, iniciación, carga, validación).

---

## S

### Soft Delete
Marcar como borrado sin eliminar físicamente.
- **Mecanismo:** status = 'deleted' (no DELETE SQL)
- **Ventaja:** Recuperable, auditable.

### Status (de record/assignment)
Estado actual.
- **Records:** active, expired, pending_validation, rejected, waivered.
- **Assignments:** pending, completed, rejected, expired, waivered.

---

## T

### Tool (del Agente IA)
API específica que agente IA puede invocar.
- **13 tools:** search_certifications, create_assignment, register_evidence, etc.
- **Allowlist:** Solo estos, no SQL directo.
- **Confirmación:** Tools de escritura requieren humano.

### Trazabilidad
Poder rastrear: quién hizo qué, cuándo, por qué.
- **Mecanismo:** Correlation ID → audit_log.
- **Matriz:** RF → Proceso → API → Test.

---

## U

### UUID (Universally Unique Identifier)
Identificador único (formato: 550e8400-e29b-41d4-a716-446655440000).
- **Ventaja:** Único globalmente, puede generarse en cliente (idempotencia).
- **Usado en:** Todos los IDs (PK en tablas).

---

## V

### Validación
Proceso de aprobar/rechazar certificación reportada.
- **Actor:** Validator (rol específico)
- **Decision:** Approved (pasa a activa) o Rejected (vuelve a pending)
- **Tabla:** validation_event

### Validador
Rol que aprueba/rechaza certificaciones.
- **Permisos:** validation:write
- **Responsabilidad:** Revisar evidencia, decidir si es válida.

### Vencimiento (Expiration)
Evento cuando certificación deja de ser válida.
- **Cálculo:** expiration_date < today → status = 'expired'
- **Alerta:** Sistema notifica 30d antes, 7d antes.

### Vigencia (Validity)
Cuánto tiempo es válida una certificación.
- **Medida:** months (ej: 36 meses)
- **Cálculo:** expiration = issue + validity_months

---

## W

### Waiver
Excepción (certificación no es requerida).
- **Tabla:** exception_waiver
- **Aprobación:** Owner autoriza.
- **Vigencia:** Período específico.

---

## Z

### (Ninguno)

---

## Abreviaturas

| Abrev. | Completo | Ejemplo |
|--------|----------|---------|
| API | Application Programming Interface | REST API |
| BD | Base de Datos | PostgreSQL BD |
| CRUD | Create, Read, Update, Delete | CRUD operations |
| FK | Foreign Key | assignment_id FK → assignment |
| GA | General Availability | Release GA |
| HR | Human Resources | HR system sync |
| IAM | Identity & Access Management | SSO / MFA |
| JWT | JSON Web Token | Bearer token |
| PII | Personally Identifiable Information | Email, SSN, phone |
| PK | Primary Key | certification_id PK |
| RBAC | Role-Based Access Control | 5 roles |
| RFC | Request For Comments | Design doc |
| RF | Requerimiento Funcional | RF-006 |
| SLA | Service Level Agreement | 10 días validación |
| SQL | Structured Query Language | PostgreSQL SQL |
| SSO | Single Sign-On | OAuth2 SSO |
| TLS | Transport Layer Security | HTTPS TLS 1.2+ |
| UUID | Universally Unique Identifier | 550e8400-... |

---

## Convenciones de Nombres

### Tablas
- Plural, snake_case: `certification_records`, `validation_events`
- Excepción: Roles singulares: `professional_role`

### Columnas
- Singular, snake_case: `record_id`, `validator_id`, `created_at`
- Booleanos prefijo `is_`: `is_active`, `is_deleted`
- Timestamps: `created_at`, `updated_at`, `occurred_at`, `decided_at`

### APIs
- Endpoints plural: `/certifications`, `/records`, `/assignments`
- Verbos HTTP: POST (crear), GET (leer), PUT (reemplazar), DELETE (borrar)
- Parámetros snake_case: `?unit_id=..., ?sort_by=...`

### Variables
- Código: camelCase: `collaboratorId`, `certificationName`
- BD: snake_case: `collaborator_id`, `certification_name`
- Constants: UPPER_SNAKE_CASE: `MAX_FILE_SIZE = 50_000_000`

### Archivos
- Documentos: kebab-case: `renovacion-certificacion.md`
- Código: snake_case: `certification_service.py`
- Clases: PascalCase: `CertificationService`, `ValidationEvent`

---

## Contexto por Rol

### Colaborador
- **Términos importantes:** Assignment, Record, Evidence, Vigencia, Vencimiento, Renovación
- **Documentos:** docs/04-procesos/alta-certificacion.md, docs/04-procesos/renovacion-certificacion.md

### Manager
- **Términos:** Assignment, Cobertura, Dashboard, Brecha (gap)
- **Documentos:** docs/04-procesos/asignacion-certificacion.md, docs/08-operacion/metricas-kpi.md

### Validator
- **Términos:** Evidence, Validación, Decision, Auditoría
- **Documentos:** docs/04-procesos/validacion-aprobacion.md, docs/05-seguridad-cumplimiento/auditoria.md

### Owner
- **Términos:** Catálogo, Requerimiento, Reglas, Waiver
- **Documentos:** docs/01-analisis-funcional/reglas-negocio.md, docs/04-procesos/soporte-excepciones.md

### Auditor
- **Términos:** Auditoría, Linaje, PII, Cumplimiento
- **Documentos:** docs/05-seguridad-cumplimiento/auditoria.md, docs/05-seguridad-cumplimiento/privacidad-datos.md

### AI Agent
- **Términos:** Tool, Confirmación, Knowledge Base, Guardrail
- **Documentos:** docs/06-agent-ai/herramientas.md, docs/06-agent-ai/guardrails.md

---

**Última actualización:** 2026-05-07  
**Mantenedor:** Technical Writer  
**Cambios recientes:** Agregados términos de Tier 3, convenciones de nombres
