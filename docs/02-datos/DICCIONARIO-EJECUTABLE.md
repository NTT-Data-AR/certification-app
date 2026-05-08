# Diccionario de Datos Ejecutable

Documentación completa y ejecutable de todas las entidades, campos, tipos, validaciones y ejemplos de la base de datos.

**Nota:** Este documento es la fuente de verdad para estructura de datos. Sincronizado con:
- `backend/database/schema.sql` (definiciones DDL)
- `models/schemas/*.schema.json` (validaciones)
- `backend/API.md` (respuestas REST)

---

## 1. Tipos de Datos Base

Todos los tipos de datos utilizados en el proyecto:

| Tipo | Descripción | Ejemplo | Validación |
|------|-----------|---------|-----------|
| **uuid** | Identificador único | `550e8400-e29b-41d4-a716-446655440000` | RFC 4122, 36 caracteres |
| **text** | Cadena de texto variable | `"AWS Solutions Architect"` | Sin longitud máxima (usar VARCHAR en BD) |
| **varchar(n)** | Texto con límite | `"ACTIVE"` (50 max) | 0 a n caracteres |
| **email** | Correo válido | `john.doe@example.com` | RFC 5322 (formato simple) |
| **date** | Fecha sin hora | `2026-05-07` | YYYY-MM-DD |
| **timestamptz** | Fecha y hora con zona | `2026-05-07T10:30:00Z` | ISO 8601 |
| **integer** | Número entero | `36` | -2B a 2B |
| **boolean** | Verdadero/Falso | `true` | true / false |
| **jsonb** | JSON binario | `{"key": "value"}` | JSON válido |

---

## 2. Enumerados (Enums)

### 2.1 record_status

Estado de un registro de certificación.

```yaml
ACTIVE:             # Certificación vigente (issue_date <= today <= expiration_date)
EXPIRED:            # Pasó fecha de vencimiento
PENDING_VALIDATION: # En validación por validador
REJECTED:           # Rechazada
WAIVERED:           # Exenta por waiver
```

### 2.2 validation_status

Estado de la validación de un record.

```yaml
PENDING:    # Aguardando validación
APPROVED:   # Validada exitosamente
REJECTED:   # Rechazada por validador
WAIVERED:   # Exenta sin validación
```

### 2.3 assignment_status

Estado de una asignación de certificación.

```yaml
PENDING:    # Creada, esperando que colaborador obtenga
COMPLETED:  # Certificación obtenida y validada
REJECTED:   # Evidencia rechazada
EXPIRED:    # Pasó due_date sin completar
WAIVERED:   # Exenta
```

### 2.4 employment_status

Estado laboral de un colaborador.

```yaml
ACTIVE:   # Activamente empleado
INACTIVE: # No activo (pre-hire, post-hire)
LEAVE:    # En licencia (vacation, parental, sick)
```

### 2.5 priority

Nivel de prioridad.

```yaml
LOW:    # Sin urgencia
MEDIUM: # Normal
HIGH:   # Importante
CRITICAL: # Urgente, requiere atención inmediata
```

### 2.6 classification

Clasificación de documento de evidencia.

```yaml
PROOF_OF_COMPLETION:  # Diploma, certificado
PASS_CONFIRMATION:    # Email de cumplimiento
CREDENTIAL_ID:        # Número de credencial validado
REGISTRY_VERIFICATION: # Verificación de registry oficial
OTHER:                 # Otro
```

### 2.7 notification_type

Tipo de notificación.

```yaml
ASSIGNMENT_CREATED:      # Nueva asignación
EVIDENCE_UPLOADED:       # Evidencia subida
VALIDATION_APPROVED:     # Aprobación
VALIDATION_REJECTED:     # Rechazo
EXPIRATION_WARNING_30D:  # Vence en 30 días
EXPIRATION_WARNING_7D:   # Vence en 7 días
EXPIRED:                 # Ya venció
RENEWAL_ELIGIBLE:        # Puede renovarse (< 90 días)
RENEWAL_REQUESTED:       # Renovación iniciada
```

