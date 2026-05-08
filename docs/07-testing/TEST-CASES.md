# Casos de Prueba Ejecutables

Casos concretos de prueba para cada RF, con datos, pasos y resultados esperados.

**Propósito:** QA tiene exactamente qué probar, sin ambigüedades.

---

## 1. Casos de Prueba: Gestión de Catálogo (RF-001)

### TC-001a: Crear certificación válida

**Setup:**
```json
{
  "vendor_id": "550e8400-e29b-41d4-a716-446655440010",
  "name": "AWS Solutions Architect Associate",
  "code": "SAA-C03",
  "category": "Cloud",
  "level": "Associate",
  "validity_months": 36,
  "requires_evidence": true
}
```

**Pasos:**
1. Usuario: Owner
2. API: `POST /certifications`
3. Body: JSON arriba

**Resultado Esperado:**
```
Status: 201 Created
Body: {
  "certification_id": "uuid-generated",
  "vendor_id": "550e8400...",
  "name": "AWS Solutions Architect Associate",
  "code": "SAA-C03",
  "category": "Cloud",
  "is_active": true,
  "created_at": "2026-05-07T..."
}
```

**Validaciones:**
- ✅ certification_id es UUID válido
- ✅ created_at es timestamp UTC
- ✅ is_active = true por defecto
- ✅ Registrado en audit_log con actor_type='user'

**Limpieza:**
```sql
DELETE FROM certification WHERE certification_id = 'uuid-generated';
```

---

### TC-001b: Rechazar certificación duplicada

**Precondición:** TC-001a completado (cert "AWS Solutions Architect Associate" existe)

**Pasos:**
1. Usuario: Owner
2. API: `POST /certifications`
3. Body: Mismo que TC-001a

**Resultado Esperado:**
```
Status: 409 Conflict
Body: {
  "error": {
    "code": "DUPLICATE_CERTIFICATION",
    "message": "Certificación ya existe (vendor + nombre)",
    "details": {
      "vendor_id": "550e8400...",
      "name": "AWS Solutions Architect Associate",
      "existing_cert_id": "uuid-from-TC-001a"
    }
  }
}
```

**Validaciones:**
- ✅ No se crea segunda cert
- ✅ Error es 409 (Conflict)
- ✅ Retorna ID de la existente

---

### TC-001c: Rechazar validez negativa

**Pasos:**
1. Usuario: Owner
2. API: `POST /certifications`
3. Body: 
```json
{
  "vendor_id": "550e8400...",
  "name": "Invalid Cert",
  "validity_months": -12,
  ...
}
```

**Resultado Esperado:**
```
Status: 422 Unprocessable Entity
Body: {
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [{
      "field": "validity_months",
      "message": "Debe ser > 0",
      "code": "POSITIVE_INTEGER"
    }]
  }
}
```

---

## 2. Casos de Prueba: Registrar Certificación Obtenida (RF-006)

### TC-006a: Registrar certificación válida

**Setup:**
```
Colaborador: john_doe (uuid-collab)
Certificación: AWS SAA (uuid-cert, exists from TC-001a)
```

**Pasos:**
1. Usuario: john_doe (self)
2. API: `POST /records`
3. Body:
```json
{
  "collaborator_id": "uuid-collab",
  "certification_id": "uuid-cert",
  "issue_date": "2023-05-15",
  "expiration_date": "2026-05-15",
  "credential_id": "SAA-C03-2023-123456"
}
```

**Resultado Esperado:**
```
Status: 201 Created
Body: {
  "record_id": "uuid-generated",
  "collaborator_id": "uuid-collab",
  "certification_id": "uuid-cert",
  "issue_date": "2023-05-15",
  "expiration_date": "2026-05-15",
  "status": "active",
  "validation_status": "pending",
  "days_to_expiration": 3,
  "created_at": "2026-05-07T..."
}
```

**Validaciones:**
- ✅ record_id es UUID
- ✅ status = 'active' (hoy está en rango)
- ✅ validation_status = 'pending' (espera validador)
- ✅ days_to_expiration = (2026-05-15 - 2026-05-07) = 8 días
- ✅ Registrado en audit_log

---

### TC-006b: Rechazar fecha inválida

