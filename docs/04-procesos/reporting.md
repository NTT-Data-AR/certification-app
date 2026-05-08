# Reportería y Exportación de Datos (RF-016)

Generación de reportes de cobertura, indicadores KPI y exportación segura de datos para análisis, auditoría y compliance.

**Ruta crítica:** `Usuario solicita reporte → Backend consulta vistas → Aplica RBAC → Retorna o exporta`

---

## 1. Tipos de Reportes

### Tipo A: Reporte de Cobertura (Coverage Report)

**Objetivo:** Medir % de colaboradores con certificaciones requeridas y activas por rol/unit/nivel.

**Acceso:** Manager (su unit), Owner (todas), Auditor (lectura)

**Métrica Principal:**
```
Coverage % = (Colaboradores con certs activas / Colaboradores esperados) * 100
```

**Detalles del Reporte:**

| Dimensión | Ejemplo | Cálculo |
|-----------|---------|---------|
| Unidad | Cloud Services | Manager ve solo su unit |
| Rol | Senior Cloud Architect | LEFT JOIN professional_role |
| Certificación requerida | AWS SAA | INNER JOIN role_certification_requirement |
| Colaboradores esperados | 12 | COUNT DISTINCT con ROLE y UNIT |
| Con cert activa | 10 | COUNT con certification_record.status='active' |
| Faltantes | 2 | 12 - 10 |
| % Cobertura | 83% | (10 / 12) * 100 |

**Query Base:**

```sql
SELECT 
  bu.unit_name,
  pr.role_name,
  c.certification_name,
  COUNT(DISTINCT coll.collaborator_id) as expected_count,
  COUNT(DISTINCT CASE WHEN cr.status='active' AND cr.expiration_date > NOW() 
                      THEN coll.collaborator_id END) as with_active_cert,
  COUNT(DISTINCT CASE WHEN ca.status IN ('pending', 'in_progress')
                      THEN coll.collaborator_id END) as with_pending_assignment,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN cr.status='active' 
                                     THEN coll.collaborator_id END) / 
        COUNT(DISTINCT coll.collaborator_id), 2) as coverage_pct
FROM business_unit bu
JOIN collaborator coll ON bu.unit_id = coll.unit_id
JOIN professional_role pr ON coll.role_id = pr.role_id
JOIN role_certification_requirement rcr ON pr.role_id = rcr.role_id
JOIN certification c ON rcr.certification_id = c.certification_id
LEFT JOIN certification_record cr 
  ON coll.collaborator_id = cr.collaborator_id
  AND c.certification_id = cr.certification_id
  AND cr.status='active'
LEFT JOIN certification_assignment ca
  ON coll.collaborator_id = ca.collaborator_id
  AND c.certification_id = ca.certification_id
  AND ca.status IN ('pending', 'in_progress')
WHERE coll.status='active'
  AND bu.unit_id=?  -- Aplicar RBAC: si Manager, filtrar su unit
GROUP BY bu.unit_id, pr.role_id, c.certification_id
ORDER BY coverage_pct ASC;
```

**Ejemplo Resultado:**

```
Cloud Services / Senior Cloud Architect / AWS SAA:
  Esperados: 12
  Con cert activa: 10
  Pending assignment: 1
  Cobertura: 83.3%
  Gaps: ["John (sin asignación)", "Maria (vence 2026-05-15)"]
```

---

### Tipo B: Reporte de Vencimientos (Expiration Report)

**Objetivo:** Identificar certificaciones próximas vencer, ordenadas por urgencia.

**Acceso:** Manager, Owner, Auditor

**Query:**

```sql
SELECT 
  bu.unit_name,
  coll.collaborator_name,
  c.certification_name,
  cr.issue_date,
  cr.expiration_date,
  DATEDIFF(cr.expiration_date, CURDATE()) as days_remaining,
  cr.status,
  CASE 
    WHEN DATEDIFF(cr.expiration_date, CURDATE()) <= 0 THEN 'EXPIRED'
    WHEN DATEDIFF(cr.expiration_date, CURDATE()) <= 7 THEN 'CRITICAL'
    WHEN DATEDIFF(cr.expiration_date, CURDATE()) <= 30 THEN 'URGENT'
    WHEN DATEDIFF(cr.expiration_date, CURDATE()) <= 90 THEN 'NORMAL'
  END as risk_level
FROM certification_record cr
JOIN collaborator coll ON cr.collaborator_id = coll.collaborator_id
JOIN business_unit bu ON coll.unit_id = bu.unit_id
JOIN certification c ON cr.certification_id = c.certification_id
WHERE cr.status='active'
  AND cr.expiration_date <= DATE_ADD(CURDATE(), INTERVAL 90 DAY)
ORDER BY cr.expiration_date ASC;
```