### 2.8 notification_channel

Medio de envío.

```yaml
EMAIL:  # Correo electrónico
TEAMS:  # Microsoft Teams
SMS:    # Mensaje de texto
IN_APP: # Notificación en aplicación
```

### 2.9 notification_status

Estado de envío.

```yaml
PENDING:    # No enviada aún
SENT:       # Enviada exitosamente
FAILED:     # Fallo en envío
DELIVERED:  # Confirmada entrega
READ:       # Leída por usuario
```

---

## 3. Entidades (Tablas)

### 3.1 business_unit

**Descripción:** Unidad organizativa (departamento, área, filial).

**Primaria:** `business_unit_id`  
**Única:** `name` (por empresa/contexto)  
**Auditoría:** No (datos maestros raramente cambian)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `business_unit_id` | uuid | No | gen_random_uuid() | Identificador único |
| `name` | text | No | - | Nombre de la unidad (ej: "Cloud Services") |
| `parent_business_unit_id` | uuid | Sí | - | Referencia a unidad padre (jerarquía) |
| `country_code` | char(2) | Sí | - | Código ISO país (ej: "ES", "AR", "CO") |
| `is_active` | boolean | No | true | Unidad activa |
| `created_at` | timestamptz | No | now() | Timestamp de creación |
| `updated_at` | timestamptz | No | now() | Timestamp de última modificación |

**Índices:**
```sql
CREATE INDEX idx_bu_name ON business_unit(name);
CREATE INDEX idx_bu_parent ON business_unit(parent_business_unit_id);
```

**Ejemplo:**
```json
{
  "business_unit_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Cloud Services",
  "parent_business_unit_id": "550e8400-e29b-41d4-a716-446655440001",
  "country_code": "ES",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z"
}
```

---

### 3.2 collaborator

**Descripción:** Colaborador (empleado). Datos mínimos, sincronizados desde HR.

**Primaria:** `collaborator_id`  
**Únicas:** `employee_number`, `email`  
**Auditoría:** Sí (cambios en estado, unidad, manager)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `collaborator_id` | uuid | No | gen_random_uuid() | Identificador único |
| `employee_number` | text | No | - | Número de empleado (ej: "E-12345") |
| `email` | email | No | - | Email corporativo (ej: "john@nttdata.com") |
| `display_name` | text | No | - | Nombre mostrable (ej: "John Doe") |
| `business_unit_id` | uuid | Sí | - | FK a business_unit |
| `manager_id` | uuid | Sí | - | FK a collaborator (su manager) |
| `employment_status` | varchar(20) | No | - | ACTIVE, INACTIVE, LEAVE |
| `source_system` | text | No | - | Sistema de origen (ej: "SAP_HR", "AD", "IMPORT") |
| `created_at` | timestamptz | No | now() | - |
| `updated_at` | timestamptz | No | now() | - |

**Restricciones:**
```sql
-- manager_id puede ser nulo (director ejecutivo)
-- manager_id != collaborator_id (no ser manager de sí mismo)
CONSTRAINT chk_manager_not_self 
  CHECK (manager_id IS NULL OR manager_id != collaborator_id)
```

**Índices:**
```sql
CREATE UNIQUE INDEX idx_collaborator_employee_number ON collaborator(employee_number);
CREATE UNIQUE INDEX idx_collaborator_email ON collaborator(email);
CREATE INDEX idx_collaborator_business_unit ON collaborator(business_unit_id);
CREATE INDEX idx_collaborator_manager ON collaborator(manager_id);
```

**Ejemplo:**
```json
{
  "collaborator_id": "550e8400-e29b-41d4-a716-446655440200",
  "employee_number": "E-12345",
  "email": "john.doe@nttdata.com",
  "display_name": "John Doe",
  "business_unit_id": "550e8400-e29b-41d4-a716-446655440000",
  "manager_id": "550e8400-e29b-41d4-a716-446655440050",
  "employment_status": "ACTIVE",
  "source_system": "SAP_HR"
}
```

