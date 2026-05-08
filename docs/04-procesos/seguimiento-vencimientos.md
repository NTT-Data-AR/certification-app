# Seguimiento de Vencimientos (RF-017)

Detección automática, monitoreo y alertas proactivas sobre certificaciones próximas a vencer. Dispara procesos de renovación.

**Ruta crítica:** `Batch job nightly → Detecta próximas vencer → Genera alertas → Manager/Colaborador notificados`

---

## 1. Fases del Proceso

### Fase 1: Detección Automática (Batch Diario)

**Disparador:** Cron job diario a las 02:00 UTC

**Actor:** Sistema (backend batch job)

**Flujo:**
1. Ejecutar job `backend/jobs/expiration_detector_job.py`
2. Consultar records activas con dates próximas vencer
3. Clasificar por riesgo (crítica, urgente, normal)
4. Crear/actualizar registros en `expiration_alert`
5. Registrar en audit log

**Query de Detección:**

```sql
SELECT 
  cr.record_id, cr.collaborator_id, c.certification_id,
  cr.expiration_date,
  DATEDIFF(cr.expiration_date, CURDATE()) as days_remaining,
  CASE 
    WHEN DATEDIFF(cr.expiration_date, CURDATE()) <= 0 THEN 'expired'
    WHEN DATEDIFF(cr.expiration_date, CURDATE()) <= 7 THEN 'critical'
    WHEN DATEDIFF(cr.expiration_date, CURDATE()) <= 30 THEN 'urgent'
    WHEN DATEDIFF(cr.expiration_date, CURDATE()) <= 90 THEN 'normal'
    ELSE 'future'
  END as risk_level
FROM certification_record cr
JOIN certification c ON cr.certification_id = c.certification_id
WHERE cr.status = 'active'
  AND cr.expiration_date <= DATE_ADD(CURDATE(), INTERVAL 90 DAY)
ORDER BY cr.expiration_date ASC;
```

**Validaciones Fase 1:**
- [ ] records.status='active' (no incluir expiradas, rechazadas, waivered)
- [ ] expiration_date es válida
- [ ] collaborator activo (no inactive)
- [ ] certification_id válida

**Almacenamiento:**

```sql
INSERT INTO expiration_alert (
  record_id, risk_level, days_remaining,
  detected_at, last_notified_at, alert_count,
  requires_renewal
) VALUES (?, ?, ?, NOW(), NULL, 0, 
  CASE WHEN ? < 90 AND ? >= 14 THEN true ELSE false END)
ON DUPLICATE KEY UPDATE
  risk_level = VALUES(risk_level),
  days_remaining = VALUES(days_remaining),
  detected_at = NOW();
```

---

### Fase 2: Generación de Alertas

**Disparador:** Fase 1 detectó expiración próxima

**Actor:** Sistema (batch job)

**Reglas de Alerta por Risk Level:**

| Risk Level | Días Restantes | Alerta | Notificación | Frecuencia |
|------------|-----------------|--------|--------------|-----------|
| future | > 90 | No | No | — |
| normal | 60-90 | Dashboard solo | No | Diaria en dashboard |
| urgent | 30-59 | Amarilla | Email + SMS | Semanal (lun/vie) |
| critical | 7-29 | Roja | Email + SMS + Teams | Cada 2 días |
| expired | 0 o < 0 | Gris + incidencia | Email + SMS + Teams + escalada | Inmediato |

**Alertas Generadas (Fase 2):**

```sql
-- 1. Por cada record con riesgo >= urgent
INSERT INTO notification (
  recipient_id, type, subject, body, channel,
  related_entity_type, related_entity_id, status, created_at
) VALUES (
  ?, 'expiration_alert', 
  'Certificación próxima vencer (7 días)',
  'Tu certificación AWS SAA vence el 2026-05-14. Inicia renovación ahora.',
  'email',
  'certification_record', ?, 'pending', NOW()
);

-- 2. Notificación a Manager (para supervisión)
INSERT INTO notification (
  recipient_id, type, subject, body, channel,
  related_entity_type, related_entity_id, status, created_at
) VALUES (
  ?, 'team_member_expiration_alert',
  'John: Certificación próxima vencer',
  'John - AWS SAA vence en 7 días. Validar renovación.',
  'email',
  'certification_record', ?, 'pending', NOW()
);
```

**Canales de Notificación:**
- Email (siempre)
- SMS (si critical o expired)
- Teams (si critical o expired)
- In-app notification (siempre)
- Dashboard widget (siempre)

---

### Fase 3: Detección de Riesgo de Cobertura

