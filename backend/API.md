# Backend API Reference

Documentación completa de los endpoints REST de la Certification App API.

## Información General

- **Base URL:** `https://api.certification.nttdata.com/api/v1` (dev: `http://localhost:8080/api/v1`)
- **Autenticación:** JWT Bearer token en header `Authorization`
- **Formato de Respuesta:** JSON
- **Especificación OpenAPI:** `backend/api/openapi.yaml`

## Estándares de Respuesta

### Respuesta Exitosa (2xx)

```json
{
  "success": true,
  "data": {
    "record_id": "550e8400-e29b-41d4-a716-446655440000",
    "...": "..."
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2026-05-07T10:30:00Z",
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150
    }
  }
}
```

### Respuesta de Error (4xx, 5xx)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "El campo 'email' es inválido",
    "details": [
      {
        "field": "email",
        "message": "Debe ser un email válido",
        "code": "INVALID_EMAIL"
      }
    ]
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2026-05-07T10:30:00Z"
  }
}
```

## Headers Requeridos

```
Authorization: Bearer {jwt_token}
Content-Type: application/json
X-Correlation-ID: {uuid}  [Opcional, generado si falta]
```

## Códigos de Estado HTTP

| Código | Significado | Ejemplo |
|--------|-----------|---------|
| 200 | OK - Lectura exitosa | GET /certifications |
| 201 | Created - Recurso creado | POST /records |
| 204 | No Content - Eliminado | DELETE /assignments/{id} |
| 400 | Bad Request - Validación falló | Campo requerido ausente |
| 401 | Unauthorized - Token inválido | JWT expirado |
| 403 | Forbidden - Permisos insuficientes | Usuario sin rol |
| 404 | Not Found - Recurso no existe | GET /records/invalid-id |
| 409 | Conflict - Recurso duplicado | Email ya existe |
| 422 | Unprocessable Entity - Lógica falló | Estado no válido para acción |
| 429 | Too Many Requests - Rate limit | > 100 req/min |
| 500 | Internal Server Error | Error no controlado |
| 503 | Service Unavailable - DB caída | Reintento automático |

---

## Endpoints

### 1. CERTIFICATIONS - Catálogo

#### `GET /certifications`

Buscar certificaciones en el catálogo.

**Parámetros de Query:**
```
vendor_id?       uuid      - Filtrar por vendor
category?        string    - Categoría (ej: "Cloud", "Database")
name?            string    - Búsqueda por nombre (partial match)
is_active?       boolean   - Solo activas (default: true)
page?            integer   - Página (default: 1)
limit?           integer   - Resultados por página (default: 20, max: 100)
sort?            string    - Campo para ordenar (name, created_at)
order?           asc|desc  - Orden (default: asc)
```

**Request:**
```bash
GET /certifications?vendor_id=550e8400&category=Cloud&limit=50
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "certification_id": "550e8400-e29b-41d4-a716-446655440000",
      "vendor_id": "550e8400-e29b-41d4-a716-446655440010",
      "vendor_name": "Amazon",
      "name": "AWS Solutions Architect Associate",
      "code": "SAA-C03",
      "category": "Cloud",
      "level": "Associate",
      "validity_months": 36,
      "requires_evidence": true,
      "is_active": true
    },
    {
      "certification_id": "550e8400-e29b-41d4-a716-446655440001",
      "vendor_id": "550e8400-e29b-41d4-a716-446655440010",
      "vendor_name": "Amazon",
      "name": "AWS Solutions Architect Professional",
      "code": "SAP-C02",
      "category": "Cloud",
      "level": "Professional",
      "validity_months": 36,
      "requires_evidence": true,
      "is_active": true
    }
  ],
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440099",
    "timestamp": "2026-05-07T10:30:00Z",
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 250
    }
  }
}
```

**Errores:**
- `400` - Parámetros inválidos (ej: `limit` > 100)
- `401` - Token ausente o inválido
- `429` - Rate limit excedido

---

#### `POST /certifications`

Crear nueva certificación en el catálogo.

**Permisos Requeridos:** `certification:write` (Certification Owner)

**Request:**
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

**Response 201:**
```json
{
  "success": true,
  "data": {
    "certification_id": "550e8400-e29b-41d4-a716-446655440100",
    "vendor_id": "550e8400-e29b-41d4-a716-446655440010",
    "vendor_name": "Amazon",
    "name": "AWS Solutions Architect Associate",
    "code": "SAA-C03",
    "category": "Cloud",
    "level": "Associate",
    "validity_months": 36,
    "requires_evidence": true,
    "is_active": true,
    "created_at": "2026-05-07T10:30:00Z"
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440099",
    "timestamp": "2026-05-07T10:30:00Z"
  }
}
```

**Errores:**
- `400` - Validación falló (campos requeridos, tipos)
- `401` - No autenticado
- `403` - Sin permisos (no es Owner)
- `409` - Certificación duplicada (mismo vendor + nombre)

---

### 2. ASSIGNMENTS - Asignaciones

#### `POST /assignments`

Asignar una certificación a un colaborador.

**Permisos Requeridos:** `assignment:create` (Manager, Owner)

**Request:**
```json
{
  "assignee_id": "550e8400-e29b-41d4-a716-446655440200",
  "certification_id": "550e8400-e29b-41d4-a716-446655440100",
  "due_date": "2026-12-31",
  "priority": "high",
  "reason": "Requerimiento para Cloud team"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "assignment_id": "550e8400-e29b-41d4-a716-446655440300",
    "assignee_id": "550e8400-e29b-41d4-a716-446655440200",
    "assignee_name": "John Doe",
    "assignee_email": "john.doe@example.com",
    "certification_id": "550e8400-e29b-41d4-a716-446655440100",
    "certification_name": "AWS Solutions Architect Associate",
    "assigned_by": "550e8400-e29b-41d4-a716-446655440050",
    "assigned_by_name": "Jane Smith",
    "due_date": "2026-12-31",
    "priority": "high",
    "status": "pending",
    "created_at": "2026-05-07T10:30:00Z"
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440099",
    "timestamp": "2026-05-07T10:30:00Z"
  }
}
```

**Estados Válidos:**
- `pending`: Asignación creada, esperando evidencia
- `completed`: Certificación validada
- `rejected`: Evidencia rechazada
- `expired`: Pasó fecha de vencimiento
- `waivered`: Exenta por excepción

**Errores:**
- `400` - Validación falló
- `401` - No autenticado
- `403` - Sin permisos (no es Manager del assignee)
- `404` - Colaborador o certificación no existe
- `409` - Asignación duplicada (mismo assignee + cert)
- `422` - Lógica falló (ej: due_date en pasado)

---

### 3. RECORDS - Registros de Certificación

#### `POST /records`

Registrar una certificación obtenida (reportada por colaborador).

**Permisos Requeridos:** `record:create` (Colaborador, Manager, Admin)

**Request:**
```json
{
  "collaborator_id": "550e8400-e29b-41d4-a716-446655440200",
  "certification_id": "550e8400-e29b-41d4-a716-446655440100",
  "assignment_id": "550e8400-e29b-41d4-a716-446655440300",
  "issue_date": "2023-05-01",
  "expiration_date": "2026-05-01",
  "credential_id": "SAA-C03-2023-123456"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "record_id": "550e8400-e29b-41d4-a716-446655440400",
    "collaborator_id": "550e8400-e29b-41d4-a716-446655440200",
    "collaborator_name": "John Doe",
    "certification_id": "550e8400-e29b-41d4-a716-446655440100",
    "certification_name": "AWS Solutions Architect Associate",
    "assignment_id": "550e8400-e29b-41d4-a716-446655440300",
    "issue_date": "2023-05-01",
    "expiration_date": "2026-05-01",
    "status": "active",
    "validation_status": "pending",
    "days_to_expiration": 725,
    "evidence_required": true,
    "created_at": "2026-05-07T10:30:00Z"
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440099",
    "timestamp": "2026-05-07T10:30:00Z"
  }
}
```

**Estados de Record:**
- `active`: Certificación vigente
- `expired`: Pasó fecha de expiración
- `pending_validation`: Aguardando validación
- `rejected`: Rechazada por validador
- `waivered`: Exenta por excepción

**Validación Status:**
- `pending`: Aguardando validación
- `approved`: Validada por validador
- `rejected`: Rechazada
- `waivered`: Exenta

**Errores:**
- `400` - Validación falló (fecha inválida, etc)
- `401` - No autenticado
- `403` - Sin permisos (no es colaborador ni manager)
- `404` - Colaborador o certificación no existe
- `422` - Lógica falló (expiration_date < issue_date)

---

#### `GET /records/{recordId}`

Obtener detalles de un registro de certificación.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "record_id": "550e8400-e29b-41d4-a716-446655440400",
    "collaborator_id": "550e8400-e29b-41d4-a716-446655440200",
    "collaborator_name": "John Doe",
    "certification_id": "550e8400-e29b-41d4-a716-446655440100",
    "certification_name": "AWS Solutions Architect Associate",
    "issue_date": "2023-05-01",
    "expiration_date": "2026-05-01",
    "status": "active",
    "validation_status": "pending",
    "credential_id": "SAA-C03-2023-123456",
    "evidence": [
      {
        "evidence_id": "550e8400-e29b-41d4-a716-446655440500",
        "document_name": "certificate.pdf",
        "storage_uri": "s3://bucket/evidence/...",
        "uploaded_at": "2026-05-07T10:30:00Z",
        "classification": "proof_of_completion"
      }
    ],
    "validation_history": [
      {
        "validation_event_id": "550e8400-e29b-41d4-a716-446655440600",
        "validator_id": "550e8400-e29b-41d4-a716-446655440050",
        "validator_name": "Jane Smith",
        "decision": "pending",
        "reason": null,
        "decided_at": null
      }
    ],
    "created_at": "2026-05-07T10:30:00Z"
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440099",
    "timestamp": "2026-05-07T10:30:00Z"
  }
}
```

