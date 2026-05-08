# Backend Architecture

Especificación técnica de la arquitectura del backend, patrones, transacciones y garantías de consistencia.

## Vision General

El backend sigue una arquitectura **data-first** donde la base de datos PostgreSQL es la fuente de verdad. Múltiples clientes (UI admin, agente IA, integraciones) acceden exclusivamente a través de APIs REST definidas en `backend/api/openapi.yaml`.

```
┌─────────────────────────────────────────────────────────────┐
│                      Clientes                               │
│  ┌───────────┬──────────────┬──────────────┬────────────┐   │
│  │ Web/Admin │ Agente IA    │ Integraciones│ Reporting  │   │
│  └────┬──────┴──────┬───────┴───────┬──────┴─────┬──────┘   │
└───────┼─────────────┼────────────────┼────────────┼──────────┘
        │ JWT+RBAC    │ Tool-based    │ Async      │ Queries
        │             │ Auth          │ Webhooks   │
┌───────▼─────────────▼────────────────▼────────────▼──────────┐
│                    API Gateway                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Authentication, Authorization, Rate Limiting, Logging│   │
│  └──────────────────────────────────────────────────────┘   │
└───────┬──────────────────────────────────────────────────────┘
        │
┌───────▼────────────────────────────────────────────────────┐
│                 Service Layer (REST)                        │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ Certification│  Validation  │ Notification │            │
│  │   Service   │    Service   │   Service    │            │
│  └──────┬───────┴──────┬───────┴──────┬───────┘            │
│  ┌──────┴───────┬──────────────┬──────┴───────┐            │
│  │   Reporting  │ Data Quality │  Audit Log   │            │
│  │   Service    │    Service   │  Service     │            │
│  └──────┬───────┴──────┬───────┴──────┬───────┘            │
│         │              │              │                     │
│  ┌──────▼──────────────▼──────────────▼──────┐             │
│  │        Business Logic Layer                │             │
│  │  ┌────────────────────────────────────┐  │             │
│  │  │ Rules Engine (Cert validity, etc)  │  │             │
│  │  │ Event Handlers                      │  │             │
│  │  │ Notification Triggers              │  │             │
│  │  └────────────────────────────────────┘  │             │
│  └──────┬───────────────────────────────────┘             │
└────────┼─────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────┐
│               Data Access Layer (Transactions)            │
│  ┌──────────────────────────────────────────────────────┐│
│  │  Unit of Work Pattern + Connection Pooling           ││
│  │  Query Optimization + Statement Caching              ││
│  │  Prepared Statements (SQL Injection Prevention)       ││
│  └──────────────────────────────────────────────────────┘│
└────────┬─────────────────────────┬──────────────────────┘
         │                         │
    ┌────▼──────────────┐  ┌──────▼──────────────┐
    │  PostgreSQL 12+   │  │  Storage (S3/Blob)  │
    │  (Operacional)    │  │  (Evidencias)       │
    │  ┌──────────────┐ │  └─────────────────────┘
    │  │ 17 tablas    │ │
    │  │ indices      │ │  ┌──────────────────────┐
    │  │ constraints  │ │  │  Cache Layer         │
    │  │ views        │ │  │  (Redis, si aplica)  │
    │  └──────────────┘ │  └─────────────────────┘
    │  ┌──────────────┐ │
    │  │   Audit     │ │
    │  │    Table    │ │
    │  └──────────────┘ │
    └──────────────────┘
```

## Capas

### 1. API Gateway / Entry Point

**Responsabilidades:**
- Validación de JWT + extracción de claims (roles, permisos, user_id)
- RBAC (Role-Based Access Control) - validación de permisos
- Rate limiting por usuario/IP
- Validación de entrada (schema, tipos)
- Correlación de requests (correlation_id)
- Logging estructurado

**Patrones:**
- JWT con claims: `{user_id, roles: [], permissions: [], iat, exp}`
- Headers requeridos: `Authorization: Bearer {token}`, `X-Correlation-ID: uuid`
- Respuestas estándar:
  ```json
  {
    "success": true,
    "data": {...},
    "meta": {
      "correlation_id": "uuid",
      "timestamp": "2026-05-07T10:30:00Z"
    }
  }
  ```

### 2. Service Layer

Cada servicio es responsable de un dominio de negocio:

#### **Certification Service**
- Buscar, crear, actualizar certificaciones en catálogo
- Crear/actualizar asignaciones
- Registrar evidencias obtenidas
- Gestionar waivers

