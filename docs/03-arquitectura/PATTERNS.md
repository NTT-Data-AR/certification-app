# Patrones de Arquitectura

Patrones reutilizables y decisiones de diseño para backend, datos y agente IA.

---

## 1. Transacciones y Consistencia

### 1.1 Patrón: Unit of Work (para operaciones atómicas)

**Cuándo usar:** Cambios múltiples que deben ser todo-o-nada.

**Ejemplo: Aprobar Certificación**
```python
def validate_certification(record_id, validator_id, decision):
    """
    Transacción atómica: validar + cambiar estado + auditar
    """
    transaction = db.begin_transaction()
    try:
        # 1. Validar precondiciones
        record = db.query("SELECT * FROM certification_record WHERE id=?", record_id)
        if record.validation_status != 'pending':
            raise ValidationError("Ya validada")
        
        # 2. Crear evento de validación
        event_id = db.insert("validation_event", {
            'record_id': record_id,
            'validator_id': validator_id,
            'decision': decision,
            'decided_at': now()
        }, transaction)
        
        # 3. Actualizar estado del record
        db.update("certification_record", record_id, {
            'validation_status': decision,
            'updated_at': now()
        }, transaction)
        
        # 4. Auditar TODAS las operaciones
        db.insert("audit_log", {
            'correlation_id': request_id,
            'actor_id': validator_id,
            'action': 'validate',
            'entity_type': 'validation_event',
            'entity_id': event_id,
            'before_data': record.to_json(),
            'after_data': {**record.to_json(), 'validation_status': decision}
        }, transaction)
        
        # 5. Commit atomically
        transaction.commit()
        return event_id
        
    except Exception as e:
        transaction.rollback()  # TODO si falla, nada de lo anterior sucedió
        raise
```

**Garantía:** Si hay error en paso 3, paso 4 no ejecuta. Todo se revierte.

### 1.2 Patrón: Optimistic Locking (evitar race conditions)

**Cuándo usar:** Múltiples usuarios podrían editar lo mismo simultáneamente.

**Ejemplo: Cambiar Status de Assignment**
```sql
-- Sin optimistic locking (MAL): 
UPDATE certification_assignment 
SET status = 'completed' 
WHERE assignment_id = '123';
-- ¿Y si otro proceso también actualizó? Conflicto silencioso.

-- CON optimistic locking (BIEN):
UPDATE certification_assignment 
SET status = 'completed', 
    version = version + 1,
    updated_at = now()
WHERE assignment_id = '123' 
  AND version = 5;  -- La versión que vimos

-- Si otro proceso cambió la fila, version != 5, UPDATE devuelve 0 filas
-- Cliente: "Hubo conflicto, recarga y reintentar"
```

**Implementación:**
```python
def update_assignment_status(assignment_id, new_status, expected_version):
    result = db.execute("""
        UPDATE certification_assignment 
        SET status = ?, version = version + 1, updated_at = now()
        WHERE assignment_id = ? AND version = ?
    """, [new_status, assignment_id, expected_version])
    
    if result.rows_affected == 0:
        raise ConflictError("Conflicto: la asignación cambió. Recarga e intenta de nuevo.")
    return result
```

### 1.3 Patrón: Snapshot Isolation

**Cuándo usar:** Reportes que deben ver estado consistente, aunque tome tiempo.

**Ejemplo: Generar Reporte de Cobertura**
```python
def generate_coverage_report_at_date(target_date):
    """
    Ver estado de certificaciones COMO SI fuera target_date
    """
    with db.transaction(isolation_level='SERIALIZABLE'):
        # Todos los SELECTs ven snapshot de target_date
        report = db.query("""
            SELECT 
                bu.name,
                cert.name,
                COUNT(*) total,
                COUNT(CASE WHEN cr.status='active' THEN 1 END) active,
                COUNT(CASE WHEN cr.status='expired' THEN 1 END) expired
            FROM business_unit bu
            LEFT JOIN collaborator c ON ...
            LEFT JOIN certification_record cr 
                ON ... AND cr.created_at <= ? 
            GROUP BY bu.name, cert.name
        """, [target_date])
        
        return report
```

---

## 2. Patrón: Idempotencia

### 2.1 Por qué es crítico

Si red falla a mitad de request:
```
Usuario clica "Asignar certificación"
→ Backend: POST /assignments
  ├─ Crea assignment en BD
  ├─ Envía email
  ├─ [CONEXIÓN CAE]
  └─ Cliente nunca recibe respuesta

Usuario reintentar (manual o automático)
→ Backend: POST /assignments
  ├─ Intenta crear assignment DE NUEVO
  ├─ RESULTADO: Duplicado (ERROR)
  └─ Cliente vuelve a enviar email (SPAM)
```

### 2.2 Solución: Idempotency Keys