---

### 3.3 vendor

**Descripción:** Proveedor de certificaciones.

**Primaria:** `vendor_id`  
**Única:** `name`  
**Auditoría:** No

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `vendor_id` | uuid | No | gen_random_uuid() | - |
| `name` | text | No | - | Nombre (ej: "Amazon", "Microsoft", "Google") |
| `website_url` | text | Sí | - | URL oficial del proveedor |
| `is_active` | boolean | No | true | - |
| `created_at` | timestamptz | No | now() | - |

**Ejemplo:**
```json
{
  "vendor_id": "550e8400-e29b-41d4-a716-446655440010",
  "name": "Amazon Web Services",
  "website_url": "https://aws.amazon.com/certification/",
  "is_active": true
}
```

---

### 3.4 certification

**Descripción:** Catálogo de certificaciones disponibles.

**Primaria:** `certification_id`  
**Única:** `(vendor_id, name)` - No pueden haber 2 certs con mismo nombre del mismo vendor  
**Auditoría:** Sí (cambios en validez, requisitos)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `certification_id` | uuid | No | gen_random_uuid() | - |
| `vendor_id` | uuid | No | - | FK a vendor |
| `code` | text | Sí | - | Código (ej: "SAA-C03", "AZ-900") |
| `name` | text | No | - | Nombre (ej: "AWS Solutions Architect Associate") |
| `category` | text | No | - | Categoría (ej: "Cloud", "Database", "Security") |
| `level` | text | Sí | - | Nivel (ej: "Associate", "Professional", "Expert") |
| `validity_months` | integer | Sí | - | Meses válida (ej: 36, null = perpetua) |
| `requires_evidence` | boolean | No | true | Requiere documento para validar |
| `is_active` | boolean | No | true | - |
| `created_at` | timestamptz | No | now() | - |

**Restricciones:**
```sql
CONSTRAINT chk_validity_positive 
  CHECK (validity_months IS NULL OR validity_months > 0)
```

**Índices:**
```sql
CREATE INDEX idx_cert_vendor ON certification(vendor_id);
CREATE INDEX idx_cert_category ON certification(category);
CREATE UNIQUE INDEX idx_cert_unique 
  ON certification(vendor_id, name);
```

**Ejemplo:**
```json
{
  "certification_id": "550e8400-e29b-41d4-a716-446655440100",
  "vendor_id": "550e8400-e29b-41d4-a716-446655440010",
  "code": "SAA-C03",
  "name": "AWS Solutions Architect Associate",
  "category": "Cloud",
  "level": "Associate",
  "validity_months": 36,
  "requires_evidence": true,
  "is_active": true
}
```

---

### 3.5 professional_role

**Descripción:** Rol profesional (puesto de trabajo).

**Primaria:** `professional_role_id`  
**Única:** `name`  
**Auditoría:** No

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `professional_role_id` | uuid | No | gen_random_uuid() | - |
| `name` | text | No | - | (ej: "Cloud Architect", "Database DBA") |
| `is_active` | boolean | No | true | - |

**Ejemplo:**
```json
{
  "professional_role_id": "550e8400-e29b-41d4-a716-446655440700",
  "name": "Cloud Architect",
  "is_active": true
}
```

---

### 3.6 role_certification_requirement

**Descripción:** Asignación de qué certificaciones son requeridas para cada rol.

**Primaria:** `requirement_id`  
**Única:** `(professional_role_id, certification_id)`  
**Auditoría:** Sí

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `requirement_id` | uuid | No | gen_random_uuid() | - |
| `professional_role_id` | uuid | No | - | FK a professional_role |
| `certification_id` | uuid | No | - | FK a certification |
| `requirement_type` | text | No | - | MANDATORY, RECOMMENDED, OPTIONAL |
| `priority` | text | No | - | LOW, MEDIUM, HIGH, CRITICAL |
| `is_active` | boolean | No | true | - |