#### **Validation Service**
- Procesar decisiones de validación (aprobado/rechazado)
- Emitir eventos de validación
- Asegurar que solo validadores autorizados puedan validar

#### **Notification Service**
- Procesar notificaciones (eventos)
- Enviar por email, Teams, SMS
- Rastrear delivery status
- Manejo de reintentos

#### **Reporting Service**
- Queries agregadas (read-only en vista de reporting)
- Suministrar datos a BI
- Caché de reportes frecuentes

#### **Data Quality Service**
- Ejecutar reglas de calidad
- Detectar anomalías
- Registrar incidencias

#### **Audit Service**
- Registrar todas las acciones en audit_log
- Proporcionar trazabilidad
- No permite mutaciones (append-only)

### 3. Business Logic Layer

**Reglas de Negocio:**
- Cálculo de vigencia: `expiration_date = issue_date + (validity_months months)`
- Estado de certificación:
  - `active`: issue_date ≤ today ≤ expiration_date
  - `expired`: today > expiration_date
  - `pending_validation`: pendiente validación por validador
  - `rejected`: rechazada
  - `waivered`: exenta con waiver válido
- Asignaciones:
  - Un colaborador puede tener múltiples certificaciones asignadas
  - Una asignación es "completada" cuando hay un registro con validation_status = 'approved'

**Event Handlers:**
```
Eventos:
├── CertificationCreated → Notificar a managers
├── CertificationAssigned → Notificar a colaborador
├── EvidenceUploaded → Notificar a validador
├── ValidationApproved → Notificar a colaborador + auditar
├── ValidationRejected → Notificar a colaborador + reabrir asignación
├── CertificationExpiring (< 30 días) → Alertar a colaborador + manager
└── CertificationExpired → Marcar asignación como fallida
```

### 4. Data Access Layer

**Transacciones y Consistencia:**

#### **Garantías ACID**
- **A**tomicity: Cada operación es todo-o-nada
- **C**onsistency: Constraints y triggers aseguran integridad
- **I**solation: READ_COMMITTED es suficiente para este caso (conflictos bajos)
- **D**urability: PostgreSQL garantiza durabilidad

#### **Patrones de Transacción**

1. **Lectura Segura (READ):**
   ```sql
   BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED;
   -- Lectura de datos (siempre es segura)
   SELECT * FROM certification_record WHERE ...;
   COMMIT;
   ```
   Usado para: Consultas, reportes, búsquedas

2. **Escritura Idempotente (CREATE/UPDATE):**
   ```sql
   BEGIN TRANSACTION;
   -- Validar precondiciones (permisos, estado anterior)
   SELECT status FROM certification_record WHERE record_id = ?;
   -- Si validación OK:
   UPDATE certification_record SET status = 'approved' WHERE record_id = ?;
   -- Registrar auditoria
   INSERT INTO audit_log VALUES (...);
   COMMIT;
   ```
   Idempotencia: Si falla y se reintenta, el segundo intento debe ser seguro
   - Usar `ON CONFLICT` para upserts
   - Usar UUIDs generados en cliente (no auto-increment)
   - Validar estado anterior antes de cambiar

3. **Transacción Multi-entidad (Renovación):**
   ```sql
   BEGIN TRANSACTION;
   -- 1. Validar asignación actual
   SELECT status FROM certification_assignment WHERE ...;
   -- 2. Crear nuevo record
   INSERT INTO certification_record (...) RETURNING record_id;
   -- 3. Actualizar asignación
   UPDATE certification_assignment SET status = 'completed' WHERE ...;
   -- 4. Auditar TODO
   INSERT INTO audit_log (...);
   INSERT INTO audit_log (...);
   INSERT INTO audit_log (...);
   COMMIT;
   ```

#### **Bloqueos y Deadlocks**
- Minimizar tiempo de lock
- Siempre hacer lock en mismo orden (por id, ascendente)
- Timeout de transacción: 30s máximo
- Si hay deadlock: reintento con backoff exponencial

#### **Indices Obligatorios**
```sql
-- PK (ya existen)
-- Búsquedas frecuentes
CREATE INDEX idx_collaborator_email ON collaborator(email);
CREATE INDEX idx_collaborator_employee_number ON collaborator(employee_number);
CREATE INDEX idx_certification_record_collaborator_status ON certification_record(collaborator_id, status);
CREATE INDEX idx_certification_record_expiration ON certification_record(expiration_date);
CREATE INDEX idx_certification_assignment_assignee_due ON certification_assignment(assignee_id, due_date, status);
CREATE INDEX idx_audit_log_actor_date ON audit_log(actor_id, occurred_at);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_ai_conversation_user_date ON ai_conversation(user_id, started_at);
```

