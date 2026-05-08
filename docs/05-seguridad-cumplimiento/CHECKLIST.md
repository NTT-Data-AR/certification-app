# Checklist de Seguridad y Cumplimiento

Checklist ejecutable para validar que proyecto cumple con controles de seguridad antes de producción.

**Propósito:** Validación objetiva, sin ambigüedades. ✅ = Cumple, ❌ = No cumple, ⚠️ = Parcial

---

## 1. Autenticación y Autorización

### 1.1 Autenticación: SSO/MFA

- [ ] ✅ SSO configurado (OAuth/OIDC)
  - [ ] Provider: Azure AD / Okta / Google
  - [ ] Endpoint: `/auth/login` redirige a SSO
  - [ ] Token: JWT con claims (user_id, roles, permissions)

- [ ] ✅ MFA activado para roles críticos (owner, validator, admin)
  - [ ] Opción 1: Authenticator app (TOTP)
  - [ ] Opción 2: Email/SMS (OTP)
  - [ ] Enforcement: MFA es obligatorio después de X logins

- [ ] ✅ Session timeout
  - [ ] JWT expiry: 1 hora máximo
  - [ ] Refresh token: 30 días máximo
  - [ ] Logout: Session invalidada en servidor

**Validación:**
```bash
# 1. Login y obtener token
TOKEN=$(curl -X POST https://idp.example.com/token \
  -d "user=test@nttdata.com&password=...")

# 2. Verificar claims
jq '.claims' <<< $(echo $TOKEN | cut -d. -f2 | base64 -d)
# Debe contener: user_id, roles[], permissions[]

# 3. Usar token en API
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/api/v1/records
# 200 OK

# 4. Esperar expiración (1 hora)
sleep 3600
# Reintento → 401 Unauthorized
```

---

### 1.2 Autorización: RBAC

- [ ] ✅ 5 Roles definidos y documentados
  - [ ] collaborator (certificaciones propias)
  - [ ] manager (equipo + asignaciones)
  - [ ] validator (aprobar/rechazar)
  - [ ] owner (catálogo + reglas)
  - [ ] auditor (lectura auditoria)

- [ ] ✅ Permisos por rol (ver docs/05-seguridad-cumplimiento/roles-permisos.md)

- [ ] ✅ Object-level authorization
  - [ ] Manager solo ve su unidad
  - [ ] Colaborador solo ve sus certs
  - [ ] Auditor puede ver todo (read-only)

**Validación:**
```bash
# 1. Login como manager_user
TOKEN_MANAGER=$(get_token manager_user)

# 2. Intentar acceder a otra unidad
curl -H "Authorization: Bearer $TOKEN_MANAGER" \
  'https://api.example.com/api/v1/reports/coverage?unit_id=OTHER_UNIT'
# 403 Forbidden (esperado)

# 3. Acceder a propia unidad
curl -H "Authorization: Bearer $TOKEN_MANAGER" \
  'https://api.example.com/api/v1/reports/coverage?unit_id=OWN_UNIT'
# 200 OK (esperado)
```

---

## 2. Validación de Entrada

### 2.1 Schema Validation

- [ ] ✅ OpenAPI schema en `backend/api/openapi.yaml`

- [ ] ✅ Validación en todos los endpoints POST/PUT
  - [ ] Tipos: string, integer, uuid, date, email
  - [ ] Longitud: maxLength, minLength
  - [ ] Formato: email, uuid, date (YYYY-MM-DD)
  - [ ] Requeridos: required arrays
  - [ ] Enum: campos cerrados (status, priority)

**Validación:**
```bash
# POST /records con date inválida
curl -X POST https://api.example.com/api/v1/records \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "collaborator_id": "uuid",
    "certification_id": "uuid",
    "issue_date": "invalid-date",  # ❌
    "expiration_date": "2026-05-15"
  }'
# 400 Bad Request o 422 Unprocessable Entity (esperado)
```

### 2.2 SQL Injection Prevention

- [ ] ✅ Prepared statements / Parameterized queries
  - [ ] NO string concatenation en SQL
  - [ ] Usar placeholders: `?` o `:name`

**Validación:**
```python
# ❌ MAL (vulnerable)
query = f"SELECT * FROM users WHERE email = '{user_email}'"
db.execute(query)

# ✅ BIEN (safe)
query = "SELECT * FROM users WHERE email = ?"
db.execute(query, [user_email])
```

### 2.3 XSS Prevention

- [ ] ✅ Output encoding en HTML/JSON
  - [ ] HTML: escape <, >, &, ", '
  - [ ] JSON: válido JSON (no inyectar )

### 2.4 CSRF Protection

- [ ] ✅ CSRF tokens en forms (si aplica)
  - [ ] Token generado por servidor
  - [ ] Validado en POST/PUT/DELETE
  - [ ] Unique per session

---

## 3. Datos: Cifrado y Privacidad