**Ejemplo:**
```json
{
  "requirement_id": "550e8400-e29b-41d4-a716-446655440800",
  "professional_role_id": "550e8400-e29b-41d4-a716-446655440700",
  "certification_id": "550e8400-e29b-41d4-a716-446655440100",
  "requirement_type": "MANDATORY",
  "priority": "HIGH"
}
```

---

### 3.7 certification_assignment

**Descripción:** Asignación de certificación a un colaborador.

**Primaria:** `assignment_id`  
**Única:** `(assignee_id, certification_id, status != 'COMPLETED')`  
**Auditoría:** Sí (creación, cambios de estado)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `assignment_id` | uuid | No | gen_random_uuid() | - |
| `assignee_id` | uuid | No | - | FK a collaborator |
| `certification_id` | uuid | No | - | FK a certification |
| `assigned_by` | uuid | Sí | - | FK a collaborator (quien asignó) |
| `due_date` | date | Sí | - | Fecha límite para obtener |
| `priority` | text | No | - | LOW, MEDIUM, HIGH, CRITICAL |
| `status` | text | No | - | PENDING, COMPLETED, REJECTED, EXPIRED, WAIVERED |
| `source` | text | No | - | ROLE_REQUIREMENT, MANUAL, IMPORT |
| `reason` | text | Sí | - | Por qué se asignó |
| `created_at` | timestamptz | No | now() | - |
| `updated_at` | timestamptz | No | now() | - |

**Restricciones:**
```sql
CONSTRAINT chk_due_date_future 
  CHECK (due_date IS NULL OR due_date > created_at::date)
CONSTRAINT chk_not_self_assign 
  CHECK (assigned_by IS NULL OR assigned_by != assignee_id)
```

**Índices:**
```sql
CREATE INDEX idx_assign_assignee ON certification_assignment(assignee_id);
CREATE INDEX idx_assign_cert ON certification_assignment(certification_id);
CREATE INDEX idx_assign_due_date ON certification_assignment(due_date, status);
```

**Ejemplo:**
```json
{
  "assignment_id": "550e8400-e29b-41d4-a716-446655440300",
  "assignee_id": "550e8400-e29b-41d4-a716-446655440200",
  "certification_id": "550e8400-e29b-41d4-a716-446655440100",
  "assigned_by": "550e8400-e29b-41d4-a716-446655440050",
  "due_date": "2026-12-31",
  "priority": "HIGH",
  "status": "PENDING",
  "source": "ROLE_REQUIREMENT",
  "reason": "Requerimiento para Cloud Architect"
}
```

---

### 3.8 certification_record

**Descripción:** Registro de certificación obtenida por colaborador.

**Primaria:** `record_id`  
**Única:** `(collaborator_id, certification_id, issue_date)` - No duplicar misma cert mismo colaborador mismo día  
**Auditoría:** Sí (cambios de estado, validación)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `record_id` | uuid | No | gen_random_uuid() | - |
| `collaborator_id` | uuid | No | - | FK a collaborator (propietario) |
| `certification_id` | uuid | No | - | FK a certification |
| `assignment_id` | uuid | Sí | - | FK a assignment (si fue asignada) |
| `credential_id` | text | Sí | - | ID de credencial (ej: "SAA-C03-123456") |
| `issue_date` | date | No | - | Fecha de emisión |
| `expiration_date` | date | Sí | - | Fecha de expiración (null = perpetua) |
| `status` | text | No | - | ACTIVE, EXPIRED, PENDING_VALIDATION, REJECTED, WAIVERED |
| `validation_status` | text | No | - | PENDING, APPROVED, REJECTED, WAIVERED |
| `evidence_required` | boolean | No | true | Requiere evidencia para validar |
| `source_system` | text | No | - | HR_IMPORT, MANUAL, RENEWAL, LEGACY_MIGRATION |
| `migration_batch_id` | uuid | Sí | - | FK a migration_batch (si es de migracion) |
| `created_at` | timestamptz | No | now() | - |
| `updated_at` | timestamptz | No | now() | - |

