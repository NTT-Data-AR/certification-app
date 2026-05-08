# Validación y Aprobación de Certificación (RF-008)

Validator revisa evidencia de certificación y decide: aprobar (activa), rechazar (pendiente), o pedir más información.

**Ruta crítica:** `Pendiente → Validator revisa evidencia → Aprueba/Rechaza → Colaborador notificado`

---

## 1. Fases del Proceso

### Fase 1: Detección y Asignación a Validator

**Disparador:** certification_record creada con status='pending_validation'

**Actor:** Sistema (automático)

**Flujo:**
1. Sistema identifica record pendiente
2. Determina qué validator(s) pueden revisar (assignment a role_certification_requirement)
3. Asigna a validator disponible (FIFO de capacity)
4. Envía notificación "Certificación pendiente tu revisión"

**Validaciones Fase 1:**
- [ ] record_id existe, status='pending_validation'
- [ ] Al menos 1 evidence_document cargada
- [ ] evidence_document.status='uploaded'
- [ ] certification_id válida en BD
- [ ] collaborator_id activo

**Almacenamiento:**
```sql
INSERT INTO validation_queue (
  record_id, assigned_to, assigned_at, priority, status
) VALUES (...);

INSERT INTO notification (
  recipient_id, type, subject, body, created_at
) VALUES ('validator@...', 'validation_pending', 
          'Certificación AWS SAA de John pendiente validación',
          'https://app.../records/xxx');
```

---

### Fase 2: Revisión de Evidencia por Validator

**Disparador:** Validator hace clic en certificación pendiente

**Actor:** Validator (rol específico, RF-008)

**Interfaz de Validator:**
```
┌─ Certificación Pendiente ──────────────────────────────┐
│                                                          │
│ Colaborador: John Smith (john@nttdata.com)              │
│ Certificación: AWS Solutions Architect Associate        │
│ Fecha emisión: 2024-05-15                               │
│ Fecha expiración: 2027-05-15                            │
│                                                          │
│ Evidencias cargadas:                                    │
│  [x] proof_of_completion: AWS_Certificate.pdf           │
│  [ ] credential_id: —                                   │
│  [ ] registry_verification: —                           │
│                                                          │
│ Tu decisión:                                            │
│  ◯ Aprobar   ◯ Rechazar   ◯ Pedir más info            │
│                                                          │
│ Motivo (obligatorio si rechazas):                       │
│ [________________________________]                      │
│                                                          │
│        [Guardar decisión]                               │
└──────────────────────────────────────────────────────────┘
```

**Datos revisados por Validator:**
| Elemento | Datos Mostrados | Datos Ocultos (PII) |
|----------|-----------------|---------------------|
| Colaborador | Nombre, Rol, Unidad | Email, ID empleado |
| Certificación | Nombre, Vendor, Vigencia | — |
| Evidencia | Archivo PDF/imagen, fecha | S3 full path |
| Historial | Registros previos de misma cert | — |
| Notas | Campo "reason" del colaborador | Datos personales |

**Validaciones Fase 2:**
- [ ] Validator autenticado, tiene permiso `validation:write`
- [ ] record_id existe, status='pending_validation'
- [ ] Validator diferente de colaborador (no auto-validar)
- [ ] Evidence files son accesibles y válidas
- [ ] Validator puede ver solo records de su scope (RBAC)

---

### Fase 3: Toma de Decisión

**Tres opciones principales:**

#### Opción A: Aprobar (APPROVED)

**Criterios de aprobación:**
- Evidencia es clara y auténtica
- Certificación es válida y actual
- Dates (issue, expiration) son consistentes
- Aplicable a rol/unidad del colaborador

**Almacenamiento:**
```sql
-- 1. Create validation event
INSERT INTO validation_event (
  record_id, validator_id, decision, reason, occurred_at
) VALUES (?, ?, 'approved', NULL, NOW());

-- 2. Update record
UPDATE certification_record 
SET status='active', 
    validation_status='approved',
    decided_by=?, 
    decided_at=NOW()
WHERE record_id=?;

-- 3. Audit log (trigger automático)
INSERT INTO audit_log (
  correlation_id, actor_id, action, entity_type, entity_id,
  before_data, after_data, occurred_at
) VALUES (...);

-- 4. Check if assignment can be completed
UPDATE certification_assignment 
SET status='completed', completed_at=NOW()
WHERE collaborator_id=? AND certification_id=?
  AND status IN ('pending', 'in_progress');
```

**Notificaciones tras APPROVED:**
- ✓ Colaborador: "AWS SAA aprobada"
- ✓ Manager: "John completó AWS SAA"
- ✓ Dashboard en tiempo real

---

#### Opción B: Rechazar (REJECTED)

**Razones comunes de rechazo:**
- Evidencia ilegible o incompleta
- Fecha de emisión en futuro o demasiado antigua
- Certificación no aplicable a su rol
- Credential ID no coincide con documento