### 3.1 Cifrado en Tránsito

- [ ] ✅ HTTPS/TLS 1.2+ obligatorio
  - [ ] Certificate válido (no self-signed)
  - [ ] HSTS header: `Strict-Transport-Security: max-age=31536000`

**Validación:**
```bash
curl -I https://api.example.com/api/v1/health
# HTTP/2 ✅
# Header: strict-transport-security ✅
# Certificado válido (no warning) ✅
```

### 3.2 Cifrado en Reposo

- [ ] ✅ Evidencias en storage seguro (S3 con encryption)
  - [ ] Server-Side Encryption (SSE-S3 o KMS)
  - [ ] Bucket policy: NO public access

- [ ] ✅ PII en BD cifrada (si aplica)
  - [ ] Opciones: pgcrypto PostgreSQL, application-level encryption
  - [ ] Keys: almacenadas en secrets manager (AWS Secrets, HashiCorp Vault)

**Validación:**
```bash
# Verificar S3 encryption
aws s3api head-bucket --bucket cert-app-evidences
# → ServerSideEncryption: AES256 ✅

# Verificar secrets manager
aws secretsmanager list-secrets | grep encryption_key
# ✅ Key existe, rotación automática
```

### 3.3 PII Minimization

- [ ] ✅ API responses NO incluyen:
  - [ ] email (sustituir por "John D.")
  - [ ] employee_number
  - [ ] credential_id (hash o ID solo)
  - [ ] salary, SSN, etc

**Validación:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/api/v1/records | jq '.data[0]'
# Esperado:
# {
#   "record_id": "uuid",
#   "collaborator_name": "John D.",  # NO email
#   "certification_name": "AWS SAA",
#   ...
# }
# ✅ PII no visible
```

---

## 4. Auditoria

### 4.1 Audit Log Completo

- [ ] ✅ audit_log captura todas las mutaciones
  - [ ] Tabla: audit_log (append-only)
  - [ ] Campos: correlation_id, actor_id, action, entity_type, entity_id, before_data, after_data, occurred_at

- [ ] ✅ No se permite DELETE en audit_log
  - [ ] Constraint: NOT DELETABLE
  - [ ] DDL protected (only admin can create index, not drop)

**Validación:**
```sql
-- 1. Crear certificación
INSERT INTO certification (...) RETURNING certification_id;
-- cert_id = '123'

-- 2. Verificar audit_log
SELECT * FROM audit_log WHERE entity_id = '123';
-- ✅ Debe existir entrada con:
--    action='create'
--    actor_id='owner@nttdata.com'
--    before_data=null
--    after_data={...}

-- 3. Intentar eliminar (debe fallar)
DELETE FROM audit_log WHERE audit_id = 'xxx';
-- ❌ ERROR: Cannot delete from audit_log
```

### 4.2 Correlation ID

- [ ] ✅ Cada request tiene correlation_id único
  - [ ] Header: `X-Correlation-ID: uuid`
  - [ ] Incluido en audit_log
  - [ ] Permite rastrear request → logs → auditoría

**Validación:**
```bash
# Request HTTP
curl -H "X-Correlation-ID: abc-123" \
  https://api.example.com/api/v1/records

# Verificar que se registró
psql $DB -c "SELECT correlation_id FROM audit_log ORDER BY occurred_at DESC LIMIT 1;"
# ✅ abc-123
```

---

## 5. Autenticación del Agente IA

### 5.1 Tool Allowlist

- [ ] ✅ Agente SOLO puede invocar tools listadas
  - [ ] 13 tools definidas en docs/06-agent-ai/herramientas.md
  - [ ] Validación en backend: whitelist de tool names

**Validación:**
```python
# Agente intenta invocar tool inexistente
agente.call_tool("delete_all_records")

# Backend:
if tool_name not in ALLOWED_TOOLS:
    raise ToolNotAllowedError(f"{tool_name} no está en allowlist")
# ✅ Rechazado

# Agente invoca tool válida
agente.call_tool("list_due_renewals")
# ✅ Permitido
```

### 5.2 Tool Confirmation

- [ ] ✅ Tools de escritura requieren confirmación humana
  - [ ] Tool retorna status='pending_human_approval'
  - [ ] User recibe notificación ("Agente solicita tu confirmación")
  - [ ] Human aprueba/rechaza
  - [ ] Tool se completa/rechaza basado en human decision

---

## 6. Rate Limiting

### 6.1 Por Usuario

- [ ] ✅ Límite: 100 requests/min por usuario
  - [ ] Implementación: Redis o in-memory cache
  - [ ] Headers respuesta: X-RateLimit-Remaining, X-RateLimit-Reset

**Validación:**
```bash
TOKEN=$(get_token user)

# 101 requests en 60 segundos
for i in {1..101}; do
  curl -H "Authorization: Bearer $TOKEN" https://api.example.com/api/v1/health
