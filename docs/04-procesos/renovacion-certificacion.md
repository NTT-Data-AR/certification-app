# Renovación de Certificación

Documentación completa del proceso de renovación de certificaciones próximas a vencer.

## 1. Objetivo

Permitir que colaboradores y managers renueven certificaciones antes de su vencimiento, manteniendo histórico completo de todas las renovaciones y aplicando validaciones antes de registrar la nueva certificación.

## 2. Alcance

**Incluye:**
- Detección automática de certificaciones próximas a vencer (< 90 días)
- Iniciación de renovación por colaborador o manager
- Carga de evidencia de nueva certificación
- Validación por validador autorizado
- Actualización del estado del registro
- Auditoria completa del proceso
- Notificaciones en cada hito

**Excluye (manejo diferente):**
- Certificaciones ya vencidas (re-tomar, no renovar)
- Waivers/excepciones (proceso separado)
- Cambio de proveedor (nueva asignación)

## 3. Actores y Permisos

| Actor | Rol | Responsabilidad | Permisos |
|-------|-----|-----------------|----------|
| **Colaborador** | Propietario | Solicitar renovación, cargar evidencia | `certification:renew:self` |
| **Manager** | Supervisor | Iniciar renovación para equipo, aprobar internamente | `certification:renew:team` |
| **Validador** | Revisor | Aprobar/rechazar evidencia | `validation:write` |
| **Certification Owner** | Administrador | Ver reportes de renovaciones pendientes | `certification:read:all` |
| **Sistema** | Orquestador | Detectar vencimientos, enviar notificaciones, cambiar estados | `system.automatic` |

## 4. Precondiciones

Para iniciar renovación, DEBEN cumplirse:

1. **Certificación existe:**
   - Record con `status = 'active'` y `validation_status = 'approved'`
   - Tenga `expiration_date` (no perpetuo)

2. **Proximidad de vencimiento:**
   - `expiration_date - today <= 90 días` (configurable por administrador)
   - Haya al menos 14 días restantes (buffer mínimo)

3. **Autorización:**
   - Colaborador: renovando la suya propia
   - Manager: renovando para sus reportes directos
   - Solo un intento de renovación activo por certificación por vez

4. **Capacidad:**
   - Colaborador en estado `employment_status = 'ACTIVE'` (no en licencia/inactivo)

## 5. Flujo Principal