---

### Tipo C: Reporte de Validaciones (Validation Report)

**Objetivo:** Auditoría de quién validó qué, cuándo, y resultados.

**Acceso:** Validator, Owner, Auditor

**Columnas:**

| Campo | Fuente | Uso |
|-------|--------|-----|
| Colaborador | collaborator | Quién fue validado |
| Certificación | certification | Qué se validó |
| Validator | validation_event.validator_id | Quién validó |
| Decisión | validation_event.decision | Aprobado/rechazado |
| Fecha | validation_event.occurred_at | Cuándo |
| Motivo | validation_event.reason | Por qué |

---

### Tipo D: Reporte de Auditoría (Audit Trail)

**Objetivo:** Compliance & forensics - quién hizo qué, cuándo, por qué.

**Acceso:** Auditor (solo), Owner (limitado), Compliance officer

**Almacenamiento:** Directo desde `audit_log` table (append-only)

**Filtros:**
- Actor (usuario ID)
- Action (create, update, delete, validate, waiver)
- Entity type (certification, assignment, record, waiver)
- Date range
- Correlation ID (rastrear request completo)

---

## 2. Generación de Reportes On-Demand

**Disparador:** Usuario hace clic "Descargar reporte" o API GET `/reports/{type}`

**Actor:** Manager, Owner, Auditor (según permisos)

**Flujo:**

```
1. Request: GET /reports/coverage?unit_id=xyz&format=json|csv|pdf
   │
2. Backend: Validar permiso (RBAC)
   └─ Si Manager: unit_id debe ser su unit
   └─ Si Owner: permitir cualquier unit
   └─ Si Auditor: permitir pero marcar as auditor-read-only
   │
3. Query: Ejecutar query de reporte
   │
4. Format:
   └─ JSON: Array de objetos
   └─ CSV: Pipe-delimited, UTF-8
   └─ PDF: Con header/footer, logo, watermark
   │
5. Return:
   └─ JSON: Direct response
   └─ CSV/PDF: 200 OK + Content-Disposition: attachment
   │
6. Audit: Registrar "auditor descargó reporte" en audit_log
```

**Validaciones:**
- [ ] Usuario autenticado
- [ ] Tiene permiso para reporte type
- [ ] Unit ID válida (si aplica)
- [ ] Date range válida
- [ ] No exceeds row limit (max 10,000 rows)

**Almacenamiento:**

```sql
INSERT INTO report_download_log (
  report_id, reporter_id, report_type, filters,
  row_count, file_format, file_size, downloaded_at
) VALUES (?, ?, ?, ?, ?, ?, ?, NOW());
```

---

## 3. Reportes Programados (Scheduled)

**Objetivo:** Enviar reportes automáticos a stakeholders en cadencia (semanal, mensual)

**Configuración:**

| Frecuencia | Recipient | Report Type | Format | Día/Hora |
|-----------|-----------|------------|--------|----------|
| Semanal | Managers | Coverage | PDF | Lunes 08:00 UTC |
| Mensual | Owner | Coverage + Expirations + Validation | PDF | 1st day, 09:00 UTC |
| Mensual | Auditor | Audit Trail | CSV | 1st day, 10:00 UTC |

**Job (Scheduled):**

```python
# backend/jobs/scheduled_report_job.py
def send_scheduled_reports():
    reports = query_scheduled_reports(
        status='enabled',
        schedule_day=today,
        schedule_hour=current_hour
    )
    
    for report_config in reports:
        # 1. Generate
        data = generate_report(
            report_config.report_type,
            report_config.filters
        )
        
        # 2. Format
        file_content = format_report(data, report_config.format)
        file_name = f"{report_config.name}_{date}.{report_config.format}"
        
        # 3. Email
        send_email(
            to=report_config.recipients,
            subject=f"Monthly Report: {report_config.name}",
            body="See attachment",
            attachment=(file_name, file_content)
        )
        
        # 4. Archive
        store_in_s3(f"reports/archive/{report_config.name}/{file_name}", file_content)
        
        # 5. Audit
        log_report_sent(report_config.id, len(recipients), len(data))
```

---

## 4. Exportación Segura de Datos

**Objetivo:** Permitir exportación para análisis externo sin exponer PII

**Opciones:**

#### Opción A: Export sin PII (Recomendado)

