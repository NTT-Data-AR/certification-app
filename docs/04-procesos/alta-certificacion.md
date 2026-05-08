# Alta de Certificación Obtenida (RF-006)

Registrar una certificación que un colaborador ha obtenido, incluyendo evidencia de su logro.

**Ruta crítica:** `Colaborador → Registra Cert → Validador aprueba → Cert Activa`

---

## 1. Fases del Proceso

### Fase 1: Iniciación (Colaborador Inicia)

**Disparador:** Colaborador hace clic en "Registrar certificación obtenida"

**Actor:** Colaborador (RF-006)

**Datos capturados:**
| Campo | Tipo | Requerido | Rango | Ejemplo |
|-------|------|-----------|-------|---------|
| collaborator_id | UUID | Sí | System-assigned | a1b2c3d4-... |
| certification_id | UUID | Sí | Válido en catálogo | AWS Solutions Architect Associate |
| issue_date | Date | Sí | ≤ hoy | 2024-05-15 |
| expiration_date | Date | Sí | ≥ issue_date | 2027-05-15 |
| credential_id | String | Opcional | Max 100 chars | AWS-123456-XYZ |
| issuer_name | String | Opcional | Max 200 chars | Amazon Web Services |
| registry_url | URL | Opcional | Valid URL | https://aws.example.com/verify/... |

**Validaciones Fase 1:**
- [ ] Colaborador autenticado (JWT válido, no expired)
- [ ] collaborator_id existe en BD
- [ ] certification_id existe en catálogo (certification table)
- [ ] issue_date ≤ hoy (no futuro)
- [ ] expiration_date ≥ issue_date
- [ ] No existe otro record PENDIENTE para esta cert en este colaborador
- [ ] credential_id no duplicado en BD (si aplica)
- [ ] Formato de campos: dates YYYY-MM-DD, URLs valid

**Estado tras Fase 1:** `certification_record.status = 'pending_validation'`

---

### Fase 2: Carga de Evidencia

**Disparador:** Colaborador completó datos y avanza a "Subir evidencia"

**Actor:** Colaborador

**Flujo:**
1. Backend retorna **presigned URL** (válida 15 minutos) para subir a S3
2. Colaborador sube archivo (PDF, JPG, PNG, Max 50 MB)
3. Frontend notifica backend con `evidence_document_id` y clasificación

**Datos de evidencia:**
| Campo | Tipo | Requerido | Opciones | Ejemplo |
|-------|------|-----------|----------|---------|
| file_name | String | Sí | | "AWS_SAA_Certificate_2024.pdf" |
| file_type | String | Sí | image/jpeg, application/pdf, image/png | application/pdf |
| file_size | Integer | Sí | ≤ 50MB | 2500000 |
| classification | Enum | Sí | proof_of_completion, credential_id, registry_verification, other | proof_of_completion |
| description | String | Opcional | Max 500 chars | "Oficial PDF from AWS" |

**Validaciones Fase 2:**
- [ ] File exists en S3 (verificar ETag)
- [ ] File size ≤ 50 MB
- [ ] File type es válido (MIME type check)
- [ ] Al menos 1 evidencia debe estar presente
- [ ] evidence_document.status = 'uploaded'

**Estado tras Fase 2:** `certification_record.status = 'pending_validation'` (aún no validada)

**Almacenamiento:**
```sql
INSERT INTO evidence_document (
  record_id, file_name, file_type, file_size, 
  classification, s3_key, s3_url, uploaded_at, status
) VALUES (...);
```

---

### Fase 3: Validación por Validator

**Disparador:** Validator recibe notificación "Certificación pendiente validación"

**Actor:** Validator (RF-008 dentro de este contexto)

**Decisiones:**
1. **Approve:** Cert es legítima, pasa a estado `active`
2. **Reject:** Evidencia insuficiente, estado vuelve a `pending_validation` + mensaje de rechazo
3. **RequestInfo:** Pedir más evidencia (campo: `required_info` de texto libre)

**Validaciones Fase 3:**
- [ ] Validator autenticado con rol `validator`
- [ ] record_id existe y status='pending_validation'
- [ ] Al menos 1 evidencia cargada
- [ ] Decision es uno de: approved, rejected, info_requested
- [ ] Si rejected: reason proporcionado (Max 500 chars)

**Almacenamiento (Approved):**
```sql
-- 1. Update record
UPDATE certification_record 
SET status='active', validation_status='approved', 
    decided_at=NOW(), decided_by=validator_id
WHERE record_id=...;

-- 2. Create validation event
INSERT INTO validation_event (
  record_id, validator_id, decision, reason, occurred_at
) VALUES (...);

-- 3. Audit log (automatic trigger)
INSERT INTO audit_log (
  correlation_id, actor_id, action, entity_type, entity_id,
  before_data, after_data, occurred_at
) VALUES (...);
```

**Estado tras Fase 3 (Approved):** `certification_record.status = 'active'`

**Notificación enviada:** Colaborador notificado "Tu certificación AWS SAA ha sido aprobada"

---

### Fase 4: Notificación (Post-Validación)

**Disparador:** Validación completada (approved/rejected)

**Actor:** Sistema (trigger automático)

**Notificaciones generadas:**
| Decisión | Tipo | Canal | Recipient | Mensaje |
|----------|------|-------|-----------|---------|
| Approved | success | Email | Colaborador | "Certificación aprobada" |
| Approved | info | Email | Manager | "Colaborador obtuvo {cert}" |
| Rejected | warning | Email | Colaborador | "Necesitamos más evidencia" |