**Errores:**
- `401` - No autenticado
- `403` - Sin permisos (no es propietario, manager o validador)
- `404` - Registro no existe

---

### 4. VALIDATION - Validación de Evidencias

#### `POST /records/{recordId}/validation`

Enviar decisión de validación (aprobado/rechazado).

**Permisos Requeridos:** `validation:write` (Validator)

**Request:**
```json
{
  "decision": "approved",
  "reason": "Certificación verificada en registry oficial"
}
```

O rechazar:
```json
{
  "decision": "rejected",
  "reason": "Credencial expirada. Por favor, proporcione certificado válido."
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "validation_event_id": "550e8400-e29b-41d4-a716-446655440600",
    "record_id": "550e8400-e29b-41d4-a716-446655440400",
    "validator_id": "550e8400-e29b-41d4-a716-446655440050",
    "validator_name": "Jane Smith",
    "decision": "approved",
    "reason": "Certificación verificada en registry oficial",
    "decided_at": "2026-05-07T10:30:00Z"
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440099",
    "timestamp": "2026-05-07T10:30:00Z"
  }
}
```

**Decisiones Válidas:**
- `approved` - Certificación validada
- `rejected` - Certificación rechazada (requiere razón)

**Efectos:**
- `approved` → Record pasa a `validation_status: 'approved'`
- `rejected` → Record pasa a `validation_status: 'rejected'`, Assignment vuelve a `pending`