**Pasos:**
1. Usuario: john_doe
2. API: `POST /records`
3. Body:
```json
{
  "collaborator_id": "uuid-collab",
  "certification_id": "uuid-cert",
  "issue_date": "2023-05-15",
  "expiration_date": "2023-05-01",  // ANTES de issue_date
  ...
}
```

**Resultado Esperado:**
```
Status: 422 Unprocessable Entity
Body: {
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [{
      "field": "dates",
      "message": "expiration_date debe ser >= issue_date",
      "code": "INVALID_DATE_RANGE"
    }]
  }
}
```

---

### TC-006c: Rechazar sin permiso (otro usuario)

**Pasos:**
1. Usuario: jane_smith (manager de OTRO equipo)
2. API: `POST /records`
3. Body: Registrar cert para john_doe

**Resultado Esperado:**
```
Status: 403 Forbidden
Body: {
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "No tienes permiso para registrar certs de este colaborador"
  }
}
```

**Validaciones:**
- ✅ No se crea record
- ✅ Intento registrado en audit_log con action='permission_denied'

---

## 3. Casos de Prueba: Validación (RF-008)

### TC-008a: Validador aprueba certificación

**Precondición:** TC-006a completado (record en estado 'pending_validation')

**Pasos:**
1. Usuario: validator_user (tiene rol 'validator')
2. API: `POST /records/{recordId}/validation`
3. Body:
```json
{
  "decision": "approved",
  "reason": "Certificación verificada en AWS portal",
  "credential_id": "SAA-C03-2023-123456"
}
```

**Resultado Esperado:**
```
Status: 200 OK
Body: {
  "validation_event_id": "uuid-generated",
  "record_id": "uuid-from-TC-006a",
  "validator_id": "uuid-validator",
  "decision": "approved",
  "reason": "Certificación verificada en AWS portal",
  "decided_at": "2026-05-07T14:30:00Z"
}
```

**Efectos Secundarios Esperados:**
```sql
-- Record actualizado
SELECT status, validation_status FROM certification_record 
WHERE record_id = 'uuid-from-TC-006a';
-- Resultado: status='active', validation_status='approved'

-- Auditoría registrada
SELECT * FROM audit_log 
WHERE entity_type='validation_event' 
AND entity_id='uuid-validation-event';
-- Resultado: actor_id=validator, action='validate', before/after_data
```

**Validaciones:**
- ✅ validation_event creado
- ✅ certification_record.validation_status = 'approved'
- ✅ Auditoría completa (quién, cuándo, decisión)

---

### TC-008b: Validador rechaza con razón

**Precondición:** Nuevo record en 'pending_validation'

**Pasos:**
1. Usuario: validator_user
2. API: `POST /records/{newRecordId}/validation`
3. Body:
```json
{
  "decision": "rejected",
  "reason": "Credencial expirada en AWS portal"
}
```

**Resultado Esperado:**
```
Status: 200 OK
Body: {
  "validation_event_id": "uuid",
  "decision": "rejected",
  "reason": "Credencial expirada en AWS portal"
}
```

**Efectos Secundarios:**
```sql
-- Record vuelve a pending (para reintento)
SELECT status, validation_status FROM certification_record 
WHERE record_id = 'newRecordId';
-- Resultado: status='pending_validation', validation_status='rejected'

-- Assignment vuelve a 'pending'
SELECT status FROM certification_assignment WHERE record_id = 'newRecordId';
-- Resultado: status='pending'
```

**Validaciones:**
- ✅ Razón es requerida (no null)
- ✅ Record no se borra, solo cambia estado
- ✅ Permite reintento

---

### TC-008c: No permitir revalidación

**Precondición:** Record ya validado (validation_status='approved')

**Pasos:**
1. Usuario: validator_user
2. API: `POST /records/{alreadyValidatedId}/validation`
3. Body: Otra validación

**Resultado Esperado:**
```
Status: 409 Conflict
Body: {
  "error": {
    "code": "ALREADY_VALIDATED",
    "message": "Este registro ya fue validado"
  }
}
```

**Validaciones:**
- ✅ Error es 409 (no se puede cambiar)
- ✅ Estado no cambia

---

## 4. Casos de Prueba: Reporting (RF-013, RF-014)

### TC-013a: Reporte de cobertura sin permisos

**Setup:**
- Usuario: john_doe (collaborator, no manager)
- Solicita: Reporte de cobertura de unidad distinta