```
┌─────────────────────────────────────────────────────────────────────┐
│                    RENOVACIÓN DE CERTIFICACIÓN                      │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ FASE 0: DETECCIÓN (Sistema automático, diaria)                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Job: detect_expiring_certifications (ejecuta cada 24h)             │
│  ┌─ Buscar: certification_records con                               │
│  │  - status = 'active'                                             │
│  │  - validation_status = 'approved'                                │
│  │  - expiration_date ENTRE (today, today + 90 días)               │
│  │                                                                  │
│  └─ Por cada certificación:                                          │
│     • Crear notificación (tipo: RENEWAL_ELIGIBLE)                   │
│     • Enviar email a colaborador + manager                          │
│     • Actualizar dashboard con badge "Renovar"                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FASE 1: INICIACIÓN                                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Actor: Colaborador o Manager                                       │
│  Acción: Clickear "Renovar" en certificación o dashboard            │
│                                                                      │
│  API: POST /api/v1/certifications/{recordId}/renewal-request        │
│                                                                      │
│  Validaciones:                                                       │
│  ✓ Record existe y está en estado renovable                         │
│  ✓ Usuario tiene permiso (self o is_manager)                        │
│  ✓ No hay otra renovación activa para esta cert                     │
│  ✓ Certificación próxima a vencer (< 90 días)                       │
│  ✓ Hay al menos 14 días restantes                                   │
│                                                                      │
│  Request Body:                                                       │
│  {                                                                   │
│    "renewal_reason": "Renovación de certificación",                 │
│    "idempotency_key": "uuid"  // evita duplicados                   │
│  }                                                                   │
│                                                                      │
│  Response 201:                                                       │
│  {                                                                   │
│    "renewal_id": "uuid",                                            │
│    "record_id": "uuid",                                             │
│    "collaborator_name": "John Doe",                                 │
│    "certification_name": "AWS Solutions Architect",                 │
│    "current_expiration": "2026-07-15",                              │
│    "days_remaining": 69,                                            │
│    "status": "pending_evidence",                                    │
│    "created_at": "2026-05-07T10:30:00Z",                            │
│    "evidence_deadline": "2026-06-15"  // 30 días para cargar        │
│  }                                                                   │
│                                                                      │
│  Cambios en BD:                                                      │
│  • Crear renewal_request record (si existe tabla)                   │
│  • Record.status sigue "active" (no cambia)                         │
│  • Crear notificación para validador                                │
│  • Auditar: quien, cuándo, qué                                      │
│                                                                      │
│  Notificaciones:                                                     │
│  • Email a colaborador: "Renovación iniciada, tienes 30 días"       │
│  • Email a manager: "Renovación de {cert} para {person}"            │
│  • Crear tarea en sistema de tickets (opcional)                     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FASE 2: CARGA DE EVIDENCIA                                          │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Actor: Colaborador                                                 │
│  SLA: 30 días desde iniciación                                      │
│                                                                      │
│  Paso 2a: Obtener URL temporal para subir archivo                   │
│  ─────────────────────────────────────────────────────────────────  │
│  API: POST /api/v1/evidences/presigned-url                          │
│  Request:                                                            │
│  {                                                                   │
│    "renewal_id": "uuid",                                            │
│    "file_name": "AWS-Solutions-Architect-cert.pdf",                 │
│    "file_size": 2500000,  // bytes                                  │
│    "file_mime_type": "application/pdf"                              │
│  }                                                                   │
│                                                                      │
│  Validaciones:                                                       │
│  ✓ Archivo < 50MB                                                   │
│  ✓ Tipo MIME permitido (pdf, png, jpg, jpeg)                        │
│  ✓ Renovación aún activa (< 30 días)                                │
│                                                                      │
│  Response:                                                           │
│  {                                                                   │
│    "presigned_url": "https://bucket.s3.amazonaws.com/...?signed",   │
│    "expires_in_seconds": 900,  // 15 minutos                        │
│    "upload_headers": {                                              │
│      "Content-Type": "application/pdf"                              │
│    }                                                                 │
│  }                                                                   │
│                                                                      │
│  Paso 2b: Subir archivo a URL temporal                              │
│  ─────────────────────────────────────────────────────────────────  │
│  Cliente (JavaScript/Web):                                          │
│  ```javascript                                                       │
│  const file = document.getElementById('file-input').files[0];      │
│  const response = await fetch(presigned_url, {                      │
│    method: 'PUT',                                                   │
│    body: file,                                                      │
│    headers: upload_headers                                          │
│  });                                                                 │
│  if (!response.ok) throw new Error('Upload failed');                │
│  ```                                                                 │
│                                                                      │
│  Paso 2c: Notificar al backend que archivo subió                    │
│  ─────────────────────────────────────────────────────────────────  │
│  API: POST /api/v1/evidences                                        │
│  Request:                                                            │
│  {                                                                   │
│    "renewal_id": "uuid",                                            │
│    "record_id": "uuid",                                             │
│    "storage_uri": "s3://bucket/evidences/renewal/uuid/...",         │
│    "file_name": "AWS-Solutions-Architect-cert.pdf",                 │
│    "file_hash": "sha256:abc123...",  // cliente calcula             │
│    "classification": "proof_of_completion"                          │
│  }                                                                   │
│                                                                      │
│  Validaciones:                                                       │
│  ✓ URI válida en storage permitido                                  │
│  ✓ Hash coincide con archivo                                        │
│  ✓ Renovación aún activa                                            │
│  ✓ No hay otra evidencia pendiente                                  │
│                                                                      │
│  Response 201:                                                       │
│  {                                                                   │
│    "evidence_id": "uuid",                                           │
│    "renewal_id": "uuid",                                            │
│    "file_name": "AWS-Solutions-Architect-cert.pdf",                 │
│    "uploaded_at": "2026-05-20T14:30:00Z",                           │
│    "status": "received"                                             │
│  }                                                                   │
│                                                                      │
│  Cambios en BD:                                                      │
│  • Crear evidence_document record                                   │
│  • renewal_request.status = 'pending_validation'                    │
│  • Auditar carga de evidencia                                       │
│                                                                      │
│  Notificaciones:                                                     │
│  • Email a colaborador: "Evidencia recibida, en validación"         │
│  • Email a validador: "Nueva evidencia para validar"                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FASE 3: VALIDACIÓN                                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Actor: Validador certificado                                       │
│  SLA: 10 días hábiles desde evidencia cargada                       │
│                                                                      │
│  Paso 3a: Revisor descarga evidencia (con presigned URL)            │
│  ───────────────────────────────────────────────────────────────────│
│  API: GET /api/v1/evidences/{evidenceId}/download                   │
│  Response: presigned URL válida 5 minutos                           │
│                                                                      │
│  Paso 3b: Validador toma decisión                                   │
│  ───────────────────────────────────────────────────────────────────│
│  API: POST /api/v1/renewals/{renewalId}/validation-decision         │
│                                                                      │
│  Opción A: APROBADO                                                 │
│  ────────────────────────────────────────                           │
│  Request:                                                            │
│  {                                                                   │
│    "decision": "approved",                                          │
│    "notes": "Certificación verificada en AWS portal",               │
│    "new_credential_id": "SAA-C03-CERT-2026-789456",                 │
│    "issue_date": "2026-05-15",                                      │
│    "expiration_date": "2029-05-15"                                  │
│  }                                                                   │
│                                                                      │
│  Validaciones (aprobación):                                          │
│  ✓ issue_date <= today                                              │
│  ✓ expiration_date >= issue_date + 14 days (mínimo)                 │
│  ✓ Validador autorizado                                             │
│  ✓ Evidence existe                                                   │
│                                                                      │
│  Cambios en BD (aprobación):                                         │
│  • Crear NUEVO certification_record con:                            │
│    - collaborator_id: (mismo)                                       │
│    - certification_id: (mismo)                                      │
│    - issue_date: (nuevo)                                            │
│    - expiration_date: (nuevo)                                       │
│    - status: 'active'                                               │
│    - validation_status: 'approved'                                  │
│    - source_system: 'renewal'                                       │
│  • Record anterior pasa a:                                          │
│    - status: 'expired' (marking como histórico)                     │
│  • renewal_request.status = 'completed'                             │
│  • Auditar: validator_id, decision, notes, timestamps               │
│                                                                      │
│  Opción B: RECHAZADO                                                │
│  ────────────────────────────────────────────────────────────────   │
│  Request:                                                            │
│  {                                                                   │
│    "decision": "rejected",                                          │
│    "reason": "Certificado expirado. Proporcione documento válido.",  │
│    "allow_resubmission": true  // permite cargar nueva evidencia    │
│  }                                                                   │
│                                                                      │
│  Cambios en BD (rechazo):                                            │
│  • renewal_request.status = 'rejected'                              │
│  • Si allow_resubmission = true:                                    │
│    - Colaborador puede cargar nueva evidencia (volver a Fase 2)     │
│  • Si allow_resubmission = false:                                   │
│    - Renovación terminada, requiere intervención manual             │
│  • Auditar rechazo                                                   │
│                                                                      │
│  Response (ambos casos):                                             │
│  {                                                                   │
│    "validation_event_id": "uuid",                                   │
│    "renewal_id": "uuid",                                            │
│    "decision": "approved" | "rejected",                             │
│    "notes": "...",                                                  │
│    "validated_at": "2026-05-22T10:15:00Z",                          │
│    "validator_name": "Jane Smith"                                   │
│  }                                                                   │
│                                                                      │
│  Notificaciones:                                                     │
│  Si APROBADO:                                                       │
│  • Email a colaborador: "¡Renovación aprobada! Nueva cert válida"  │
│  • Email a manager: "Renovación completada para {person}"           │
│  • Dashboard actualizado: nueva fecha de vencimiento                │
│                                                                      │
│  Si RECHAZADO:                                                      │
│  • Email a colaborador: "Evidencia rechazada: {reason}"             │
│  • Email a manager: "Acción requerida: renovación fallida"          │
│  • Si allow_resubmission: "Puedes cargar nueva evidencia"           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────┐
        │ ¿APROBADO?                      │
        └────┬────────────────────────┬───┘
             │ SÍ                   │ NO
             ↓                       ↓
    ┌──────────────────┐    ┌──────────────────────────────┐
    │ FASE 4: CIERRE   │    │ FASE 4b: RECHAZO/REINTENTO   │
    └──────────────────┘    └──────────────────────────────┘
             │                       │
             │              Si allow_resubmission:
             │              → Volver a Fase 2 (carga)
             │
             ↓              Si no:
    ┌──────────────────────────────────────────┐
    │ Certificación renovada:                  │
    │ • nuevo record activo con nuevo vencim.  │
    │ • histórico en base de datos             │
    │ • dashboard refrescado                   │
    │ • auditoria completa                     │
    └──────────────────────────────────────────┘
```

