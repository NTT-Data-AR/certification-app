# Asignación de Certificación a Colaborador (RF-002, RF-013)

Asignar certificaciones requeridas a colaboradores para cumplir en un período específico (assignment).

**Ruta crítica:** `Manager → Asigna Cert → Colaborador notificado → Busca cumplir → Manager seguimiento`

---

## 1. Fases del Proceso

### Fase 1: Iniciación (Manager Asigna)

**Disparador:** Manager hace clic en "Asignar certificación" para un colaborador o grupo

**Actor:** Manager (RF-002) o Dueño de Catálogo (RF-013)

**Datos de Asignación:**
| Campo | Tipo | Requerido | Rango | Ejemplo |
|-------|------|-----------|-------|---------|
| collaborator_id | UUID | Sí | Válido en BD | john@nttdata.com |
| certification_id | UUID | Sí | Válido en catálogo | AWS Solutions Architect |
| assigned_at | DateTime | Sí | ≤ ahora | 2026-05-07T10:30:00Z |
| due_date | Date | Sí | > assigned_at | 2026-12-31 |
| reason | String | Opcional | Max 500 chars | "Requisito para proyecto X" |
| priority | Enum | Opcional | low, medium, high, critical | high |
| notes | String | Opcional | Max 1000 chars | "Validar con HR si experiencia equivalente" |

**Validaciones Fase 1:**
- [ ] Manager autenticado, tiene permiso `assignment:write` (RF-002)
- [ ] O Dueño de catálogo, permiso `assignment:write:all` (RF-013)
- [ ] Si Manager: collaborator_id es reporta directa (relación en business_unit)
- [ ] collaborator_id existe y status ≠ 'inactive'
- [ ] certification_id existe en catálogo
- [ ] due_date ≥ 14 días desde hoy (mínimo 2 semanas)
- [ ] due_date ≤ 4 años desde hoy (máximo razonable)
- [ ] No existe assignment ACTIVA para este (collab, cert)
- [ ] priority es uno de: low, medium, high, critical

**Cálculo de Vigencia:**
```sql
validity_months = (SELECT validity_months FROM certification WHERE certification_id=?);
expected_completion = due_date - (validity_months * 30 días)
-- Ejemplo: due_date=2026-12-31, validity=36 meses
--          expected_completion ≈ 2024-01-01 (retrocediendo 3 años)
```

**Estado tras Fase 1:** `certification_assignment.status = 'pending'`

---

### Fase 2: Notificación a Colaborador

**Disparador:** Assignment creada exitosamente

**Actor:** Sistema (trigger automático)

**Notificaciones:**
| Tipo | Canal | Recipient | Plantilla | Tiempo |
|------|-------|-----------|-----------|--------|
| assignment_created | Email | Colaborador | "Se te asignó AWS SAA con vencimiento 2026-12-31" | Inmediato |
| assignment_created | Dashboard | Colaborador | Widget "Nuevas asignaciones (1)" | Inmediato |
| assignment_created | Email | Manager | "Asignación creada para John: AWS SAA" | Inmediato |

**Almacenamiento:**
```sql
INSERT INTO certification_assignment (
  collaborator_id, certification_id, assigned_at, due_date,
  reason, priority, status, assigned_by
) VALUES (...);

INSERT INTO notification (
  recipient_id, type, status, channel, subject, body,
  created_at
) VALUES (...);
```

---

### Fase 3: Validación de Reglas (Automática)

**Disparador:** Assignment creada

**Actor:** Sistema (trigger)

**Reglas Aplicadas:**
1. **Sobreposición con recordes activas**
   - Si existe `certification_record` activa para esta (collab, cert) → assignment completada automáticamente
   - Status: `assignment.status = 'completed'`
   - Fecha completada: `completed_at = certification_record.validation_approved_at`

2. **Waiver (excepción) existente**
   - Si existe `exception_waiver` válida → assignment marcada como "waivered"
   - Status: `assignment.status = 'waivered'`
   - Razón: heredada del waiver

