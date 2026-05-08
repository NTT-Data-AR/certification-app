# Gestión de Evidencias de Certificación (RF-007)

Carga, almacenamiento seguro y gestión del ciclo de vida de documentos de prueba (certificados, credential IDs, registry verification).

**Ruta crítica:** `Colaborador → Solicita presigned URL → Sube archivo S3 → Backend valida → Validator revisa`

---

## 1. Fases del Proceso

### Fase 1: Solicitud de Presigned URL

**Disparador:** Colaborador hace clic en "Subir evidencia" durante registro de certificación

**Actor:** Colaborador (RF-007)

**Flujo:**
1. Colaborador hace POST `/records/{recordId}/evidence/presigned-url`
2. Backend genera UUID para evidence_document
3. Backend crea presigned URL válida por 15 minutos
4. Retorna URL + instrucciones

**Datos de Solicitud:**

| Campo | Tipo | Requerido | Rango | Ejemplo |
|-------|------|-----------|-------|---------|
| record_id | UUID | Sí | Debe existir y ser del colaborador | abc123... |
| classification | Enum | Sí | proof_of_completion, credential_id, registry_verification, other | proof_of_completion |
| description | String | Opcional | Max 500 chars | "Official AWS certificate PDF" |

**Validaciones Fase 1:**
- [ ] Colaborador autenticado
- [ ] record_id existe y collaborator_id es el usuario actual
- [ ] record.status IN ('pending_validation', 'pending_info_response')
- [ ] classification es enum válido
- [ ] No excede límite de 5 evidencias por record

**Respuesta:**

```json
{
  "evidence_document_id": "evt-xyz-789",
  "presigned_url": "https://cert-app-evidences.s3.amazonaws.com/...",
  "expires_in_seconds": 900,
  "max_file_size": 52428800,
  "accepted_content_types": ["application/pdf", "image/jpeg", "image/png"]
}
```

---

### Fase 2: Carga de Archivo a S3

**Disparador:** Colaborador tiene presigned URL válida

**Actor:** Colaborador (navegador, JavaScript)

**Flujo:**
1. Colaborador selecciona archivo local
2. Frontend valida:
   - Tamaño ≤ 50 MB
   - Tipo MIME permitido
3. Frontend sube directamente a presigned URL (sin pasar por backend)
4. S3 retorna 200 OK con ETag

**Validaciones Fase 2 (Frontend):**
- [ ] File size ≤ 50 MB
- [ ] File type en lista permitida (PDF, JPEG, PNG)
- [ ] Presigned URL no expirada (< 15 min)

**Validaciones Fase 2 (S3):**
- [ ] Content-Type en ACL permitidos
- [ ] No sobrescribe archivo existente (S3 key único)
- [ ] Bucket encryption habilitada (AES-256)

**Almacenamiento en S3:**

```
Bucket: cert-app-evidences-prod
Estructura:
  /
  ├─ 2026/05/07/evt-xyz-789/original.pdf
  └─ 2026/05/07/evt-xyz-789/metadata.json

metadata.json:
{
  "evidence_document_id": "evt-xyz-789",
  "collaborator_id": "collab-123",
  "record_id": "rec-456",
  "file_name": "AWS_Certificate.pdf",
  "file_size": 2500000,
  "content_type": "application/pdf",
  "uploaded_at": "2026-05-07T14:30:00Z",
  "uploaded_by": "collab-123",
  "classification": "proof_of_completion"
}
```

---

### Fase 3: Notificación al Backend

**Disparador:** Frontend recibe 200 OK de S3

**Actor:** Colaborador (frontend notifica backend)

**Flujo:**
1. Frontend hace POST `/records/{recordId}/evidence/confirm`
2. Backend verifica ETag en S3 (el archivo fue cargado)
3. Backend crea registro en BD (evidence_document)
4. Backend retorna confirmation

**Datos de Confirmación:**

| Campo | Tipo | Requerido | Ejemplo |
|-------|------|-----------|---------|
| evidence_document_id | UUID | Sí | evt-xyz-789 |
| s3_etag | String | Sí | "3456789abcdef" |
| file_name | String | Sí | "AWS_Certificate.pdf" |