```python
@app.post("/assignments")
def create_assignment(request: AssignmentRequest):
    # Cliente GENERA idempotency_key y NO CAMBIA entre reintentos
    idempotency_key = request.idempotency_key  # ej: uuid
    
    # Verificar si ya procesamos esta key
    existing = db.query(
        "SELECT * FROM assignment_idempotency WHERE key = ?",
        idempotency_key
    )
    
    if existing:
        # Ya lo procesamos: retornar resultado anterior (sin duplicar)
        return existing.result
    
    # Primera vez: procesar normalmente
    try:
        assignment = db.insert("certification_assignment", {
            'assignee_id': request.assignee_id,
            'certification_id': request.certification_id,
            'idempotency_key': idempotency_key,
            ...
        })
        
        result = {'assignment_id': assignment.id, 'status': 'pending'}
        
        # Guardar que procesamos esta key exitosamente
        db.insert("assignment_idempotency", {
            'key': idempotency_key,
            'result': json.dumps(result),
            'processed_at': now()
        })
        
        return result
        
    except Exception as e:
        # Fallo: NO guardar idempotency (próximo reintento lo intenta de nuevo)
        raise
```

**Resultado:**
```
Intento 1: POST /assignments (idempotency_key=uuid-1)
  → Crear + OK → Guardar resultado en assignment_idempotency

Intento 2 (reintento): POST /assignments (idempotency_key=uuid-1)
  → Buscar en assignment_idempotency → Encontrado
  → Retornar resultado anterior (NO crear duplicado)

✓ Sin duplicados, sin emails spam
```

---

## 3. Patrón: Event Sourcing para Auditoria

### 3.1 Qué es

En lugar de almacenar "estado actual", almacenar "secuencia de cambios".

### 3.2 Ejemplo: Validación de Certificación

**Tradicional (MAL):**
```
Tabla certification_record:
  status = 'active'
  validation_status = 'approved'
  
¿Cuándo se aprobó? ¿Quién aprobó? PERDIDO (no está en la tabla)
```

**Event Sourcing (BIEN):**
```
Tabla audit_log (append-only):
  1. action='create', entity_type='certification_record', 
     after_data={...}, occurred_at='2026-05-01T10:00'
  
  2. action='update', entity_type='certification_record',
     before_data={validation_status='pending'},
     after_data={validation_status='approved'},
     actor_id='validator@nttdata.com',
     occurred_at='2026-05-07T14:30'
  
  3. action='update', entity_type='certification_record',
     before_data={status='pending_validation'},
     after_data={status='active'},
     actor_id='system',
     occurred_at='2026-05-07T14:31'

¿Cuándo se aprobó? 2026-05-07T14:30 (evento #2)
¿Quién aprobó? validator@nttdata.com
¿Por qué cambió status? Ver evento #3
```

### 3.3 Reconstruir Estado en Cualquier Momento

```python
def get_certification_record_at_date(record_id, as_of_date):
    """
    Reconstruir estado del registro como si fuera as_of_date
    """
    # Obtener estado inicial (creación)
    events = db.query("""
        SELECT * FROM audit_log
        WHERE entity_type = 'certification_record'
          AND entity_id = ?
          AND occurred_at <= ?
        ORDER BY occurred_at ASC
    """, [record_id, as_of_date])
    
    # Aplicar cambios secuencialmente
    state = None
    for event in events:
        if event.action == 'create':
            state = event.after_data
        elif event.action == 'update':
            state.update(event.after_data)
    
    return state
```

---

## 4. Patrón: Soft Delete (Borrado Lógico)

### 4.1 Por qué no DELETE física

```sql
-- MAL: DELETE física
DELETE FROM certification_record WHERE record_id = '123';
-- ¿Quién borró? Cuándo? Por qué? (NO ESTÁ EN AUDITORIA)

-- BIEN: Soft delete (marcar estado)
UPDATE certification_record 
SET status = 'deleted', updated_at = now()
WHERE record_id = '123';

-- El audit_log automáticamente captura:
--   before_data = {status='active', ...}
--   after_data = {status='deleted', ...}
```

### 4.2 Búsquedas Excluyen Borrados

```python
def get_active_records(collaborator_id):
    """
    Por defecto, NO incluir borrados
    """
    return db.query("""
        SELECT * FROM certification_record
        WHERE collaborator_id = ?
          AND status != 'deleted'
        ORDER BY created_at DESC
    """, [collaborator_id])

def get_all_records_including_deleted(collaborator_id):
    """
    Solo si necesitas histórico completo (admin, auditor)
    """
    return db.query("""
        SELECT * FROM certification_record
        WHERE collaborator_id = ?
        ORDER BY created_at DESC
    """, [collaborator_id])
```

---

## 5. Patrón: Rate Limiting

### 5.1 Por Usuario

```python
from redis import Redis

redis = Redis()

def check_rate_limit(user_id, limit_per_minute=100):
    key = f"ratelimit:{user_id}:{datetime.now().strftime('%H:%M')}"
    
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, 60)  # Expirar en 60 segundos
    
    if count > limit_per_minute:
        raise RateLimitError(f"Límite {limit_per_minute} reqs/min excedido")
    
    return count

# En cada endpoint
@app.post("/assignments")
def create_assignment(request: Request):
    user_id = validate_jwt(request)
    check_rate_limit(user_id)  # Lanzar excepción si excede
    # ... resto de lógica
```