3. **Requiere confirmación de Manager**
   - Si `priority = 'critical'` → assignment requiere confirmación explícita
   - Status: `pending_manager_confirmation`
   - Manager debe hacer clic "Confirmar asignación"

**Validaciones Fase 3:**
```sql
-- 1. ¿Existe record activa?
SELECT COUNT(*) FROM certification_record 
WHERE collaborator_id=? AND certification_id=? 
  AND status='active' AND expiration_date > NOW();
-- Si > 0 → assignment.status='completed'

-- 2. ¿Existe waiver válida?
SELECT COUNT(*) FROM exception_waiver 
WHERE collaborator_id=? AND certification_id=?
  AND valid_from <= NOW() AND valid_to > NOW();
-- Si > 0 → assignment.status='waivered'
```

---

### Fase 4: Seguimiento (Manager + Sistema)

**Disparador:** Período desde asignación hasta due_date

**Actor:** Manager (verifica manualmente), Sistema (alertas automáticas)

**Alertas Generadas:**
| Tiempo Restante | Alerta | Recipient | Acción |
|-----------------|--------|-----------|--------|
| > 90 días | info (opcional) | Manager | Dashboard solo |
| 60 días | reminder (amarilla) | Colaborador + Manager | Email + SMS |
| 30 días | urgente (roja) | Colaborador + Manager | Email + SMS + Teams |
| 7 días | crítica (roja) | Colaborador + Manager + Owner | Escalada + Teams |
| 0 días (vencida) | vencida (gris) | Colaborador + Manager + Owner | Incidencia automática |

**Dashboard Manager:**
```
Asignaciones por estado:
  ✓ Completadas: 8 (80%)
  ⏳ Pendientes: 2 (20%)
     - John: AWS SAA (vence 2026-12-20) [30 días]
     - Maria: GCP ACE (vence 2026-12-25) [35 días]
  ❌ Vencidas: 1
     - Pedro: Azure AZ-900 (vencía 2026-05-01)
```

---

### Fase 5: Cierre (Automática o Manual)

**Cierre Automático (Sistema):**
- Colaborador registra certification_record y es aprobada → assignment.status='completed'
- O existe waiver válida → assignment.status='waivered'
- O fecha debido pasada y no hay evidencia → assignment.status='expired' (nuevo estado)

**Cierre Manual (Manager):**
- Manager marca assignment como completada si evidencia es externa (experiencia equivalente no documentada)
- Requiere approving comment (evidencia contextual)
- Manager mark como "waivered" solo si existe excepción formal

**Almacenamiento (Cierre Automático):**
```sql
UPDATE certification_assignment 
SET status='completed', completed_at=NOW(),
    completed_via='record_validation' -- o 'waiver_granted'
WHERE assignment_id=?;
```

---

## 2. Validaciones por Fase

| Validación | Fase | Crítica | Acción |
|------------|------|---------|--------|
| Manager tiene permiso | 1 | Sí | 403 Forbidden |
| collaborator_id es reporta | 1 | Sí | 403 Forbidden |
| Colaborador activo | 1 | Sí | 400 Bad Request |
| Cert existe | 1 | Sí | 400 Bad Request |
| due_date ≥ 14 días | 1 | Sí | 400 Bad Request |
| due_date ≤ 4 años | 1 | Sí | 400 Bad Request |
| No existe assignment activa | 1 | No (advertencia) | 409 Conflict (warn) |
| priority es enum | 1 | Sí | 400 Bad Request |

---

## 3. Casos de Borde