**Restricciones:**
```sql
CONSTRAINT chk_record_dates 
  CHECK (expiration_date IS NULL OR expiration_date >= issue_date)
CONSTRAINT chk_status_consistency 
  CHECK (
    (status = 'PENDING_VALIDATION' AND validation_status = 'PENDING') OR
    (status = 'ACTIVE' AND validation_status = 'APPROVED') OR
    (status = 'EXPIRED' AND validation_status IN ('APPROVED', 'REJECTED')) OR
    (status = 'REJECTED' AND validation_status = 'REJECTED') OR
    (status = 'WAIVERED' AND validation_status = 'WAIVERED')
  )
```

**Índices:**
```sql
CREATE INDEX idx_record_collaborator_status 
  ON certification_record(collaborator_id, status);
CREATE INDEX idx_record_expiration 
  ON certification_record(expiration_date);
CREATE INDEX idx_record_validation 
  ON certification_record(validation_status);
```

**Ejemplo:**
```json
{
  "record_id": "550e8400-e29b-41d4-a716-446655440400",
  "collaborator_id": "550e8400-e29b-41d4-a716-446655440200",
  "certification_id": "550e8400-e29b-41d4-a716-446655440100",
  "assignment_id": "550e8400-e29b-41d4-a716-446655440300",
  "credential_id": "SAA-C03-2023-789456",
  "issue_date": "2023-05-15",
  "expiration_date": "2026-05-15",
  "status": "ACTIVE",
  "validation_status": "APPROVED",
  "evidence_required": true,
  "source_system": "MANUAL"
}
```

---

### 3.9 evidence_document

**Descripción:** Documentos de evidencia (PDF, imagen, etc).

**Primaria:** `evidence_id`  
**Única:** ninguna (múltiples evidencias por record)  
**Auditoría:** Sí (qué evidencia, quién subió, cuándo)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `evidence_id` | uuid | No | gen_random_uuid() | - |
| `record_id` | uuid | No | - | FK a certification_record |
| `storage_uri` | text | No | - | URI en storage (ej: "s3://bucket/path/file.pdf") |
| `classification` | text | No | - | PROOF_OF_COMPLETION, CREDENTIAL_ID, REGISTRY_VERIFICATION, OTHER |
| `uploaded_by` | uuid | Sí | - | FK a collaborator (quién subió) |
| `uploaded_at` | timestamptz | No | now() | - |

**Índices:**
```sql
CREATE INDEX idx_evidence_record ON evidence_document(record_id);
```

**Ejemplo:**
```json
{
  "evidence_id": "550e8400-e29b-41d4-a716-446655440500",
  "record_id": "550e8400-e29b-41d4-a716-446655440400",
  "storage_uri": "s3://cert-app-bucket/evidences/2026/05/file.pdf",
  "classification": "PROOF_OF_COMPLETION",
  "uploaded_by": "550e8400-e29b-41d4-a716-446655440200",
  "uploaded_at": "2026-05-07T10:30:00Z"
}
```

---

### 3.10 validation_event

**Descripción:** Decisiones de validación de certificaciones.

**Primaria:** `validation_event_id`  
**Auditoría:** Sí (quién validó, qué decidió)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `validation_event_id` | uuid | No | gen_random_uuid() | - |
| `record_id` | uuid | No | - | FK a certification_record |
| `validator_id` | uuid | No | - | FK a collaborator (validador) |
| `decision` | text | No | - | APPROVED, REJECTED |
| `reason` | text | Sí | - | Justificación (requerida si REJECTED) |
| `decided_at` | timestamptz | No | now() | - |

**Restricciones:**
```sql
CONSTRAINT chk_rejection_reason 
  CHECK (decision = 'APPROVED' OR reason IS NOT NULL)
```