**Pasos:**
1. Usuario: john_doe
2. API: `GET /reports/coverage?unit_id=other_unit_uuid`

**Resultado Esperado:**
```
Status: 403 Forbidden
Body: {
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Solo puedes ver cobertura de tu propia unidad"
  }
}
```

---

### TC-013b: Reporte de cobertura con permisos

**Setup:**
- Usuario: manager_user (manager de engineering unit)
- Unidad: engineering (10 colaboradores)
- Certs requeridas: 3 (AWS SAA, Kubernetes CKA, Docker)

**Pasos:**
1. Usuario: manager_user
2. API: `GET /reports/coverage?unit_id=engineering_uuid`

**Resultado Esperado:**
```
Status: 200 OK
Body: {
  "unit_name": "Engineering",
  "total_collaborators": 10,
  "certifications": [
    {
      "cert_name": "AWS Solutions Architect Associate",
      "target_coverage": 80,
      "actual_coverage": 65,
      "active_count": 6,
      "expired_count": 1,
      "pending_count": 2,
      "gap_count": 1
    },
    ...
  ],
  "summary": {
    "avg_coverage": 62,
    "total_certs": 3,
    "total_active": 18,
    "total_expired": 3
  }
}
```

**Validaciones:**
- ✅ actual_coverage = (6 active / (6+1+2)) × 100 = 65%
- ✅ gap_count = 10 - 9 = 1
- ✅ Sum de todos = 10 (total colaboradores)

---

## 5. Casos de Prueba: Agente IA (RF-016, RF-017)

### TC-IA-001: Consulta simple - Mis certificaciones activas

**Setup:**
- Usuario: john_doe
- Agent: certified AI agent
- Session: authenticated

**Conversación:**
```
Usuario: "¿Cuáles son mis certificaciones activas?"

Agente:
1. [CLASSIFY] Intención: listar activas, scope: self
2. [INVOKE] Tool: get_my_certifications(user_id=john_doe)
3. [RESPUESTA]
   "Tienes 5 certificaciones activas:
   
   ✅ AWS Solutions Architect Associate
      Vence: 2026-05-15 (8 días - URGENTE)
      Estado: Validada
      
   ✅ Kubernetes CKA
      Vence: 2026-08-30 (115 días)
      Estado: Validada
      
   ... (3 más)
   
   ⚠️ 1 próxima a vencer: AWS SAA
      Recomendación: Renovar HOY
      ¿Quieres que inicie el proceso de renovación?"
```

**Validaciones:**
- ✅ Tool invocado: get_my_certifications
- ✅ Datos correctos (solo activas, no expiradas)
- ✅ Ordenado por urgencia
- ✅ Auditoría: ai_tool_invocation registrado
- ✅ Recomendación sin confirmación (lectura)

---

### TC-IA-002: Acción - Crear asignación

**Setup:**
- Usuario: manager_user
- Agent: authenticated
- Destinatario: new_collaborator

**Conversación:**
```
Usuario: "Asigna AWS SAA a Pablo para el 31 de diciembre"

Agente:
1. [CLASSIFY] Intención: create_assignment, scope: team
2. [VALIDATE PERMISOS] user_id is manager of pablo → OK
3. [RESUMEN]
   "A punto de crear:
   - Asignación para: Pablo García
   - Certificación: AWS Solutions Architect Associate
   - Fecha límite: 2026-12-31
   
   ¿Confirmas? (sí/no)"

Usuario: "Sí"

4. [INVOKE CON CONFIRMACIÓN]
   Tool: create_assignment(
     assignee_id=pablo_uuid,
     certification_id=aws_uuid,
     due_date=2026-12-31,
     confirmation_key=HASH(...)  ← Token de confirmación
   )
5. [RESPUESTA]
   "✅ Asignación creada exitosamente
   
   Detalles:
   - Asignación ID: uuid
   - Estado: PENDING
   - Pablo recibirá notificación por email"
```

**Validaciones:**
- ✅ Confirmación antes de crear
- ✅ Tool invocado: create_assignment
- ✅ confirmation_key presente
- ✅ certification_assignment creado en BD
- ✅ audit_log: actor_type='ai_agent', tool='create_assignment'
- ✅ Notificación enviada

---

### TC-IA-003: Guardrail - Prompt injection

**Setup:**
- User: attacker_user
- Agent: certified