**Datos requeridos:**
| Campo | Tipo | Requerido | Rango | Ejemplo |
|-------|------|-----------|-------|---------|
| decision | Enum | Sí | rejected | rejected |
| reason | String | Sí | Max 500 chars | "Certificado vencido según documento" |
| required_info | String | Opcional | Max 500 chars | "Enviar certificado actual o declaración de equivalencia" |
| allow_resubmit | Boolean | Default true | — | true |

**Almacenamiento:**
```sql
-- 1. Create validation event
INSERT INTO validation_event (
  record_id, validator_id, decision, reason, required_info, occurred_at
) VALUES (?, ?, 'rejected', ?, ?, NOW());

-- 2. Update record
UPDATE certification_record 
SET status='pending_validation',  -- Vuelve a pendiente para reintento
    rejected_count = rejected_count + 1,
    last_rejection_reason=?,
    decided_by=?,
    decided_at=NOW()
WHERE record_id=?;

-- 3. Audit log
INSERT INTO audit_log (...) VALUES (...);
```

**Notificaciones tras REJECTED:**
- ⚠️ Colaborador: "Necesitamos más evidencia: {required_info}"
- ⚠️ Manager: "Rechazo para John en AWS SAA - revisar"
- Dashboard marca en rojo

**Límite de rechazos:**
- Máximo 3 rechazos por record
- Tras 3 rechazos: status='rejected' (permanente), assignment='expired'
- Colaborador debe contactar manager/owner

---

#### Opción C: Pedir Más Información (INFO_REQUESTED)

**Cuándo usarla:**
- Evidencia incompleta pero recuperable
- Necesita documento complementario (ej: credential ID registry)
- Duda que puede aclararse rápidamente

**Datos requeridos:**
| Campo | Tipo | Requerido | Ejemplo |
|-------|------|-----------|---------|
| decision | Enum | Sí | info_requested |
| required_info | String | Sí | "Enviar credential ID o registry verification" |
| deadline | Date | Sí | Hoy + 5 días |

**Almacenamiento:**
```sql
-- 1. Create validation event
INSERT INTO validation_event (
  record_id, validator_id, decision, required_info,
  info_deadline, occurred_at
) VALUES (?, ?, 'info_requested', ?, DATE_ADD(NOW(), INTERVAL 5 DAY), NOW());

-- 2. Update record (status NO cambia, sigue pending_validation)
UPDATE certification_record 
SET info_requested_at=NOW(),
    info_required=?,
    info_deadline=DATE_ADD(NOW(), INTERVAL 5 DAY)
WHERE record_id=?;
```

**Notificaciones tras INFO_REQUESTED:**
- 📋 Colaborador: "Se requiere más info: {required_info}. Límite: 5 días"
- ⏰ Sistema envía reminder si no responde en 3 días
- Validator puede ver historial de requests

---

### Fase 4: Validación de Decisión (Confirmación Humana)

**Nota:** Validator ya ES humano. No requiere segunda aprobación.

**Sin embargo, para IA Agent:**
- Si agente sugiere validación, requiere confirmación humana
- Validator revisa y aprueba/rechaza sugerencia

---

## 2. Flujo Detallado de Validación

```
START: record.status='pending_validation'
  │
  ├─ Validator abre record
  │  └─ Lee evidencia, fecha, historial
  │
  ├─ Validator decide:
  │  │
  │  ├─ APPROVED
  │  │  ├─ record.status='active'
  │  │  ├─ assignment auto-completada
  │  │  ├─ Email a colaborador
  │  │  └─ END (certificación activa)
  │  │
  │  ├─ REJECTED
  │  │  ├─ rejected_count++
  │  │  ├─ Si rejected_count >= 3
  │  │  │  ├─ record.status='rejected' (permanente)
  │  │  │  ├─ assignment.status='expired'
  │  │  │  └─ END (rechazada definitivamente)
  │  │  │
  │  │  └─ Si rejected_count < 3
  │  │     ├─ record.status='pending_validation'
  │  │     ├─ Email con motivo y opción reintento
  │  │     └─ END (abierta a reintento)
  │  │
  │  └─ INFO_REQUESTED
  │     ├─ record.status='pending_validation'
  │     ├─ info_deadline=NOW()+5d
  │     ├─ Email con requerimiento
  │     └─ END (esperando colaborador)
  │
  └─ [Cron job diario: check expiradas]
     └─ Si info_deadline < NOW() → auto-rechazar como "No respondió"
```

---

## 3. Validaciones por Fase