#### **Evitar N+1 Queries**
- Usar JOINs cuando sea posible
- Cargar relaciones en un solo query
- Caché de lectura para datos estáticos (vendor, certification)

## Patrones Transversales

### 1. Auditoria (Audit-First)

**Principio:** Toda acción que mutea datos debe ser auditada en el mismo commit.

**Estructura de audit_log:**
```sql
INSERT INTO audit_log (
  correlation_id,     -- UUID del request
  actor_id,           -- Usuario que hizo el cambio
  actor_type,         -- 'user', 'system', 'ai-agent'
  action,             -- 'create', 'update', 'delete', 'validate'
  entity_type,        -- 'certification_record', 'assignment', etc.
  entity_id,          -- UUID de qué cambió
  before_data,        -- JSONB del estado anterior
  after_data,         -- JSONB del estado nuevo
  occurred_at         -- Timestamp
) VALUES (...);
```

**Campos auditados obligatoriamente:**
- certification_record (create, update, delete)
- certification_assignment (create, update)
- validation_event (create)
- exception_waiver (create, update)
- certification (create, update) - cambios en catálogo

**Consultas de auditoria:**
```sql
-- Quién cambió qué cuándo
SELECT actor_id, action, entity_type, entity_id, occurred_at 
FROM audit_log 
WHERE correlation_id = ?
ORDER BY occurred_at;

-- Histórico de un registro
SELECT before_data, after_data, actor_id, occurred_at
FROM audit_log
WHERE entity_type = 'certification_record' AND entity_id = ?
ORDER BY occurred_at;
```

### 2. Validación (Backend-First)

Todas las validaciones deben ocurrir en la API/DB, NUNCA en cliente.

**Niveles:**
1. **Schema** (OpenAPI):
   ```yaml
   - type: string
     format: uuid
     minLength: 36
   - type: email
   ```

2. **Dominio** (SQL constraints):
   ```sql
   -- No permitir expiration_date < issue_date
   CONSTRAINT chk_record_dates CHECK (expiration_date >= issue_date)
   
   -- No permitir waivers superpuestos
   -- (validar en aplicación por complejidad)
   ```

3. **Negocio** (Stored Procedures / Application):
   ```
   - ¿El usuario tiene permiso?
   - ¿El registro está en estado válido?
   - ¿Ya hay validación? (no permitir revalidar)
   - ¿La evidencia cumple requisitos?
   ```

### 3. Seguridad en URLs de Evidencias

Las evidencias se almacenan en storage externo (S3, Azure Blob).

**Flujo:**
1. Cliente sube a presigned URL (generada por API)
   ```
   POST /api/v1/evidences/presigned-url
   Response: {url: "https://bucket.s3.amazonaws.com/path?signed_params"}
   Client: PUT {file} → URL (por 15 minutos)
   ```

2. Cliente notifica API que subió
   ```
   POST /api/v1/records/{recordId}/evidence-uploaded
   Body: {storage_uri: "s3://bucket/path", file_hash: "sha256"}
   ```

3. API verifica hash y archiva URI en base de datos
   ```sql
   INSERT INTO evidence_document (record_id, storage_uri, ...)
   ```

4. Acceso posterior solo con permisos
   ```
   GET /api/v1/evidences/{evidenceId}
   [Valida permisos] → Genera presigned URL temporal (5 min)
   ```

### 4. Idempotencia

**Definición:** Hacer una acción 2+ veces tiene el mismo efecto que 1 vez.

**Cómo lograrlo:**

1. **Generar UUID en cliente:**
   ```json
   POST /api/v1/records
   {
     "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
     "collaborator_id": "...",
     "certification_id": "..."
   }
   ```
   DB: `CREATE UNIQUE INDEX idx_idempotency_key ON records(idempotency_key)`

2. **Detectar duplicados:**
   ```sql
   -- Si ya existe con misma key
   SELECT record_id FROM certification_record 
   WHERE idempotency_key = ? AND status = 'approved';
   -- Retornar registro existente (no error)
   ```

3. **Métodos idempotentes:**
   - GET, HEAD, OPTIONS: siempre idempotentes
   - POST con idempotency_key: idempotente
   - PUT {id}: idempotente (reemplaza)
   - PATCH: NO idempotente (depende de orden)
   - DELETE: idempotente (2da vez = 404 o 200 vacío)

### 5. Resiliencia y Reintentos