## 6. Validaciones por Fase

### Fase 1: Iniciación
- ✓ Record existe con `status = 'active'` y `validation_status = 'approved'`
- ✓ Certificación no expirada (expiration_date > today)
- ✓ Próxima a vencer: `expiration_date - today <= 90 días`
- ✓ Buffer mínimo: `expiration_date - today >= 14 días`
- ✓ Colaborador `employment_status = 'ACTIVE'`
- ✓ Permiso: colaborador (renovar propia) O manager (renovar equipo)
- ✓ No existe otra renovación activa para este record

### Fase 2: Carga de Evidencia
- ✓ Renovación existe y está en `pending_evidence`
- ✓ Archivo: tipo MIME permitido (pdf, png, jpg, jpeg)
- ✓ Archivo: tamaño < 50MB
- ✓ Archivo: hash válido (SHA256 coincide)
- ✓ Plazo: < 30 días desde iniciación
- ✓ Storage: URI accesible y verificable
- ✓ No hay otra evidencia pendiente

### Fase 3: Validación
- ✓ Renovación en estado `pending_validation`
- ✓ Evidence cargada y verificada
- ✓ Validador tiene rol `validation:write`
- ✓ Si aprobación:
  - issue_date <= today
  - expiration_date > issue_date
  - expiration_date >= issue_date + 14 días
  - credential_id único (si se proporciona)