| Validación | Fase | Crítica | Acción |
|------------|------|---------|--------|
| Validator autenticado | 2 | Sí | 401 Unauthorized |
| Tiene permiso validation:write | 2 | Sí | 403 Forbidden |
| record_id existe, pending | 2 | Sí | 404 Not Found |
| Evidence cargada | 2 | Sí | 400 Bad Request |
| Decision es enum válido | 3 | Sí | 400 Bad Request |
| Reason no vacío si rejected | 3 | Sí | 400 Bad Request |
| required_info no vacío si info_req | 3 | Sí | 400 Bad Request |

---

## 4. Casos de Borde

| Caso | Precondición | Comportamiento | Validación |
|------|--------------|-----------------|-----------|
| **Double validation** | 2 validators aprueban simultáneamente | 1ª gana, 2ª recibe 409 Conflict | DB constraint UNIQUE(record, validator) |
| **Validator pierde rol** | Validation en progreso → validator removido | Validación se rechaza automáticamente | Trigger on role DELETE |
| **Evidence borrada antes de validación** | S3 object deleted | Validator ve "evidencia no disponible", validación rechazada | `SELECT s3_status FROM evidence_document` |
| **Record expirada mientras se revisa** | Expiration date llegó durante revisión | Validación aún se completa (historial), pero record marca 'expired' | Batch job de expiración es independiente |
| **Colaborador registra nueva evidencia** | Mientras validator revisa | Nueva evidence cargada, validator puede ver ambas | Query todas las evidencias del record |
| **Rechazos repetidos** | 3 rechazos acumulados | 4ª tentativa → validación rechazada automáticamente | `WHERE rejected_count >= 3 AND status='pending'` |

---

## 5. SLAs

| Hito | Tiempo Máximo | Responsable | Alerta |
|------|---------------|-------------|--------|
| Notification enviada a validator | 5 minutos desde registro | Sistema | Retry x3 |
| Validación completada | 10 días desde evidencia cargada | Validator | Escalada @día 10 |
| Decisión comunicada a colaborador | 1 minuto desde validator decision | Sistema | Retry x3 |
| Info deadline expirada | 5 días desde request | Sistema | Auto-rechazar si no responde |

---

## 6. Ejemplo de Línea de Tiempo

**Escenario: Aprobación exitosa con minor issue request**

```
Viernes 15-may, 09:30 — John registra AWS SAA
  ✓ record.status='pending_validation'
  ✓ Notificación a validators disponibles

Viernes 15-may, 10:00 — María (validator) asignada
  ✓ María abre dashboard, ve 3 pendientes
  ✓ Ordena por priority (John=high) y edad

Viernes 15-may, 10:15 — María abre evidencia de John
  ✓ Ve PDF de certificado AWS
  ✓ Verifica: nombre, fechas, ID credencial
  ✓ Decisión: "credential_id en documento no visible"
  ✓ Selecciona INFO_REQUESTED

Viernes 15-may, 10:20 — Email a John
  ✓ "Se requiere credential ID del documento"
  ✓ "Plazo: 5 días (20-may)"

Viernes 15-may, 14:00 — John sube nuevo documento
  ✓ Carta de AWS con credential ID visible
  ✓ record.status aún 'pending_validation'
  ✓ Notificación a María: "Nueva evidencia disponible"

Viernes 15-may, 15:00 — María revisa evidencia actualizada
  ✓ Ahora ve credential ID claramente
  ✓ Decisión: APPROVED
  ✓ record.status='active'

Viernes 15-may, 15:05 — Notificaciones automáticas
  ✓ John: "AWS SAA aprobada! 🎉"
  ✓ Carlos (manager): "John completó AWS SAA"
  ✓ Dashboard en tiempo real
```

---

## 7. Integración con Otros Procesos

```
VALIDACIÓN
  ├─ Depende de: ALTA-CERT (record debe existir)
  ├─ Completa: ASIGNACIÓN (si exists, auto-complete)
  ├─ Genera: validation_event (para auditoría)
  └─ Dispara: RENOVACIÓN (si próxima vencer)
```

---

## 8. Checklist de Implementación

- [ ] OpenAPI endpoint: `POST /records/{id}/validation` (validator decide)
- [ ] OpenAPI endpoint: `GET /validations/queue` (validator task list)
- [ ] Permission check: `validation:write` role
- [ ] Validator assignment logic (queue FIFO)
- [ ] PII masking: no mostrar email/ID empleado
- [ ] Trigger: auto-complete assignment si approved
- [ ] Trigger: auto-reject si 3 rechazos
- [ ] Cron job: check info_deadline expirada y auto-reject
- [ ] Email service: notificaciones de aprobación/rechazo
- [ ] Dashboard widget: "Pendiente tu validación (3)"
- [ ] Test cases: TC-008a (approve), TC-008b (reject), TC-008c (info_request)
- [ ] Runbook: "Validator workflow"

---

**Última actualización:** 2026-05-07  
**Estado:** Implementado y validado  
**Relacionado:** RF-008, TC-008a/b/c
