# Soporte de Excepciones y Waivers (RF-012)

Gestión de excepciones: waivers (exención de certificación), equivalencias y casos especiales que justifican desviaciones de la política de certificación.

**Ruta crítica:** `Manager/Dueño solicita waiver → Owner aprueba → Assignment/Record actualizadas → Auditoría completa`

---

## 1. Fases del Proceso

### Fase 1: Solicitud de Waiver

**Disparador:** Manager o dueño hace clic "Solicitar excepción"

**Actor:** Manager (para su unit) o Dueño de catálogo (para todas)

**Razones Comunes de Waiver:**

| Razón | Descripción | Duración Típica | Ejemplo |
|-------|-------------|-----------------|---------|
| Experiencia equivalente | Profesional tiene skills pero no cert formal | 1-3 años | "John tiene 10 años en AWS, técnicamente equivalente a SAA" |
| Contratación externa | Nuevo hire contratado por expertise | Período probatorio | "María contratada como Expert, revisión en 6 meses" |
| Cambio de rol | Rol cambió, nueva cert no aplica | Hasta nuevo rol claro | "Pedro cambió de Cloud Architect a Data Engineer" |
| Disponibilidad examen | Examen no disponible en región | 6-12 meses | "Certificación X solo en 2 ciudades, esperando próximo año" |
| Certificación retirada | Vendor retiró certificación | Permanente | "AWS retiró Solutions Architect Associate" |
| Restricción legal | Contrato prohíbe ciertos trainings | Período contractual | "Consultora restringe en contrato" |
| Transición en progreso | Candidato está preparándose | 6-12 meses | "En preparación para examen, esperar hasta agosto" |

**Datos de Solicitud:**

| Campo | Tipo | Requerido | Rango | Ejemplo |
|-------|------|-----------|-------|---------|
| collaborator_id | UUID | Sí | Válida | uuid-123 |
| certification_id | UUID | Sí | Válida en catálogo | AWS SAA |
| reason | Enum | Sí | Lista arriba | equivalent_experience |
| reason_detail | String | Sí | Max 1000 chars | "John ha trabajado 10 años con AWS, ha liderado..." |
| valid_from | Date | Sí | ≥ hoy | 2026-05-07 |
| valid_to | Date | Sí | ≥ valid_from | 2027-05-07 |
| supporting_evidence | String | Opcional | Max 500 chars, file URL | "reference_from_john@company.com" |
| requested_by | UUID | System | Actor | manager_id |

**Validaciones Fase 1:**
- [ ] Solicitante autenticado, tiene permiso (manager de unit o owner)
- [ ] collaborator_id existe, status='active'
- [ ] certification_id existe
- [ ] valid_from ≥ hoy
- [ ] valid_to ≥ valid_from
- [ ] valid_to ≤ 5 años (límite máximo)
- [ ] No existe waiver no-expirada para este (collaborator, certification)
- [ ] reason es enum válido

**Almacenamiento:**

```sql
INSERT INTO exception_waiver (
  waiver_id, collaborator_id, certification_id,
  reason, reason_detail, supporting_evidence,
  valid_from, valid_to,
  requested_by, status, requested_at
) VALUES (
  UUID(), ?, ?, ?, ?, ?,
  ?, ?,
  ?, 'pending_approval', NOW()
);

INSERT INTO audit_log (
  actor_id, action, entity_type, entity_id,
  before_data, after_data, occurred_at
) VALUES (
  manager_id, 'waiver_requested', 'exception_waiver', waiver_id,
  NULL, '{"reason": "equivalent_experience", ...}', NOW()
);
```

---

### Fase 2: Revisión y Aprobación por Owner

**Disparador:** Waiver creada, status='pending_approval'

**Actor:** Dueño de catálogo (owner rol, RF-012)

**Interfaz de Owner:**

```
┌─ Solicitud de Excepción ────────────────────────────┐
│                                                      │
│ Colaborador: John Smith (john@nttdata.com)         │
│ Certificación: AWS SAA                              │
│ Razón: Experiencia equivalente                      │
│                                                      │
│ Detalles:                                           │
│ "John ha trabajado 10 años con AWS, ha liderado    │
│  15+ proyectos de arquitectura cloud. Técnicamente │
│  equivalente a SAA aunque sin certificación formal" │
│                                                      │
│ Evidencia: Email de manager supportando             │
│                                                      │
│ Vigencia solicitada: 2026-05-07 a 2027-05-07       │
│                                                      │
│ Tu decisión:                                        │
│  ◯ Aprobar   ◯ Rechazar   ◯ Pedir más info        │
│                                                      │
│ Motivo (si rechazas):                              │
│ [_________________________________]                │
│                                                      │
│ Vigencia ajustada (si aplica):                      │
│ Desde: [2026-05-07] Hasta: [2027-05-07]            │
│                                                      │
│        [Guardar decisión]                           │
└────────────────────────────────────────────────────┘
```