| Caso | Precondición | Comportamiento | Validación |
|------|--------------|-----------------|-----------|
| **Doble asignación** | Manager asigna 2x misma cert | 2ª queda pendiente, no duplica | `UNIQUE(collaborator_id, certification_id, status)` |
| **Asignación a inactivo** | collaborator.status='inactive' | 400 Bad Request | `WHERE status ≠ 'inactive'` |
| **Due date en pasado** | Manager pone due_date < hoy | 400 Bad Request | `due_date > CURDATE()` |
| **Cert retirada del catálogo** | Después de asignar, cert marked 'deleted' | Assignment sigue válida (historial) | Soft delete, no cascade |
| **Waiver creada después** | Assignment creada → Luego waiver | Assignment auto-actualizada a 'waivered' | Trigger on waiver INSERT |
| **Record aprobada después** | Assignment pendiente → Record aprobada | Assignment auto-completada | Trigger on validation_event |
| **Manager pierde acceso a unit** | Manager removido de unit → assignments pendientes | Las asignaciones quedan "orfandas" | Alert: "Revisar asignaciones huérfanas" |

---

## 4. SLAs

| Hito | Tiempo Máximo | Responsable | Alerta |
|------|---------------|-------------|--------|
| Asignación creada y notificada | 5 minutos | Sistema | Retry x3 si falla |
| Colaborador inicia registro | N/A (info) | Colaborador | Dashboard reminder |
| Manager valida evidencia | 10 días antes vencimiento | Manager | Email @3 días antes |
| Asignación completada o waivered | En o antes due_date | Colaborador + Manager | Incidencia si vencida |

---

## 5. Ejemplo de Línea de Tiempo (Escenario: Asignación exitosa)

**Mayo 2026**

```
Miércoles 07-may, 10:00 — Manager "Carlos" asigna AWS SAA a John
  ✓ Fase 1: due_date=2026-12-31, priority=high
  ✓ assignment.status='pending'
  ✓ correlation_id='xyz-789', audit_log entry created

Miércoles 07-may, 10:02 — Notificación enviada a John
  ✓ Fase 2: Email: "AWS SAA asignada, vence 2026-12-31"
  ✓ Dashboard John: Widget "1 new assignment"

Miércoles 07-may, 10:05 — Sistema valida reglas automáticamente
  ✓ Fase 3: ¿Existe record activa? No
  ✓ ¿Existe waiver? No
  ✓ Assignment queda en status='pending'

Julio 2026 (30 días antes) — Sistema envía alerta urgente
  ✓ Email a John + Carlos: "AWS SAA vence en 30 días"
  ✓ Dashboard ambos: color rojo

Diciembre 2026, 20-dic — John registra y aprueba certificación
  ✓ certification_record creada y validada
  ✓ Trigger: assignment.status='completed', completed_at=2026-12-20

Diciembre 2026, 20-dic — Notificaciones de cierre
  ✓ John: "AWS SAA assignment completada"
  ✓ Carlos: "John completó AWS SAA"
```

---

## 6. Integración con Otros Procesos

```
ASIGNACIÓN
  ├─ Depende de: CATÁLOGO (certs deben existir)
  ├─ Genera: assignment que motiva ALTA-CERT
  ├─ Puede generar: RENOVACIÓN (si cert próxima vencer)
  ├─ Vinculado a: SOPORTE-EXCEPCIONES (waiver cancela asignación)
  └─ Reportado en: REPORTES (cobertura = asignaciones completadas)
```

---

## 7. Checklist de Implementación

- [ ] OpenAPI endpoint: `POST /assignments` (crear asignación)
- [ ] OpenAPI endpoint: `GET /assignments?status=pending&collaborator_id=...` (listar)
- [ ] OpenAPI endpoint: `PUT /assignments/{id}` (manager marca completada/waivered)
- [ ] Permission checks en backend (assignment:write vs assignment:write:all)
- [ ] Trigger: auto-complete si record aprobada (backend/database/schema.sql)
- [ ] Trigger: auto-waiver si exception_waiver creada
- [ ] Alert job: verificar assignments próximas vencer (backend/jobs/alert_job.py)
- [ ] Dashboard widget: "Asignaciones pendientes" (manager view)
- [ ] Email notification service
- [ ] Test cases: TC-013a (manager asigna), TC-013b (auto-complete), TC-013c (waiver)
- [ ] Runbook: "Asignación vencida" → escalada

---

**Última actualización:** 2026-05-07  
**Estado:** Implementado y validado  
**Relacionado:** RF-002, RF-013, TC-013a/b/c