---

## 2. Validaciones por Fase

| Validación | Fase | Crítica | Acción |
|------------|------|---------|--------|
| Colaborador existe | 1 | Sí | 400 Bad Request |
| Cert existe | 1 | Sí | 400 Bad Request |
| issue_date ≤ hoy | 1 | Sí | 400 Bad Request |
| expiration_date ≥ issue_date | 1 | Sí | 400 Bad Request |
| Evidencia file_type válido | 2 | Sí | 422 Unprocessable |
| Evidencia file_size ≤ 50MB | 2 | Sí | 413 Payload Too Large |
| Validator autenticado | 3 | Sí | 401 Unauthorized |
| Decision es enum válido | 3 | Sí | 400 Bad Request |
| reason no vacío si rejected | 3 | Sí | 400 Bad Request |

---

## 3. Casos de Borde

| Caso | Precondición | Comportamiento Esperado | Validación SQL |
|------|--------------|------------------------|-----------------|
| **Duplicado antes de validación** | record EXISTS con status='pending_validation' para mismo (collab, cert) | 409 Conflict: "Ya existe certificación pendiente" | `SELECT COUNT(*) FROM certification_record WHERE collaborator_id=? AND certification_id=? AND status='pending_validation'` |
| **Cert expirada al registrar** | issue_date válida pero hoy > calculated expiration | OK - registra como `active` pero marcador de `will_expire_soon` | expiration_date < NOW() → notificación de próximo vencimiento |
| **Evidence borrada antes de validación** | S3 object deleted manualmente | Validator ve estado `evidence_deleted` en UI, validación rechazada | `SELECT status FROM evidence_document WHERE record_id=?` |
| **Validator cambia de rol** | Validator approval en progreso → rol removido | Validación se rechaza automáticamente con audit | Trigger on role_certification_requirement DELETE |
| **Múltiples evidencias** | Colaborador sube 3 PDFs diferentes | System acepta todas, validator ve todas en UI | `SELECT COUNT(*) FROM evidence_document WHERE record_id=?` |
| **Credential ID duplicado** | Otra cert anterior con mismo credential_id | 409 Conflict si `credential_id NOT NULL` | `SELECT COUNT(*) FROM evidence_document WHERE credential_id=? AND record_id !=?` |

---

## 4. SLAs

| Hito | Tiempo Máximo | Responsable | Alerta |
|------|---------------|-------------|--------|
| Subida de evidencia completada | 7 días desde registro | Colaborador | Email @día 3 |
| Validación completada | 10 días desde evidencia cargada | Validator | Escalada @día 10 |
| Notificación enviada | 5 minutos desde decisión | Sistema | Retry x3 si falla |

---

## 5. Ejemplo de Línea de Tiempo

**Semana del 13-19 de mayo de 2024**

```
Lunes 13-may, 10:30 — Colaborador "John" registra AWS SAA
  ✓ Fase 1: Datos validados, status='pending_validation'
  ✓ correlation_id='abc-123', audit log entry created

Martes 14-may, 14:00 — John carga PDF de certificado
  ✓ Fase 2: Presigned URL obtenido, archivo en S3
  ✓ evidence_document.status='uploaded'

Miércoles 15-may, 09:30 — Validator "María" inicia sesión
  → Ve 3 certificaciones pendientes (incluyendo John)
  ✓ Abre evidencia PDF, verifica nombre+fecha

Miércoles 15-may, 09:45 — María aprueba
  ✓ Fase 3: Validation decision='approved'
  ✓ record_id.status='active'
  ✓ validation_event created, audit log updated

Miércoles 15-may, 10:00 — Notificación automática enviada
  ✓ Email a John: "AWS SAA aprobada"
  ✓ Notificación a su manager
  ✓ Dashboard John actualizado en tiempo real
```

---

## 6. Integración con Otros Procesos

```
ALTA-CERT
  ├─ Depende de: ASIGNACIÓN (assignment puede exigir evidencia)
  ├─ Genera: certification_record que se usa en RENOVACIÓN
  └─ Vinculado a: VALIDACIÓN (validator aprueba)

RENOVACIÓN
  ├─ Depende de: ALTA-CERT (necesita record activa previa)
  └─ Mismo flujo de ALTA pero campo renewal_of_record_id ≠ NULL
```

---

## 7. Checklist de Implementación

- [ ] OpenAPI endpoint: `POST /records` (crear record)
- [ ] OpenAPI endpoint: `POST /records/{id}/evidence` (subir evidencia)
- [ ] OpenAPI endpoint: `POST /records/{id}/validation` (validator aprueba/rechaza)
- [ ] S3 presigned URL generation (backend/services/evidence_service.py)
- [ ] Validation rules en backend/services/certification_service.py
- [ ] audit_log trigger automático (backend/database/schema.sql)
- [ ] Email notification service (backend/jobs/notification_job.py)
- [ ] Test cases: TC-006a (registrar válida), TC-006b (rechazar duplicado), TC-006c (validator aprueba)
- [ ] Runbook: "Certificación pendiente validación" → validator workflow

---

**Última actualización:** 2026-05-07  
**Estado:** Implementado y validado  
**Relacionado:** RF-006, RF-008, TC-006a/b/c