### 5.2 Por Herramienta del Agente

```python
def check_agent_tool_rate_limit(user_id, tool_name, limit_per_hour=1000):
    key = f"agent-tools:{user_id}:{tool_name}:{datetime.now().strftime('%H')}"
    
    count = redis.incr(key)
    if count == 1:
        redis.expire(key, 3600)  # Expirar en 1 hora
    
    if count > limit_per_hour:
        raise RateLimitError(f"Agente: límite {limit_per_hour} {tool_name}/h")
```

---

## 6. Patrón: Circuit Breaker (Fallos de Dependencias)

### 6.1 Problema

```
Backend llama a HR API
→ HR está lenta (10s timeout)
→ Todas las requests se bloquean esperando HR
→ Cascada de fallos
```

### 6.2 Solución: Circuit Breaker

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
def call_hr_api_sync_collaborators():
    """
    Si 5 fallos en 60s → circuit abre
    → Futuros calls fallan RÁPIDO (no esperan)
    → Pasado 60s → intenta recuperar (circuit cierra)
    """
    return requests.get('https://hr-api.internal/collaborators')

# En job de sincronización
def sync_collaborators_job():
    try:
        result = call_hr_api_sync_collaborators()
        # Procesar resultado
    except CircuitBreakerOpenError:
        logger.error("HR API no disponible (circuit abierto)")
        # Usar datos en caché
        return {"cached_at": datetime.now()}
    except Exception as e:
        logger.error(f"Error sync HR: {e}")
        # Reintentar más tarde (queue)
```

---

## 7. Patrón: CQRS (Command Query Responsibility Segregation)

### 7.1 Para Operaciones de Escritura (Command)

```python
def create_certification_command(params):
    """
    Writes: validar, persistir, auditar
    Responsable SOLO de cambiar estado
    """
    # 1. Validar
    if not params['vendor_id']:
        raise ValidationError("vendor_id required")
    
    # 2. Persistir
    cert_id = db.insert("certification", {
        'vendor_id': params['vendor_id'],
        'name': params['name'],
        ...
    })
    
    # 3. Auditar
    db.insert("audit_log", {...})
    
    return {'certification_id': cert_id}
```

### 7.2 Para Operaciones de Lectura (Query)

```python
def get_certificates_by_vendor_query(vendor_id):
    """
    Reads: optimizado para lectura (denormalización, caché)
    Responsable SOLO de retornar datos
    """
    # Usar vista denormalizada (no join costoso)
    certs = cache.get(f"certs:{vendor_id}")
    if not certs:
        certs = db.query("""
            SELECT * FROM v_certifications_by_vendor 
            WHERE vendor_id = ?
        """, [vendor_id])
        cache.set(f"certs:{vendor_id}", certs, ttl=3600)
    
    return certs
```

---

## 8. Patrón: Bulkhead (Isolación de Fallos)

### 8.1 Problema

```
Request pool (20 threads):
├─ 5 requests a BD (rápidos, 10ms)
├─ 10 requests a Email (lentos, 5s)
└─ 5 requests a HR (lentos, 10s)

Email y HR lentos AGOTAN el pool
→ Requests a BD esperan (timeouts)
→ Cascada de fallos
```

### 8.2 Solución: Thread Pools Separados

```python
from concurrent.futures import ThreadPoolExecutor

db_executor = ThreadPoolExecutor(max_workers=15, queue_size=50)
email_executor = ThreadPoolExecutor(max_workers=5, queue_size=100)
external_executor = ThreadPoolExecutor(max_workers=5, queue_size=50)

@app.post("/records")
def create_record(request):
    # BD: ejecutar inmediatamente (pool dedicado)
    record = db_executor.submit(db.insert, "certification_record", {...})
    
    # Email: en background (pool pequeño, no interfiere BD)
    email_executor.submit(send_email, user_email, ...)
    
    # HR: en background (pool pequeño)
    external_executor.submit(call_hr_api, ...)
    
    return {'record_id': record.result()}
```

---

## 9. Resumen de Patrones

| Patrón | Cuándo Usar | Beneficio |
|--------|-----------|----------|
| Unit of Work | Cambios múltiples | Atomicidad (todo-o-nada) |
| Optimistic Locking | Edición concurrente | Evitar race conditions |
| Snapshot Isolation | Reportes consistentes | Ver estado coherente |
| Idempotency Keys | Reintentos | Sin duplicados |
| Event Sourcing | Auditoria | Histórico completo |
| Soft Delete | Trazabilidad | No perder datos |
| Rate Limiting | Evitar abuso | Estabilidad |
| Circuit Breaker | Fallos externos | No cascada |
| CQRS | Reads vs Writes | Optimización |
| Bulkhead | Fallos aislados | Sin contagio |

---

**Última actualización:** 2026-05-07  
**Estado:** Baseline - agregar patrones con cada decisión arquitectónica