**Decisiones:**

#### Opción A: Aprobar

**Almacenamiento:**

```sql
-- 1. Update waiver
UPDATE exception_waiver 
SET status='approved', 
    approved_by=owner_id,
    approved_at=NOW()
WHERE waiver_id=?;

-- 2. Auto-complete related assignments (si existen)
UPDATE certification_assignment
SET status='waivered', completed_at=NOW()
WHERE collaborator_id=? AND certification_id=?
  AND status IN ('pending', 'in_progress');

-- 3. Auto-waiver related records (si existen y pendientes)
UPDATE certification_record
SET status='waivered', decided_at=NOW()
WHERE collaborator_id=? AND certification_id=?
  AND status='pending_validation';

-- 4. Audit log
INSERT INTO audit_log (...) VALUES (
  owner_id, 'waiver_approved', 'exception_waiver', ?, ...
);
```

**Notificaciones:**
- ✓ Manager: "Waiver aprobada para John (AWS SAA, 1 año)"
- ✓ Colaborador: "Tu excepción de AWS SAA fue aprobada"

---

#### Opción B: Rechazar

**Almacenamiento:**

```sql
UPDATE exception_waiver 
SET status='rejected',
    rejected_by=owner_id,
    rejected_at=NOW(),
    rejection_reason=?
WHERE waiver_id=?;

INSERT INTO audit_log (...) VALUES (
  owner_id, 'waiver_rejected', 'exception_waiver', ?, 
  JSON_OBJECT('reason', rejection_reason), NOW()
);
```

**Notificaciones:**
- ⚠️ Manager: "Waiver rechazada: {motivo}"
- ⚠️ Colaborador: "Se requiere certificación requerida"

---

#### Opción C: Pedir más información

**Almacenamiento:**

```sql
UPDATE exception_waiver 
SET status='pending_info',
    info_required=?,
    info_deadline=DATE_ADD(NOW(), INTERVAL 5 DAY)
WHERE waiver_id=?;
```

---

### Fase 3: Vigencia y Expiración

**Disparador:** Cron job diario comprueba expiración

**Actor:** Sistema (batch)

**Query:**

```sql
SELECT * FROM exception_waiver
WHERE status='approved'
  AND valid_to < CURDATE()
ORDER BY valid_to DESC;
```

**Acciones:**

1. **Auto-expirar waiver:**
```sql
UPDATE exception_waiver 
SET status='expired', expired_at=NOW()
WHERE valid_to < CURDATE() AND status='approved';
```

2. **Reactivar assignment (si aplica):**
```sql
UPDATE certification_assignment
SET status='pending',
    reason='Waiver expirada, renovar certificación requerida'
WHERE collaborator_id=? AND certification_id=?
  AND status='waivered'
  AND valid_from <= NOW() AND valid_to < CURDATE();
```

3. **Notificar:**
```
Manager: "Waiver para John - AWS SAA expiró. Certificación nuevamente requerida."
Colaborador: "Tu excepción de AWS SAA expiró. Debes obtener certificación."
```

---

### Fase 4: Renovación de Waiver (si aplica)

**Disparador:** Owner o Manager quiere extender waiver próxima a expirar

**Actor:** Owner (RF-012)

**Flujo:**
1. 30 días antes de expirar: alerta en dashboard
2. Owner abre waiver y hace clic "Renovar"
3. Llena nueva vigencia
4. Crea nueva excepción_waiver con status='approved' (si Owner la auto-apropia)
5. Archiva la anterior (status='expired')

---

## 2. Validaciones por Fase

| Validación | Fase | Crítica | Acción |
|------------|------|---------|--------|
| Solicitante autenticado | 1 | Sí | 401 Unauthorized |
| Tiene permiso (manager o owner) | 1 | Sí | 403 Forbidden |
| collaborator_id existe | 1 | Sí | 400 Bad Request |
| certification_id existe | 1 | Sí | 400 Bad Request |
| valid_from ≥ hoy | 1 | Sí | 400 Bad Request |
| valid_to ≥ valid_from | 1 | Sí | 400 Bad Request |
| No existe waiver activa | 1 | No (warning) | 409 Conflict |
| Owner autenticado | 2 | Sí | 401 Unauthorized |
| Decision es enum válido | 2 | Sí | 400 Bad Request |
| Rejection reason no vacío | 2 | Sí | 400 Bad Request (si rejected) |

---

## 3. Casos de Borde