**Validaciones Fase 3:**
- [ ] Backend verifica ETag en S3 (HEAD request)
- [ ] evidence_document_id existe en BD (pending)
- [ ] ETag coincide con almacenado
- [ ] File size ≤ 50 MB (re-verificar)

**Almacenamiento en BD:**

```sql
INSERT INTO evidence_document (
  evidence_document_id, record_id, file_name, file_type,
  file_size, classification, description,
  s3_key, s3_etag, status, uploaded_at, uploaded_by
) VALUES (
  'evt-xyz-789', 'rec-456', 'AWS_Certificate.pdf', 'application/pdf',
  2500000, 'proof_of_completion', 'Official certificate',
  '2026/05/07/evt-xyz-789/original.pdf', '3456789abcdef',
  'uploaded', NOW(), 'collab-123'
);
```

---

### Fase 4: Almacenamiento y Seguridad

**Ubicación:** Amazon S3 (object storage)

**Configuración de Seguridad:**

| Control | Configuración | Propósito |
|---------|---------------|----------|
| Server-Side Encryption | SSE-S3 (AES-256) | Proteger en reposo |
| Bucket policy | NO public access | Evitar exposición accidental |
| CORS | Presigned URL único | Único cliente autorizado |
| Access logs | Enabled | Auditar acceso |
| Versioning | Enabled | Recuperar versiones anteriores |
| Lifecycle | 7 años archiving, 8+ años delete | Retención legal |

**Presigned URL Seguridad:**
- Válida solo 15 minutos
- Una sola operación (PUT)
- Credenciales AWS NO expuestas al cliente
- Cada colaborador solo accede sus propios archivos

---

### Fase 5: Acceso a Evidencia (Validator)

**Disparador:** Validator necesita revisar evidencia

**Actor:** Validator (rol específico)

**Flujo:**
1. Validator accede `/records/{recordId}/evidence`
2. Backend genera presigned GET URL (válida 30 min)
3. Validator descarga/visualiza en navegador

**Validaciones Fase 5:**
- [ ] Validator autenticado, tiene permiso `validation:write`
- [ ] record_id existe
- [ ] evidence_document.status='uploaded'
- [ ] Audit log: quién descargó, cuándo

**Presigned GET URL:**

```json
{
  "evidence_url": "https://..../2026/05/07/evt-xyz-789/original.pdf?expires=...",
  "expires_in": 1800,
  "file_name": "AWS_Certificate.pdf",
  "classification": "proof_of_completion"
}
```

---

### Fase 6: Eliminación y Retención

**Disparador:** Certificación expirada O solicitud de borrado

**Actor:** Sistema (automático) o Auditor (manual)

**Política de Retención:**

| Caso | Retención | Acción |
|------|-----------|--------|
| Record activa | Mientras válida | Mantener en S3, acceso full |
| Record expirada | 7 años | Archivar a Glacier, acceso limited |
| Record rechazada | 1 año | Mantener en S3 (histórico), luego delete |
| GDPR: solicitud borrado | N/A | Soft delete en BD, S3 delete inmediato |

**Borrado (GDPR - Derecho al Olvido):**

```sql
-- 1. BD: soft delete
UPDATE evidence_document 
SET status='deleted', deleted_at=NOW()
WHERE record_id IN (SELECT record_id FROM certification_record 
                     WHERE collaborator_id=?);

-- 2. S3: hard delete
DELETE s3://cert-app-evidences/2026/.../evidence_document_id/*

-- 3. Audit log
INSERT INTO audit_log (
  actor_id, action, entity_type, entity_id,
  reason, occurred_at
) VALUES (?, 'gdpr_erasure', 'evidence_document', ?, 'Solicitud derecho al olvido', NOW());
```

---

## 2. Validaciones por Fase