**Errores:**
- `400` - Validación falló (decision o reason ausentes)
- `401` - No autenticado
- `403` - Sin permisos (no es validador)
- `404` - Registro no existe
- `409` - Ya validado (no se puede revalidar)
- `422` - Record no en estado pendiente

---

### 5. REPORTING - Reportes

#### `GET /reports/coverage`

Obtener cobertura de certificaciones por unidad organizativa.

**Parámetros de Query:**
```
unit_id?         uuid      - Filtrar por unidad (default: todas)
include_expired? boolean   - Incluir expiradas (default: false)
as_of?           date      - Fecha de corte (default: hoy)
```

**Request:**
```bash
GET /reports/coverage?unit_id=550e8400&include_expired=false&as_of=2026-05-07
Authorization: Bearer {token}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "as_of": "2026-05-07",
    "units": [
      {
        "unit_id": "550e8400-e29b-41d4-a716-446655440700",
        "unit_name": "Cloud Services",
        "parent_unit": "Technology",
        "total_collaborators": 45,
        "certifications": [
          {
            "certification_id": "550e8400-e29b-41d4-a716-446655440100",
            "certification_name": "AWS Solutions Architect Associate",
            "target_coverage": 80,
            "actual_coverage": 65,
            "active_count": 29,
            "expired_count": 2,
            "pending_count": 9,
            "gap_count": 5
          },
          {
            "certification_id": "550e8400-e29b-41d4-a716-446655440101",
            "certification_name": "AWS Solutions Architect Professional",
            "target_coverage": 40,
            "actual_coverage": 35,
            "active_count": 16,
            "expired_count": 1,
            "pending_count": 2,
            "gap_count": 26
          }
        ],
        "summary": {
          "total_certifications": 2,
          "avg_coverage": 50,
          "total_active": 45,
          "total_expired": 3,
          "total_pending": 11
        }
      }
    ]
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440099",
    "timestamp": "2026-05-07T10:30:00Z"
  }
}
```

**Errores:**
- `400` - Parámetros inválidos
- `401` - No autenticado
- `403` - Sin permisos (Auditor, Manager solo de su unidad)

---

### 6. AI TOOLS - Herramientas para Agente

#### `POST /ai/tools/list-due-renewals`