| Caso | Precondición | Comportamiento | Validación |
|------|--------------|-----------------|-----------|
| **Waiver después assignment** | Assignment creada → Luego waiver | Assignment auto-actualiza a 'waivered' | Trigger on waiver INSERT |
| **Waiver expira mañana** | valid_to = CURDATE()+1 | Batch job ejecuta, alerta enviada | Scheduled batch |
| **Doble waiver** | Existente + nueva para misma cert | Rechazar nueva (constraint) | UNIQUE check |
| **Owner rechaza** | Waiver no aprobada → rechazada | Assignment vuelve a 'pending' | UPDATE cascada |
| **Renovación durante vigencia** | Waiver activa → Nueva solicitada | Crear segunda waiver, archiva la primera después expiration | Soft delete + new INSERT |
| **Certificación retirada del catálogo** | Cert.status='deleted' | Waiver aún válida (historial) | Soft delete, no cascade |
| **Colaborador inactivado** | status='inactive' durante waiver | Waiver sigue válida pero no aplica | LEFT JOIN on collaborator.status |

---

## 4. SLAs

| Hito | Tiempo Máximo | Responsable | Alerta |
|------|---------------|-------------|--------|
| Waiver creada y notificada | 5 minutos | Sistema | Async |
| Owner revisa (SLA) | 2 días | Owner | Email reminder @día 2 |
| Decisión comunicada | 5 minutos | Sistema | Notificación |
| Expiración detectable | 24 horas después fecha | Batch job | Scheduled nightly |
| Renovación iniciada | 30 días antes expiración | Manager | Alert en dashboard |

---

## 5. Ejemplo de Línea de Tiempo

**Escenario: Waiver aprobada y extendida después**

```
Lunes 07-may, 10:00 — Carlos (Manager) solicita waiver para John
  ✓ reason='equivalent_experience'
  ✓ valid_from=2026-05-07, valid_to=2026-05-07 (1 año)
  ✓ Supporting evidence: "John 10 años AWS"
  ✓ waiver.status='pending_approval'

Lunes 07-may, 10:05 — Ana (Owner) notificada
  ✓ Email: "Waiver pendiente aprobación (John - AWS SAA)"

Martes 08-may, 09:00 — Ana revisa y aprueba
  ✓ Abre waiver, verifica experiencia
  ✓ Decision='approved', valid_to=2027-05-07
  ✓ waiver.status='approved'

Martes 08-may, 09:05 — Notificaciones automáticas
  ✓ Carlos: "Waiver aprobada para John (1 año)"
  ✓ John: "Tu excepción de AWS SAA fue aprobada"
  ✓ assignment (si pendiente) auto-completada

Abril 2027 (1 mes antes expiración) — Batch detects
  ✓ valid_to=2027-05-07, TODAY=2027-04-07
  ✓ Dashboard alert: "Waiver John - AWS SAA expira en 30 días"

Mayo 2027, 01-may — Carlos solicita renovación
  ✓ Click "Renovar waiver"
  ✓ Nuevo waiver creado: valid_to=2028-05-07
  ✓ Ana aprueba (o auto-aprueba)

Mayo 2027, 07-may — Vieja waiver auto-expira
  ✓ Batch: valid_to < TODAY
  ✓ status='approved' → 'expired'
  ✓ Nueva waiver ya active (si fue aprobada)
```

---

## 6. Integración con Otros Procesos

```
EXCEPCIONES
  ├─ Dispara: ASIGNACIÓN auto-complete
  ├─ Auto-completa: VALIDACIÓN (si pendiente)
  ├─ Genera: Eventos para REPORTING (compliance)
  └─ Genera: Audit trail (compliance + forensics)
```

---

## 7. Checklist de Implementación

- [ ] exception_waiver table en BD
- [ ] OpenAPI endpoint: `POST /waivers` (crear solicitud)
- [ ] OpenAPI endpoint: `POST /waivers/{id}/decision` (owner aprueba)
- [ ] Permission check: owner rol para aprobar
- [ ] Triggers: auto-complete assignment/record si waiver approved
- [ ] Cron job: detectar expiración diaria
- [ ] Expiración auto-handler: reactivar assignment
- [ ] Batch renewal reminder: 30 días antes
- [ ] Dashboard widget: "Waivers expiring" (Owner)
- [ ] Audit logging completo
- [ ] Email notifications
- [ ] Test cases: TC-012a (solicitar), TC-012b (aprobar), TC-012c (expirar)
- [ ] Runbook: "Waiver rechazada", "Renovación de waiver"

---

**Última actualización:** 2026-05-07  
**Estado:** Implementado con vigencia y expiración  
**Relacionado:** RF-012, TC-012a/b/c