**Disparador:** Alertas generadas, sistema calcula gaps

**Actor:** Sistema (batch, parte de job de detección)

**Flujo:**
1. Para cada expiración que requiere renovación
2. ¿Existe assignment para renovar?
3. Si no existe → crear incidencia "Gap de cobertura"

**Query de Gaps:**

```sql
SELECT 
  ca.collaborator_id, ca.certification_id,
  cr.expiration_date,
  COUNT(CASE WHEN ca.status='pending' THEN 1 END) as pending_assignments,
  COUNT(CASE WHEN ew.waiver_id IS NOT NULL 
              AND ew.valid_to > NOW() THEN 1 END) as waivers_valid
FROM certification_record cr
LEFT JOIN certification_assignment ca 
  ON cr.collaborator_id = ca.collaborator_id 
  AND cr.certification_id = ca.certification_id
LEFT JOIN exception_waiver ew
  ON cr.collaborator_id = ew.collaborator_id
  AND cr.certification_id = ew.certification_id
WHERE cr.status='active'
  AND cr.expiration_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 90 DAY)
  AND ca.status IS NULL  -- No hay assignment pendiente
  AND ew.waiver_id IS NULL  -- No hay waiver válida
GROUP BY ca.collaborator_id, ca.certification_id
ORDER BY cr.expiration_date ASC;
```

**Incidencias de Gap (si aplica):**

```sql
INSERT INTO data_quality_issue (
  issue_type, severity, entity_type, entity_id,
  description, detected_at
) VALUES (
  'coverage_gap', 'high',
  'certification_assignment',
  ?,
  CONCAT('Colaborador ', ?, ' sin asignación de renovación para ',
         ?, '. Vence ', ?),
  NOW()
);
```

---

### Fase 4: Seguimiento Manual (Manager/Auditor)

**Interfaz:** Dashboard de vencimientos

```
┌─ Seguimiento de Vencimientos ──────────────────────────┐
│                                                          │
│ Filtros: [Risk Level ▼] [Unit ▼] [Days Range ▼]       │
│                                                          │
│ ┌─ CRITICAL (7 días) ─────────────────────────────┐   │
│ │  John - AWS SAA - Vence 2026-05-14 ⏰ CRÍTICA   │   │
│ │  Action: [Iniciar renovación] [Crear waiver]   │   │
│ │                                                  │   │
│ │  Maria - Azure AZ-900 - Vence 2026-05-21 ⏰   │   │
│ │  Action: [Iniciar renovación] [Crear waiver]   │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ ┌─ URGENT (30 días) ──────────────────────────────┐   │
│ │  Pedro - GCP ACE - Vence 2026-06-15 ⏱️ URGENTE │   │
│ │  Action: [Iniciar renovación]                   │   │
│ └─────────────────────────────────────────────────┘   │
│                                                          │
│ ┌─ NORMAL (60 días) ──────────────────────────────┐   │
│ │  6 más certificaciones...                       │   │
│ └─────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

**Acciones desde Dashboard:**
- **Iniciar renovación:** Crea assignment + dispara RENOVACIÓN proceso
- **Crear waiver:** Abre modal para crear exception_waiver
- **Marcar completada:** Si renovación ya realizada
- **Snooze alerta:** Silencia por 7 días (audit log)

---

### Fase 5: Renovación Automática (Opcional)

**Disparador:** Si configurado, sistema puede auto-iniciar renovación

**Actor:** Sistema O Manager manual

**Precondiciones para Auto-Renovación:**
- risk_level='critical' (7 días)
- collaborator.status='active'
- assignment no existe para próxima renovación
- Configuración global permitido

**Acción:**

```sql
-- 1. Crear assignment "renovación automática"
INSERT INTO certification_assignment (
  collaborator_id, certification_id, assigned_by,
  assigned_at, due_date, reason,
  status, auto_triggered
) VALUES (
  ?, ?, 'system',
  NOW(), ?, 
  'Renovación automática (próxima expiración)',
  'pending', true
);