- ✓ Si rechazo: reason no vacía

## 7. Estados

```
pending_evidence
    ↓
pending_validation  [puede rechazarse y volver a pending_evidence]
    ↓
completed (si aprobado) O rejected (si no permite reintento)
```

## 8. Campos Requeridos por Pantalla/API

### Solicitud de Renovación (Fase 1)
```json
{
  "renewal_reason": "string [opcional]",
  "idempotency_key": "uuid"
}
```

### Carga de Evidencia (Fase 2)
```json
{
  "renewal_id": "uuid",
  "record_id": "uuid",
  "storage_uri": "string (s3://...)",
  "file_name": "string",
  "file_hash": "sha256:...",
  "classification": "proof_of_completion"
}
```

### Decisión de Validación (Fase 3)
#### Aprobación:
```json
{
  "decision": "approved",
  "notes": "string",
  "new_credential_id": "string [opcional]",
  "issue_date": "date",
  "expiration_date": "date"
}
```

#### Rechazo:
```json
{
  "decision": "rejected",
  "reason": "string",
  "allow_resubmission": "boolean"
}
```

## 9. Excepciones y Casos Edge

| Caso | Tratamiento |
|------|-----------|
| Certificación vence mientras está en renovación (Fase 2/3) | Cambiar estado automáticamente, pero mantener renovación activa. Permitir validación incluso si vencida (es nueva evidencia) |
| Colaborador se va de licencia durante renovación | Mantener renovación activa, notificar a manager. Manager puede continuar o cancelar |
| Validador rechaza pero collaborator no resubmite (> 30 días) | Crear incidencia. Enviar recordatorio a colaborador + manager |
| Duplicado: 2 renovaciones del mismo record | Rechazar segunda, retornar error 409 (Conflict) |
| Storage no disponible (S3 caído) | Reintento automático con backoff. Alert a operaciones si > 3 intentos |
| Certificación eliminada (soft delete) del catálogo | Renovación se rechaza automáticamente. Notificar a colaborador |