done

# Request #101:
# ❌ 429 Too Many Requests
# Header: X-RateLimit-Remaining: 0
# Header: X-RateLimit-Reset: 2026-05-07T14:31:00Z
```

### 6.2 Por Tool del Agente

- [ ] ✅ Límite: 1000 tool invocations/hora por agente
  - [ ] Métrica: ai_tool_invocation table
  - [ ] Validación: antes de invocar tool

---

## 7. Seguridad del Backend

### 7.1 Dependencias

- [ ] ✅ No hay vulnerabilidades conocidas
  - [ ] Tool: `npm audit` (JavaScript) o `pip audit` (Python)
  - [ ] Frecuencia: antes de cada release
  - [ ] Remediar: update o replace

**Validación:**
```bash
# Python
pip install safety
safety check

# JavaScript
npm audit
# Output: 0 vulnerabilities (esperado)
```

### 7.2 Secrets Management

- [ ] ✅ No hay secrets en código
  - [ ] .gitignore: .env, .env.local, secrets/
  - [ ] CI/CD: secrets en vault (AWS Secrets, HashiCorp Vault)
  - [ ] Aplicación: cargar desde variables de ambiente

**Validación:**
```bash
# Buscar secretos en repo
git log --all --oneline --grep='secret|password|key' | wc -l
# 0 (esperado)

grep -r "password\|secret\|api_key" --exclude-dir=.git src/
# No matches (esperado)
```

### 7.3 CORS

- [ ] ✅ CORS permitido solo para dominios de confianza
  - [ ] Header: `Access-Control-Allow-Origin: https://app.example.com`
  - [ ] NO: `Access-Control-Allow-Origin: *`

---

## 8. Cumplimiento Normativo

### 8.1 GDPR (si aplica en EU)

- [ ] ✅ Right to Erasure (derecho al olvido)
  - [ ] Método: soft delete (status='deleted')
  - [ ] Datos perm eliminados después de N días (ej: 7 años archivos)

- [ ] ✅ Data Minimization
  - [ ] Recopilar solo datos necesarios
  - [ ] API: no expone email, SSN, etc (ver 3.3)

- [ ] ✅ Consent management
  - [ ] Usuario consiente procesamiento de datos
  - [ ] Log de consentimiento (fecha, qué consintió)

### 8.2 Auditoría Interna

- [ ] ✅ Audit trail completo (8 años retención)
  - [ ] Tabla: audit_log
  - [ ] Política: No borrar, solo archivar después de 8 años

- [ ] ✅ Access logs (quién, cuándo, qué)
  - [ ] Log de todos los accesos (API, admin, operaciones)
  - [ ] Retention: 90 días online, 1 año archive

---

## 9. Checklist de Release

Antes de deploying a producción:

### Pre-Release

- [ ] ✅ Todos los tests pasan (`pytest -v`)
- [ ] ✅ Seguridad audit completado (este checklist)
- [ ] ✅ Code review aprobado por 2+ devs
- [ ] ✅ Performance testing: latencia < 2s (p95)
- [ ] ✅ Load testing: 100 users simultáneos, SLA met
- [ ] ✅ Backups configurados y testeados
- [ ] ✅ Disaster recovery plan en lugar
- [ ] ✅ Monitoring/alertas configuradas
- [ ] ✅ Runbook de incidentes completado

### Post-Release

- [ ] ✅ Canary deployment: 5% tráfico
- [ ] ✅ Monitoreo por 24h sin issues
- [ ] ✅ Gradual rollout: 25% → 50% → 100%
- [ ] ✅ Rollback plan listo (en 5 minutos máximo)

---

## 10. Auditoría Periódica

| Frecuencia | Qué Auditar | Responsable |
|-----------|-----------|-----------|
| Diaria | Alertas de seguridad, excepciones | DevOps |
| Semanal | Logs de acceso anormal, rate limits | Security |
| Mensual | Vulnerabilidades (dependencies), cambios RBAC | Security + Dev Lead |
| Trimestral | Acceso de usuarios (roles vigentes), datos sensibles | Compliance |
| Anual | Seguridad integral (penetration test), cumplimiento normativo | External Auditor |

---

## 11. Resumen: ¿Listo para Producción?

| Sección | Cumple | Crítico |
|---------|--------|---------|
| Auth & Authz | ? | ✅ |
| Validación | ? | ✅ |
| Cifrado | ? | ✅ |
| Auditoria | ? | ✅ |
| Agente IA | ? | ✅ |
| Rate Limiting | ? | ⚠️ |
| Cumplimiento | ? | ⚠️ |

**Criterio de aprobación:** Todos los ✅ deben ser checked, al menos 80% de ⚠️.

---

**Última actualización:** 2026-05-07  
**Próxima auditoría:** 2026-06-07 (mensual)
**Responsable:** CISO + Security Team