-- 2. Notificar a Manager
INSERT INTO notification (...) VALUES (
  manager_id, 'auto_renewal_triggered',
  'Renovación automática iniciada para John - AWS SAA',
  'El sistema inició renovación automática. Validar con John.'
);
```

---

## 2. Validaciones por Fase

| Validación | Fase | Crítica | Acción |
|------------|------|---------|--------|
| record.status='active' | 1 | Sí | Skip (no procesar) |
| expiration_date válida | 1 | Sí | Log error, skip |
| collaborator.status='active' | 1 | No | Igual alert pero marca |
| Risk level clasificación | 2 | Sí | Validar DATEDIFF |
| Notificación recipient existe | 2 | Sí | Log si falla |
| Assignment no duplicada | 5 | Sí | UNIQUE constraint |

---

## 3. Casos de Borde

| Caso | Precondición | Comportamiento | Validación |
|------|--------------|-----------------|-----------|
| **Fecha expiración hoy** | expiration_date=TODAY | risk_level='critical', alert inmediato | DATEDIFF=0 |
| **Ya expirada** | expiration_date < TODAY | risk_level='expired', incidencia, escalada | DATEDIFF<0 |
| **Batch job falló** | Error en job previo | Reintento con backoff exponencial | Monitoring alert |
| **Múltiples alertas** | Mismo record múltiples notificaciones | Consolidar en 1 email, skip duplicados | INSERT ... ON DUPLICATE |
| **Waiver creada después** | Assignment + luego waiver | Waiver se aplica, assignment auto-cancel | Trigger on waiver INSERT |
| **Renovación iniciada** | Assignment creada durante batch | Batch no duplica, respeta | Query checks existing assignment |
| **Collaborator inactivado** | Active → Inactive durante batch | Alerta sigue, pero marcada "inactivo" | LEFT JOIN status check |

---

## 4. SLAs

| Hito | Tiempo Máximo | Responsable | Alerta |
|------|---------------|-------------|--------|
| Batch detectión ejecutada | 02:00 UTC nightly | Sistema | Monitoring alert si falla |
| Alertas generadas | 5 minutos después batch | Sistema | Async job |
| Notificaciones enviadas | 15 minutos después alertas | Notificación service | Retry x3 si falla |
| Manager ve en dashboard | Inmediato (real-time query) | Backend | Cache < 5 min |
| Renovación iniciada | < 24h antes vencimiento | Manager o sistema | Manual + auto option |

---

## 5. Ejemplo de Línea de Tiempo

**Escenario: Detección → Alerta → Renovación iniciada**

```
Martes 07-may, 02:00 UTC — Batch job "expiration_detector" ejecutado
  ✓ Query 500 records activas
  ✓ Detecta: John (AWS SAA, vence 2026-05-14, 7 días)
  ✓ risk_level='critical'
  ✓ INSERT expiration_alert

Martes 07-may, 02:05 — Alertas generadas
  ✓ INSERT notifications (email, SMS, Teams)
  ✓ Dashboard widget actualizado

Martes 07-may, 02:30 — John recibe email
  ✓ Asunto: "AWS SAA vence en 7 días"
  ✓ Body: "Inicia renovación ahora"
  ✓ Link a dashboard

Martes 07-may, 09:00 — Carlos (manager) ve dashboard
  ✓ Widget rojo: "3 certificaciones críticas"
  ✓ Hace clic en John → expiration_alert detail
  ✓ Clic "Iniciar renovación"

Martes 07-may, 09:01 — Renovación iniciada
  ✓ assignment creada (due_date=2026-05-14)
  ✓ Dispara RENOVACIÓN proceso
  ✓ Notificación a John: "Renovación iniciada"

Miércoles 08-may (1 día antes) — Recordatorio urgente
  ✓ Batch job detecta aún sin registro nuevo
  ✓ risk_level aún 'critical' pero updated
  ✓ SMS + Teams: "6 HORAS para vencer"
```

---

## 6. Integración con Otros Procesos

```
SEGUIMIENTO
  ├─ Depende de: ALTA-CERT (records activas)
  ├─ Dispara: RENOVACIÓN (auto o manual)
  ├─ Genera: alertas → notificaciones
  └─ Reportado en: REPORTES (cobertura, riesgos)
```

---

## 7. Checklist de Implementación

- [ ] Batch job: `backend/jobs/expiration_detector_job.py`
- [ ] Cron schedule: `0 2 * * *` (02:00 UTC diario)
- [ ] expiration_alert table en BD
- [ ] Query de detección optimizada (index en expiration_date)
- [ ] Risk level classification logic
- [ ] Notification triggers para cada risk level
- [ ] Dashboard endpoint: `GET /dashboard/expirations`
- [ ] Action handler: `POST /expirations/{id}/action` (iniciar renovación, waiver, etc)
- [ ] Monitoring/alerting: job failed, queue size, latency
- [ ] Test cases: TC-017a (detecta urgente), TC-017b (auto-renovación)
- [ ] Runbook: "Batch job falló", "Alerta duplicada"

---

**Última actualización:** 2026-05-07  
**Estado:** Implementado con nightly batch  
**Relacionado:** RF-017, TC-017a/b