[Solo invocable por agente IA autorizado]

Listar certificaciones próximas a renovar (< 90 días para vencer).

**Request:**
```json
{
  "collaborator_id": "550e8400-e29b-41d4-a716-446655440200",
  "days_threshold": 90
}
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "collaborator_id": "550e8400-e29b-41d4-a716-446655440200",
    "collaborator_name": "John Doe",
    "email": "john.doe@example.com",
    "renewals": [
      {
        "record_id": "550e8400-e29b-41d4-a716-446655440400",
        "certification_name": "AWS Solutions Architect Associate",
        "vendor_name": "Amazon",
        "expiration_date": "2026-07-15",
        "days_remaining": 69,
        "issued_date": "2023-07-15",
        "credential_id": "SAA-C03-2023-123456",
        "priority": "high"
      }
    ]
  },
  "meta": {
    "correlation_id": "550e8400-e29b-41d4-a716-446655440099",
    "timestamp": "2026-05-07T10:30:00Z"
  }
}
```

**Notas:**
- Esto es un "tool" para el agente IA, ejecutado bajo permisos específicos
- El agente usa esto para iniciar conversaciones sobre renovaciones
- Requiere autenticación especial del agente (no JWT de usuario)

---

## Flujos Comunes

### Flujo 1: Asignar y Registrar Certificación

```
1. Crear asignación
   POST /assignments
   → {assignment_id, status: "pending"}

2. Colaborador registra certificación
   POST /records
   → {record_id, validation_status: "pending"}

3. Validador aprueba
   POST /records/{recordId}/validation
   → {decision: "approved"}
   
4. Record pasa a approved, assignment se completa
```

### Flujo 2: Renovación

```
1. Certificación próxima a vencer (< 90 días)
2. Agente notifica a colaborador
3. Colaborador carga nueva evidencia
   POST /records (con nueva issue_date, expiration_date)
4. Validador aprueba nueva certificación
5. Record anterior se mantiene como histórico (expired)
```

### Flujo 3: Reportaje de Cobertura

```
1. Manager solicita reporte de cobertura
   GET /reports/coverage?unit_id={id}
2. API calcula por certificación:
   - Total asignados
   - Validados/activos
   - Pendientes
   - Vencidos
   - Brechas
3. Retorna vista agregada para dashboard
```

---

## Rate Limiting

- **Límite:** 100 requests por minuto por usuario
- **Header de respuesta:** `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **Exceso:** Retorna 429 Too Many Requests
- **Backoff recomendado:** Esperar hasta `X-RateLimit-Reset`

---

## Paginación

Para endpoints que retornan listas:

```
?page=1&limit=20
```

Retorna:
```json
"meta": {
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## Errores Comunes y Soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| 401 Unauthorized | Token ausente/expirado | Reauthenticate y obtén nuevo token |
| 403 Forbidden | Permisos insuficientes | Verifica rol/permisos del usuario |
| 404 Not Found | Recurso no existe | Verifica ID, puede haber sido eliminado |
| 409 Conflict | Duplicado (email, cert+vendor) | Usa PUT para actualizar, no POST para crear |
| 422 Unprocessable | Lógica falló (estado inválido) | Verifica precondiciones (fechas, estado anterior) |
| 429 Too Many Requests | Rate limit | Espera y reintenta con backoff exponencial |
| 503 Service Unavailable | DB/servicio caído | Reintento automático después de 30s |

---

## Testing con curl

```bash
# Obtener token (simulado)
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Buscar certificaciones
curl -X GET "http://localhost:8080/api/v1/certifications?category=Cloud" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Crear certificación
curl -X POST "http://localhost:8080/api/v1/certifications" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": "550e8400-e29b-41d4-a716-446655440010",
    "name": "New Cert",
    "category": "Cloud",
    "validity_months": 36
  }'

# Registrar certificación
curl -X POST "http://localhost:8080/api/v1/records" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "collaborator_id": "550e8400-e29b-41d4-a716-446655440200",
    "certification_id": "550e8400-e29b-41d4-a716-446655440100",
    "issue_date": "2023-05-01",
    "expiration_date": "2026-05-01"
  }'

# Validar
curl -X POST "http://localhost:8080/api/v1/records/550e8400-e29b-41d4-a716-446655440400/validation" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approved",
    "reason": "Verified in official registry"
  }'
```

---

## Referencias

- `backend/api/openapi.yaml` - Especificación OpenAPI completa
- `backend/ARCHITECTURE.md` - Detalles arquitectónicos
- `docs/04-procesos/` - Procesos de negocio
- `models/schemas/` - Esquemas JSON