## 10. SLAs y Tiempos

| Fase | Actor | SLA | Alerta |
|------|-------|-----|--------|
| Iniciación → Carga | Colaborador | 30 días | Alert a 25 días |
| Carga → Validación | Sistema | inmediato | - |
| Validación | Validador | 10 días hábiles | Alert a 5 días |
| Total (mejor caso) | - | 40 días | - |

## 11. Ejemplo de Ejecución Completa

**Escenario:** John tiene AWS Solutions Architect venciendo en 69 días.

```
2026-05-07 [10:30] - Sistema detecta que vence el 2026-07-15
2026-05-07 [10:35] - Email a John: "Tu cert vence en 69 días, renovar aquí →"
2026-05-07 [10:35] - Email a manager Jane: "John tiene cert por renovar"
2026-05-07 [14:00] - John abre dashboard, ve "Renovar" en AWS cert
2026-05-07 [14:05] - John clica "Renovar"
              → POST /api/v1/certifications/.../renewal-request
              → renewal_id = "uuid-123", status = "pending_evidence"
              → Email: "Tienes 30 días para subir evidencia"
2026-05-20 [09:00] - John descarga nuevo certificado de AWS portal
2026-05-20 [09:15] - John sube PDF a través de presigned URL
2026-05-20 [09:20] - POST /api/v1/evidences
              → Evidence recibida, renewal.status = "pending_validation"
              → Email a Jane (validador): "Nueva evidencia para revisar"
2026-05-22 [10:00] - Jane descarga PDF desde presigned URL
2026-05-22 [10:15] - Jane verifica en AWS portal: certificado válido
2026-05-22 [10:20] - Jane aprueba:
              → POST /api/v1/renewals/uuid-123/validation-decision
              → decision = "approved"
              → issue_date = "2026-05-15", expiration_date = "2029-05-15"
              → Nuevo record creado, viejo marcado como "expired"
              → renewal_request.status = "completed"
2026-05-22 [10:25] - Email a John: "¡Renovación aprobada! Válida hasta 2029-05-15"
2026-05-22 [10:25] - Email a Jane: "Renovación completada"
2026-05-22 [10:30] - Dashboard actualizado, John ve nueva fecha

Total: 15 días de proceso, 3 acciones de usuario (clic, subida, notificaciones)
```

## 12. Integración con Otros Procesos

### Relación con Asignaciones
- Si hay `certification_assignment` ligada al record original, se considera completada
- No se crea nueva assignment automáticamente (manager puede crear si necesario)

### Relación con Waivers
- Si hay waiver vigente para esta certificación, renovación NO es requerida
- Si renovación se completa, waiver se cancela automáticamente

### Relación con Reporting
- Reportes incluyen: renovaciones pendientes, en progreso, completadas
- Vista: `v_renewal_status` agregada por unidad y periodo

## 13. Checklist de Implementación

- [ ] Crear tabla/modelo `renewal_request`
- [ ] Job para detectar certificaciones próximas a vencer
- [ ] API POST para iniciar renovación (Fase 1)
- [ ] API para presigned URLs (upload + download)
- [ ] API POST para cargar evidencia (Fase 2)
- [ ] API POST para decisión de validación (Fase 3)
- [ ] Estados en BD y máquina de estados
- [ ] SLAs y alertas en jobs
- [ ] Tests: flujo completo, rechazo + reintento, edge cases
- [ ] Auditoria en cada fase
- [ ] Notificaciones (email, dashboard, Teams)
- [ ] Documentación de usuario final

## 14. Referencias

- `docs/03-arquitectura/ARCHITECTURE.md` - Patrones de transacción
- `backend/API.md` - Endpoints REST
- `docs/02-datos/diccionario-datos.md` - Campos y tipos
- `docs/04-procesos/validacion-aprobacion.md` - Proceso de validación
- `docs/04-procesos/alertas-notificaciones.md` - Sistema de notificaciones