**Índices:**
```sql
CREATE INDEX idx_validation_record ON validation_event(record_id);
CREATE INDEX idx_validation_validator ON validation_event(validator_id);
```

**Ejemplo:**
```json
{
  "validation_event_id": "550e8400-e29b-41d4-a716-446655440600",
  "record_id": "550e8400-e29b-41d4-a716-446655440400",
  "validator_id": "550e8400-e29b-41d4-a716-446655440050",
  "decision": "APPROVED",
  "reason": "Certificado verificado en AWS portal",
  "decided_at": "2026-05-07T11:00:00Z"
}
```

---

### 3.11 exception_waiver

**Descripción:** Excepciones/waivers (exenciones de certificación).

**Primaria:** `waiver_id`  
**Auditoría:** Sí (creación, cambios de estado)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `waiver_id` | uuid | No | gen_random_uuid() | - |
| `collaborator_id` | uuid | No | - | FK a collaborator |
| `certification_id` | uuid | No | - | FK a certification |
| `approved_by` | uuid | No | - | FK a collaborator (quien aprobó) |
| `reason` | text | No | - | Por qué se otorga waiver |
| `valid_from` | date | No | - | Fecha de inicio de vigencia |
| `valid_to` | date | No | - | Fecha de fin de vigencia |
| `status` | text | No | - | ACTIVE, EXPIRED, REVOKED |

**Restricciones:**
```sql
CONSTRAINT chk_waiver_dates 
  CHECK (valid_to >= valid_from)
```

**Índices:**
```sql
CREATE INDEX idx_waiver_collaborator_cert 
  ON exception_waiver(collaborator_id, certification_id);
CREATE INDEX idx_waiver_validity 
  ON exception_waiver(valid_from, valid_to);
```

**Ejemplo:**
```json
{
  "waiver_id": "550e8400-e29b-41d4-a716-446655440900",
  "collaborator_id": "550e8400-e29b-41d4-a716-446655440200",
  "certification_id": "550e8400-e29b-41d4-a716-446655440100",
  "approved_by": "550e8400-e29b-41d4-a716-446655440050",
  "reason": "Experiencia equivalente reconocida",
  "valid_from": "2026-05-07",
  "valid_to": "2027-05-07",
  "status": "ACTIVE"
}
```

---

### 3.12 notification

**Descripción:** Log de notificaciones enviadas.

**Primaria:** `notification_id`  
**Auditoría:** No (tabla es log)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `notification_id` | uuid | No | gen_random_uuid() | - |
| `recipient_id` | uuid | No | - | FK a collaborator |
| `notification_type` | text | No | - | ASSIGNMENT_CREATED, EVIDENCE_UPLOADED, etc. |
| `related_entity_type` | text | Sí | - | certification_record, assignment, etc. |
| `related_entity_id` | uuid | Sí | - | ID de entidad relacionada |
| `channel` | text | No | - | EMAIL, TEAMS, SMS, IN_APP |
| `status` | text | No | - | PENDING, SENT, FAILED, DELIVERED, READ |
| `created_at` | timestamptz | No | now() | - |

**Índices:**
```sql
CREATE INDEX idx_notif_recipient ON notification(recipient_id, created_at);
CREATE INDEX idx_notif_status ON notification(status, created_at);
```

---

### 3.13 audit_log

**Descripción:** Log de todas las acciones (append-only).

**Primaria:** `audit_id`  
**Auditoría:** No (es la tabla de auditoría)

| Campo | Tipo | Nulo | Defecto | Descripción |
|-------|------|------|---------|-----------|
| `audit_id` | uuid | No | gen_random_uuid() | - |
| `correlation_id` | uuid | No | - | ID del request que generó el evento |
| `actor_id` | text | No | - | Email, system ID, AI agent ID |
| `actor_type` | text | No | - | user, system, ai_agent |
| `action` | text | No | - | CREATE, UPDATE, DELETE, VALIDATE, REJECT |
| `entity_type` | text | No | - | certification_record, assignment, etc. |
| `entity_id` | uuid | No | - | Qué cambió |
| `before_data` | jsonb | Sí | - | Estado anterior (NULL si CREATE) |
| `after_data` | jsonb | Sí | - | Estado nuevo (NULL si DELETE) |
| `occurred_at` | timestamptz | No | now() | - |