**Datos Incluidos:**
- Certification name, vendor (sí)
- Collaborator ID (sí, UUID)
- Collaborator name (parcial: "John D.")
- Email (no)
- Phone (no)
- Employee number (no)

```csv
unit_name,role_name,certification_name,collaborator_id,collaborator_name,status,coverage_pct
Cloud Services,Senior Architect,AWS SAA,uuid-123,John D.,active,83%
```

#### Opción B: Export con PII (Solo si autorizado)

**Requisito:** Owner + IT Director approval

**Datos Incluidos:** Todos (incluyendo email, phone, SSN si existe)

**Auditoría:** Registrar quién, qué, cuándo, para qué

```sql
INSERT INTO sensitive_data_export_log (
  exporter_id, export_type, row_count,
  approved_by, approval_reason, exported_at
) VALUES (?, ?, ?, ?, ?, NOW());
```

---

## 5. Almacenamiento de Reportes

**Histórico:**

```
S3 Bucket: cert-app-reports-prod
├─ 2026/05/07/coverage_report_20260507.csv
├─ 2026/05/07/coverage_report_20260507.pdf
├─ 2026/05/01/monthly_report_202605.pdf
└─ 2026/04/01/monthly_report_202604.pdf

Retention: 2 años (después archive a Glacier)
```

---

## 6. KPIs y Métricas

**Dashboard KPI (Owner level):**

```
┌─ Certification Coverage ──────────────────────────┐
│  Overall: 87.3% ↑ (was 85.2% last month)         │
│  Cloud Services: 92% | Data Analytics: 78%       │
│                                                    │
├─ Critical Expirations ──────────────────────────┐
│  7-day: 5 certificates                           │
│  30-day: 18 certificates                         │
│  Action: Initiate 5 renewals                     │
│                                                    │
├─ Recent Validations ───────────────────────────┐
│  This week: 23 validated (21 approved, 2 rejected)
│  Validator: Maria 12, Juan 8, Pedro 3           │
│                                                    │
├─ Assignment Tracking ───────────────────────────┐
│  Total assigned: 450 | Completed: 387 (86%)     │
│  Pending: 63 | Expired: 0                       │
└─────────────────────────────────────────────────┘
```

---

## 7. Validaciones

| Validación | Crítica | Acción |
|------------|---------|--------|
| Usuario tiene permiso | Sí | 403 Forbidden |
| Report type válido | Sí | 400 Bad Request |
| Unit ID (si aplica) existe | Sí | 400 Bad Request |
| Row limit no excedido | Sí | 429 Too Many |
| Format válido (json/csv/pdf) | Sí | 400 Bad Request |

---

## 8. SLAs

| Hito | Tiempo Máximo | Responsable |
|------|---------------|-------------|
| Reporte on-demand | 5 segundos | Backend |
| Exportación PDF | 30 segundos | PDF generator |
| Reporte programado enviado | 15 minutos | Scheduler |
| Archivo archivado en S3 | 1 hora | S3 sync job |

---

## 9. Ejemplo de Flujo

```
Miércoles 07-may, 10:00 — Carlos (Manager) abre Dashboard
  ✓ Ve widget "Coverage: Cloud Services 87%"
  ✓ Hace clic "Descargar reporte completo"
  ✓ GET /reports/coverage?unit_id=cloud-services&format=pdf

Miércoles 07-may, 10:02 — Backend genera PDF
  ✓ Query 12 certificaciones requeridas
  ✓ Calcula cobertura, gaps, riesgos
  ✓ Renderiza PDF con tablas, gráficos
  ✓ 200 OK + PDF attachment

Miércoles 07-may, 10:03 — Carlos descarga
  ✓ file: coverage_20260507.pdf
  ✓ Auditor ve log: "Manager Carlos descargó coverage report"
```

---

## 10. Checklist de Implementación

- [ ] Reporting views en BD: `backend/database/views_reporting.sql`
- [ ] Endpoints: `GET /reports/{type}` con parámetros
- [ ] RBAC por reporte type
- [ ] PDF generation (ReportLab o similar)
- [ ] CSV export con proper escaping
- [ ] Scheduled report job
- [ ] S3 storage para archivos generados
- [ ] Report download audit logging
- [ ] KPI dashboard query optimization
- [ ] Test cases: TC-016a (coverage), TC-016b (export)
- [ ] Runbook: "Reporte toma demasiado tiempo", "PDF error"

---

**Última actualización:** 2026-05-07  
**Estado:** Implementado con múltiples report types  
**Relacionado:** RF-016, TC-016a/b