| Validación | Fase | Crítica | Acción |
|------------|------|---------|--------|
| Colaborador autenticado | 1 | Sí | 401 Unauthorized |
| record_id existe | 1 | Sí | 400 Bad Request |
| record pertenece a colaborador | 1 | Sí | 403 Forbidden |
| classification es enum | 1 | Sí | 400 Bad Request |
| File size ≤ 50 MB | 2 | Sí | 413 Payload Too Large |
| File type permitido | 2 | Sí | 422 Unprocessable |
| ETag coincide | 3 | Sí | 409 Conflict |
| Validator tiene permiso | 5 | Sí | 403 Forbidden |

---

## 3. Casos de Borde

| Caso | Precondición | Comportamiento | Validación |
|------|--------------|-----------------|-----------|
| **Presigned URL expirada** | > 15 min sin subir | 403 Forbidden en S3 | Check uploaded_at timestamp |
| **Upload interrumpido** | 50% del archivo subido | Reintento: nueva presigned URL | Retry count en BD |
| **Duplicado** | 2 colaboradores suben mismo PDF | S3 keys únicos (different UUIDs) | UUID para cada evidence |
| **Metadata tampering** | Cliente modifica metadata.json | Backend re-verifica ETag | S3 object integrity check |
| **Validator descarga expirada record** | record.status='expired' | Aún puede acceder (histórico) | Soft delete, no hard delete |
| **Almacenamiento full** | S3 cuota excedida | Rechazar nueva subida | Monitor S3 usage |
| **Encryption key perdida** | KMS key deleted | Archivos irrecuperables | Backup keys, disaster recovery |

---

## 4. SLAs

| Hito | Tiempo Máximo | Responsable | Alerta |
|------|---------------|-------------|--------|
| Presigned URL generada | 2 segundos | Backend | Monitor latency |
| Archivo cargado | 15 minutos | Colaborador | URL expira, retry |
| Confirmación recibida | 30 segundos | Backend | Async job |
| Acceso por validator | 5 minutos | Backend genera GET URL | Monitor availability |
| Archiving (expirado) | 24 horas después expiración | Sistema batch | Cron job nightly |

---

## 5. Ejemplo de Línea de Tiempo

**Escenario: Colaborador sube certificado, validator revisa**

```
Miércoles 15-may, 14:00 — John registra AWS SAA
  ✓ record creada, status='pending_validation'

Miércoles 15-may, 14:05 — John hace clic "Subir evidencia"
  ✓ POST /records/rec-456/evidence/presigned-url
  ✓ Backend genera presigned PUT URL válida 15 min

Miércoles 15-may, 14:08 — John sube PDF de 2.5 MB
  ✓ Frontend PUT request directo a S3 (sin backend)
  ✓ S3 retorna 200 OK, ETag='3456789abc'
  ✓ Frontend notifica backend

Miércoles 15-may, 14:09 — Backend confirma en BD
  ✓ POST /records/rec-456/evidence/confirm
  ✓ Backend verifica ETag en S3
  ✓ INSERT evidence_document(status='uploaded')

Viernes 17-may, 10:00 — María (validator) abre record
  ✓ GET /records/rec-456/evidence
  ✓ Backend genera presigned GET URL válida 30 min
  ✓ María descarga PDF en navegador
  ✓ Audit log: validator_id=maría, action=download_evidence
```

---

## 6. Integración con Otros Procesos

```
EVIDENCIAS
  ├─ Depende de: ALTA-CERT (record creada)
  ├─ Requerida por: VALIDACIÓN (validator revisa)
  ├─ RENOVACIÓN también sube evidencias
  └─ GDPR: borrado cascada para colaborador
```

---

## 7. Checklist de Implementación

- [ ] AWS S3 bucket creada y configurada
- [ ] Presigned URL generation: `POST /records/{id}/evidence/presigned-url`
- [ ] Presigned URL validation: `POST /records/{id}/evidence/confirm`
- [ ] Evidence retrieval: `GET /records/{id}/evidence`
- [ ] S3 lifecycle policy configurada (7 años archiving)
- [ ] GDPR delete handler: cascade delete de evidencias
- [ ] Audit logging en BD para cada operación
- [ ] Test cases: TC-007a (subir válida), TC-007b (rechazar oversized)

---

**Última actualización:** 2026-05-07  
**Estado:** Implementado con AWS S3 integration  
**Relacionado:** RF-007, TC-007a/b