**Errores Transitorios (reintento automático):**
- 408 Request Timeout → reintento 3x con backoff
- 429 Too Many Requests → reintento con jitter
- 503 Service Unavailable → reintento 3x

**Errores Permanentes (sin reintento):**
- 400 Bad Request → corregir entrada
- 401 Unauthorized → reauthenticar
- 403 Forbidden → checkear permisos
- 404 Not Found → recurso no existe
- 422 Unprocessable Entity → validación falló

**Backoff Exponencial:**
```
Intento 1: inmediato
Intento 2: 100ms + jitter (0-100ms)
Intento 3: 1s + jitter (0-1s)
Intento 4: 10s + jitter (0-10s)
→ Fallo después de 4 intentos
```

## Vistas Especializadas (Read-Only)

```sql
-- Reporting: Cobertura por unidad
CREATE VIEW v_coverage_by_unit AS
SELECT bu.name, COUNT(*) total, ...
FROM business_unit bu
LEFT JOIN collaborator c ON c.business_unit_id = bu.business_unit_id
...;

-- Operational: Certificaciones próximas a vencer
CREATE VIEW v_expiring_soon AS
SELECT cr.*, c.display_name, c.email, ...
FROM certification_record cr
WHERE cr.status = 'active'
  AND cr.expiration_date BETWEEN now() AND now() + interval '30 days'
...;

-- Audit: Cambios recientes
CREATE VIEW v_recent_changes AS
SELECT entity_type, entity_id, actor_id, action, occurred_at
FROM audit_log
WHERE occurred_at > now() - interval '7 days'
ORDER BY occurred_at DESC;
```

## Jobs y Procesos Batch

Ejecutados regularmente por scheduler (ej: Airflow, cron, cloud functions):

| Job | Frecuencia | Responsabilidad |
|-----|-----------|-----------------|
| `sync_collaborators` | Diaria (madrugada) | Sincronizar desde HR |
| `detect_expirations` | Diaria | Marcar certificaciones como expiradas |
| `send_expiring_alerts` | Diaria | Notificar a 30 días de expiración |
| `process_pending_validations` | Cada 4h | Procesar validaciones pendientes |
| `data_quality_check` | Diaria | Ejecutar reglas de calidad |
| `archive_old_conversations` | Semanal | Archivar conversaciones IA antiguas |
| `generate_compliance_report` | Semanal | Generar reportes para auditoría |
| `cleanup_temporary_data` | Mensual | Limpiar datos temporales, sessions expiradas |

## Resiliencia Operacional

### Recuperación ante Fallos

1. **Fallo de DB (downtime < 5 min):**
   - API retorna 503 Service Unavailable
   - Clientes reintentan automáticamente
   - Datos en flight se pierden (aceptable < 5 min)

2. **Fallo de Notification Service:**
   - Envío encolado en queue (con reintentos)
   - No bloquea transacción principal
   - Dashboard de notificaciones fallidas

3. **Fallo de Integracion HR:**
   - Reintento exponencial
   - Alert a operaciones si fallos > 3
   - Usar datos en cache hasta siguiente sync exitosa

### Monitoreo

**Métricas clave:**
- Latencia API (p50, p95, p99)
- Tasa de error por endpoint (4xx, 5xx)
- Tasa de jobs fallidos
- Tamaño de queues de notificación
- Edad de transacciones activas
- Cobertura de certificaciones (%)

**Alertas:**
- Latencia p95 > 2s
- Error rate > 1%
- Job fallido (reintento)
- Queue > 10k elementos
- DB connection pool exhausted

## Checkpoints de Implementación

- [ ] Crear schema.sql con todas las tablas
- [ ] Crear índices recomendados
- [ ] Crear vistas de reporting
- [ ] Implementar API gateway (auth, RBAC, logging)
- [ ] Implementar services (métodos CRUD)
- [ ] Agregar auditoria a todos los cambios
- [ ] Implementar validaciones de dominio
- [ ] Tests unitarios (servicios aislados)
- [ ] Tests de integración (API + DB)
- [ ] Tests de transacciones (deadlocks, race conditions)
- [ ] Configurar jobs batch
- [ ] Configurar monitoreo y alertas

## Referencias

- `backend/database/schema.sql` - Definición de tablas
- `backend/database/indexes.sql` - Índices adicionales
- `backend/database/views_reporting.sql` - Vistas
- `backend/api/openapi.yaml` - Especificación API
- `docs/02-datos/modelo-logico.md` - Modelo de datos
- `docs/05-seguridad-cumplimiento/seguridad.md` - Controles de seguridad