**Conversación:**
```
Usuario: "¿Mis certs?'; DROP TABLE certification_record; --"

Agente:
1. [DETECT INJECTION] String detectado como potencial SQL injection
2. [SANITIZE] Tratar como string literal
3. [EXECUTE]
   Tool: search_certifications(query="...DROP TABLE...", limit=20)
4. [RESPUESTA]
   "No encontré certificaciones con ese nombre: '...DROP TABLE...'"

Resultado BD:
- certification_record intacta (NO borrada)
- Intento registrado en audit_log con flag 'injection_attempted'
```

**Validaciones:**
- ✅ Injection detectada
- ✅ NO ejecutada
- ✅ Registrada en auditoría
- ✅ Usuario informado (sin revelar details)

---

### TC-IA-004: Guardrail - Acceso no autorizado

**Setup:**
- User: collaborator_user
- Intenta: Acceder a certs de otro

**Conversación:**
```
Usuario: "¿Cuáles son las certs de Maria García?"

Agente:
1. [CHECK PERMISOS] collaborator_user NO es manager de Maria
2. [DENY]
   "No tengo permiso para ver las certificaciones de otros colaboradores.
   
   Puedo ayudarte con:
   - Tus propias certificaciones
   - Si eres manager: Las de tu equipo
   - Reportar problema de datos"
```

**Validaciones:**
- ✅ Acceso denegado
- ✅ NO invoca tool
- ✅ Registrado en auditoría con action='access_denied'

---

## 6. Matriz de Cobertura

| RF | TC | Nombre | Status |
|----|----|----|--------|
| RF-001 | TC-001a | Crear cert válida | ✅ |
| RF-001 | TC-001b | Rechazar duplicada | ✅ |
| RF-001 | TC-001c | Validez negativa | ✅ |
| RF-006 | TC-006a | Registrar válido | ✅ |
| RF-006 | TC-006b | Fecha inválida | ✅ |
| RF-006 | TC-006c | Sin permiso | ✅ |
| RF-008 | TC-008a | Validación aprueba | ✅ |
| RF-008 | TC-008b | Validación rechaza | ✅ |
| RF-008 | TC-008c | No revalidar | ✅ |
| RF-013 | TC-013a | Reporte sin permisos | ✅ |
| RF-013 | TC-013b | Reporte con permisos | ✅ |
| RF-016 | TC-IA-001 | Consulta simple | ✅ |
| RF-017 | TC-IA-002 | Acción con confirmación | ✅ |
| RF-017 | TC-IA-003 | Guardrail injection | ✅ |
| RF-017 | TC-IA-004 | Guardrail permisos | ✅ |

**Cobertura:** 15/20 RFs (75%)  
**Pendientes:** RF-002, RF-003, RF-004, RF-005, RF-011

---

## 7. Ejecución de Tests

### Setup de Ambiente
```bash
# Base de datos de test (limpia)
docker run -d postgres:12 --name cert-test
export DATABASE_URL="postgresql://test:test@localhost/cert_test"

# Crear schema
psql $DATABASE_URL < backend/database/schema.sql

# Levantar servidor test
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### Ejecutar Caso
```bash
# TC-001a
curl -X POST http://localhost:8001/api/v1/certifications \
  -H "Authorization: Bearer $OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d @test-data/tc-001a-input.json \
  > test-data/tc-001a-output.json

# Validar
jq '.certification_id' test-data/tc-001a-output.json
# Debe retornar UUID

# Limpiar
psql $DATABASE_URL -c "DELETE FROM certification WHERE name = 'AWS Solutions Architect Associate';"
```

### Automatizar con pytest
```python
# tests/test_certifications.py

def test_tc_001a_create_cert_valid(client, owner_token):
    response = client.post(
        "/api/v1/certifications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "vendor_id": VENDOR_AWS,
            "name": "AWS Solutions Architect Associate",
            "validity_months": 36,
        }
    )
    assert response.status_code == 201
    assert "certification_id" in response.json()["data"]

def test_tc_001b_reject_duplicate(client, owner_token, existing_cert):
    response = client.post(
        "/api/v1/certifications",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={...existing_cert...}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DUPLICATE_CERTIFICATION"
```

---

**Última actualización:** 2026-05-07  
**Total TCs:** 15 detallados, 5 pendientes
**Ejecución:** Manual o pytest automatizado