**Índices:**
```sql
CREATE INDEX idx_audit_entity 
  ON audit_log(entity_type, entity_id, occurred_at);
CREATE INDEX idx_audit_actor_date 
  ON audit_log(actor_id, occurred_at);
CREATE INDEX idx_audit_correlation 
  ON audit_log(correlation_id);
```

---

## 4. Vistas (Read-Only)

### 4.1 v_active_certifications

Certificaciones activas para colaborador (hoy).

```sql
CREATE VIEW v_active_certifications AS
SELECT 
  cr.record_id,
  cr.collaborator_id,
  c.display_name,
  cert.certification_id,
  cert.name,
  cert.category,
  cr.issue_date,
  cr.expiration_date,
  (cr.expiration_date - CURRENT_DATE) AS days_remaining,
  cr.status,
  cr.validation_status,
  v.name AS vendor_name,
  bu.name AS business_unit
FROM certification_record cr
  JOIN collaborator c ON cr.collaborator_id = c.collaborator_id
  JOIN certification cert ON cr.certification_id = cert.certification_id
  JOIN vendor v ON cert.vendor_id = v.vendor_id
  LEFT JOIN business_unit bu ON c.business_unit_id = bu.business_unit_id
WHERE cr.status = 'ACTIVE'
  AND cr.expiration_date > CURRENT_DATE;
```

### 4.2 v_expiring_soon

Certificaciones venciendo en próximo trimestre.

```sql
CREATE VIEW v_expiring_soon AS
SELECT *
FROM v_active_certifications
WHERE days_remaining > 0 
  AND days_remaining <= 90
ORDER BY days_remaining ASC;
```

---

## 5. Validaciones Aplicadas

### 5.1 Validaciones en BD (Constraints)

- **Fechas:** `expiration_date >= issue_date`
- **Permisos:** Solo propietario puede modificar su record
- **Estados:** Transiciones válidas entre estados (máquina de estados)
- **Unicidad:** No duplicar record mismo collab + cert + día
- **Integridad referencial:** FKs no nulas hacia tablas maestras

### 5.2 Validaciones en API

- **JWT:** Token válido, no expirado
- **RBAC:** Roles y permisos según acción
- **Schema:** Campos requeridos, tipos, formatos (email, uuid, date)
- **Negocio:** Certificación próxima a vencer (< 90d), no revalidar, etc.

### 5.3 Validaciones en Cliente

- Opcional, duplicadas en servidor
- Campos requeridos marked
- Formatos indicados (ej: fecha como YYYY-MM-DD)
- Mensajes útiles

---

## 6. Sincronización y Consistencia

Este diccionario DEBE mantenerse sincronizado con:

| Archivo | Qué verificar |
|---------|--------------|
| `backend/database/schema.sql` | DDL de tablas, tipos, constraints |
| `models/schemas/*.schema.json` | Validaciones OpenAPI |
| `backend/API.md` | Request/response bodies |
| `docs/02-datos/diccionario-datos.md` | Definiciones de campos |
| `docs/02-datos/entidades.md` | Listado de entidades |
| `tests/` | Casos de prueba reflejan restricciones |

---

## 7. Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-05-07 | Versión inicial, documentadas 13 entidades |

---

## 8. Próximos Pasos de Implementación

- [ ] Crear todas las tablas en PostgreSQL
- [ ] Crear índices listados
- [ ] Crear vistas de reporting
- [ ] Agregar triggers para auditoria automática
- [ ] Tests: inserción, validación, constraints
- [ ] Tests: integridad referencial
- [ ] Documentación de migraciones
- [ ] Performance testing de índices
