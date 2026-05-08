# Matriz de Trazabilidad

Mapeo completo que conecta Requerimientos Funcionales → Procesos → APIs → Casos de Prueba.

**Propósito:** Entender el impacto completo de un cambio. Ej: "¿Si cambio validación, qué se ve afectado?"

---

## 1. Matriz Master (RF → Proceso → API → Test)

| RF ID | Requerimiento | Proceso | Endpoint API | Tabla BD | Test Case |
|-------|--|--|--|--|--|
| **RF-001** | Gestionar catálogo de certificaciones | alta-certificacion | POST /certifications | certification | TC-001 |
| **RF-002** | Consultar certificaciones por filtros | - | GET /certifications | certification | TC-002 |
| **RF-003** | Gestionar colaboradores sincronizados | - | GET /collaborators | collaborator | TC-003 |
| **RF-004** | Definir requerimientos por rol | - | POST /role-requirements | role_certification_requirement | TC-004 |
| **RF-005** | Asignar certificaciones | asignacion-certificacion | POST /assignments | certification_assignment | TC-005 |
| **RF-006** | Registrar certificación obtenida | alta-certificacion | POST /records | certification_record | TC-006 |
| **RF-007** | Gestionar evidencias | gestion-evidencias | POST /evidences | evidence_document | TC-007 |
| **RF-008** | Validar certificación reportada | validacion-aprobacion | POST /records/{id}/validation | validation_event | TC-008 |
| **RF-009** | Calcular vigencia | renovacion-certificacion | GET /records/{id}/expiration | certification_record | TC-009 |
| **RF-010** | Alertas de vencimiento | seguimiento-vencimientos | GET /notifications | notification | TC-010 |
| **RF-011** | Gestionar renovación | renovacion-certificacion | POST /renewals | (new table) | TC-011 |
| **RF-012** | Gestionar waivers | soporte-excepciones | POST /waivers | exception_waiver | TC-012 |
| **RF-013** | Dashboard operativo | reporting | GET /dashboard | (view) | TC-013 |
| **RF-014** | Exportar reportes autorizados | reporting | GET /reports/export | (view) | TC-014 |
| **RF-015** | Auditoria funcional | - | GET /audit-log | audit_log | TC-015 |
| **RF-016** | Consultas mediante agente IA | - | GET /tools/* | - | TC-IA-001 |
| **RF-017** | Acciones mediante agente IA | - | POST /tools/* | - | TC-IA-002 |
| **RF-018** | Knowledge base del agente | - | GET /knowledge-base | ai_conversation | TC-IA-003 |
| **RF-019** | Calidad de datos | - | POST /dq-issues | data_quality_issue | TC-019 |
| **RF-020** | Linaje y fuente de datos | - | GET /lineage | audit_log | TC-020 |

---

## 2. Mapeo por Proceso

### 2.1 Proceso: Alta de Certificación
```
RF-001: Gestionar catálogo
├─ Entrada: Nombre, código, vendor, categoría, validez
├─ APIs:
│   POST /certifications (crear)
│   GET /certifications (listar)
│   PUT /certifications/{id} (actualizar)
├─ Tabla: certification
├─ Validaciones:
│   - Certificación única (vendor + name)
│   - Validez > 0 meses
│   - Vendor existe
├─ Tests:
│   - TC-001a: Crear cert válida
│   - TC-001b: Rechazar duplicada
│   - TC-001c: Validez negativa

RF-006: Registrar certificación obtenida
├─ Entrada: Colaborador, certificación, fechas, evidencia
├─ APIs:
│   POST /records (crear registro)
│   POST /evidences (subir archivo)
├─ Tablas: certification_record, evidence_document
├─ Validaciones:
│   - Expiration >= issue_date
│   - Colaborador existe
│   - Evidencia < 50MB
├─ Tests:
│   - TC-006a: Registrar válido
│   - TC-006b: Fecha inválida rechazada
│   - TC-006c: Archivo grande rechazado
```

### 2.2 Proceso: Asignación de Certificación
```
RF-005: Asignar certificaciones
├─ Entrada: Colaborador, certificación, fecha límite, prioridad
├─ APIs:
│   POST /assignments (crear asignación)
│   GET /assignments (listar)
├─ Tabla: certification_assignment
├─ Validaciones:
│   - Manager del colaborador
│   - Certificación activa
│   - Due date > hoy
├─ Tests:
│   - TC-005a: Asignación válida
│   - TC-005b: Sin permisos rechazada
│   - TC-005c: Due date pasado rechazado
```

### 2.3 Proceso: Validación y Aprobación
```
RF-008: Validar certificación reportada
├─ Entrada: Decisión (approved/rejected), razón
├─ APIs:
│   POST /records/{id}/validation (validar)
├─ Tablas: validation_event, certification_record
├─ Validaciones:
│   - Solo validador autorizado
│   - Evidencia presente
│   - Record en estado pendiente
├─ Efectos:
│   - Si approved → certification_record.validation_status = 'approved'
│   - Si rejected → vuelve a pending_evidence
├─ Tests:
│   - TC-008a: Validación aprobada
│   - TC-008b: Validación rechazada con razón
│   - TC-008c: Sin permisos rechazada
```

### 2.4 Proceso: Renovación de Certificación
```
RF-011: Gestionar renovación
├─ Entrada: Record a renovar, nueva evidencia, nuevas fechas
├─ APIs:
│   POST /renewals (iniciar)
│   POST /evidences (subir nueva)
│   POST /renewals/{id}/validate (validar)
├─ Tablas: (renewal_request), certification_record, evidence_document
├─ Validaciones:
│   - Certificación próxima a vencer (< 90 días)
│   - Al menos 14 días restantes
│   - Colaborador ACTIVE
├─ SLA:
│   - 30 días para carga de evidencia
│   - 10 días hábiles para validación
├─ Tests:
│   - TC-011a: Renovación completada
│   - TC-011b: Rechazo + reintento
│   - TC-011c: Vencimiento durante renovación
```

### 2.5 Proceso: Reporting
```
RF-013: Dashboard operativo
RF-014: Exportar reportes autorizados
├─ Entrada: Filtros (unit_id, cert_id, date_range), formato (JSON/CSV/PDF)
├─ APIs:
│   GET /reports/coverage (cobertura)
│   GET /reports/expiring (vencimientos próximos)
│   GET /reports/export (exportar)
├─ Tablas: (views) → certification_record, certification_assignment
├─ Validaciones:
│   - Manager solo ve su unidad
│   - Owner ve todo
│   - Auditor acceso limitado
├─ Tests:
│   - TC-013a: Reporte sin permisos rechazado
│   - TC-013b: Reporte con permisos retorna datos
│   - TC-014a: Exportación sin datos sensibles
```

---

## 3. Mapeo por API

### GET /certifications
**RF-002:** Consultar certificaciones por filtros
```
Parámetros: vendor_id, category, name, is_active, page, limit
Respuesta: Array de certifications
Permisos: certification:read (cualquiera autenticado)
Tablas: certification JOIN vendor
Tests:
  - TC-002a: Búsqueda por categoría
  - TC-002b: Paginación
  - TC-002c: Filtro activas
```

### POST /assignments
**RF-005:** Asignar certificaciones
```
Body: assignee_id, certification_id, due_date, priority, reason
Respuesta: assignment con ID y estado
Permisos: certification:assign (manager, owner)
Tablas: certification_assignment
Auditar: Quién asignó, cuándo, a quién
Tests:
  - TC-005a: Asignación válida
  - TC-005b: Permisos insuficientes
  - TC-005c: Asignación duplicada
```

### POST /records
**RF-006:** Registrar certificación obtenida
```
Body: collaborator_id, certification_id, issue_date, expiration_date, credential_id
Respuesta: record con ID y status
Permisos: certification:record (colaborador self, manager, admin)
Tablas: certification_record
Auditar: Quién registró, qué datos
Tests:
  - TC-006a: Registro válido
  - TC-006b: Fecha inválida
  - TC-006c: Colaborador no existe
```

### POST /records/{recordId}/validation
**RF-008:** Validar certificación reportada
```
Body: decision (approved|rejected), reason
Respuesta: validation_event con resultado
Permisos: validation:write (validador)
Tablas: validation_event, certification_record (UPDATE)
Auditar: Validador, decisión, razón, timestamp
Tests:
  - TC-008a: Aprobación
  - TC-008b: Rechazo con razón
  - TC-008c: Revalidación rechazada
```

### GET /reports/coverage
**RF-013, RF-014:** Dashboard operativo, exportar reportes
```
Parámetros: unit_id, cert_id, as_of_date, format (json|csv|pdf)
Respuesta: Agregados por unidad y certificación
Permisos: reports:read (manager own unit, owner all)
Tablas: views → certification_record, certification_assignment
Tests:
  - TC-013a: Cobertura por unidad
  - TC-013b: Brecha de skills
  - TC-014a: Exportación JSON
  - TC-014b: Exportación CSV
```

---

## 4. Mapeo por Tabla

### certification
```
Usado por:
  - RF-001: Crear, actualizar
  - RF-002: Consultar, filtrar
  - RF-004: Requerimientos por rol
  - RF-005: Validar existe
  - RF-006: Validar existe
  
RFs afectados si cambio schema:
  - RF-002 (filtros)
  - RF-013 (reporting)
  - RF-020 (linaje)
```

### certification_record
```
Usado por:
  - RF-006: Crear registro
  - RF-008: Validar (UPDATE)
  - RF-009: Calcular vigencia
  - RF-010: Alertas (filtro expiration_date)
  - RF-011: Renovación (crear nuevo record)
  - RF-013: Dashboard (cuenta, agregados)
  - RF-015: Auditoria (histórico)
  - RF-020: Linaje (source_system)
  
Índices críticos:
  - (collaborator_id, status) → para RF-010, RF-013
  - (expiration_date) → para RF-009, RF-010
  - (validation_status) → para RF-008
  
RFs afectados si cambio:
  - RF-009, RF-010, RF-011, RF-013 (todos los que leen)
```

### certification_assignment
```
Usado por:
  - RF-005: Crear asignación
  - RF-013: Dashboard (cuenta pending, completadas)
  - RF-015: Auditoria

RFs afectados si cambio:
  - RF-013 (reporting)
  - RF-015 (auditoria)
```

### validation_event
```
Usado por:
  - RF-008: Crear decisión
  - RF-015: Auditoria (decisiones)

RFs afectados si cambio:
  - RF-008 (validación)
  - RF-015 (auditoria)
```

### audit_log
```
Usado por:
  - RF-015: Auditoria funcional
  - RF-020: Linaje de datos

Crítico para cumplimiento → no eliminar ni modificar

RFs afectados si cambio:
  - RF-015 (auditoria)
  - RF-020 (linaje)
```

---

## 5. Análisis de Impacto: Escenarios

### Escenario 1: Cambio en Duración de Validez
**Cambio:** Agregar campo `validity_years` además de `validity_months`

**Impacto:**

```
RF-001: Crear cert
  ├─ API: POST /certifications (agregar parámetro)
  ├─ Tabla: certification (nueva columna)
  ├─ Tests: TC-001d (validar años)
  └─ Aprobado por: Owner

RF-009: Calcular vigencia
  ├─ Lógica: expiration = issue_date + (validity_years * 12 meses)
  ├─ Tests: TC-009a (años correctamente)
  └─ Cambio: LÓGICA, no BD

RF-010: Alertas de vencimiento
  ├─ NO AFECTADO (usa expiration_date, ya calculado)
  └─ Test: Sin cambios

RF-013: Dashboard
  ├─ NO AFECTADO directamente
  ├─ Pero reporte de "vigencia típica" ahora varía
  └─ Test: TC-013d (verificar años reflejados)

Tabla afectada: certification
  - Query impacto: Ninguno (lógica en aplicación)
  - Índices: Sin cambios
  
Total cambios:
  - 1 API endpoint
  - 1 tabla BD
  - 4 test cases
  - 0 procesos nuevos
  - 0 dependencias rotas
```

### Escenario 2: Agregar Flujo de Recertificación (Sin Renovación)
**Cambio:** Nueva RF-021 = Certif. puede actualizarse sin vencimiento próximo

**Impacto:**

```
Nuevos:
  - RF-021: Recertificación sin plazo
  - Proceso: recertificacion.md
  - API: POST /recertifications
  - Tabla: (reusar certification_record)
  
Afectados:
  - RF-006: Crear registro
    ├─ API: GET /certification-types (new)
    └─ Test: TC-006d (tipo = recertification)
  
  - RF-008: Validar
    ├─ Lógica: aplica igual
    └─ Test: Sin cambios
  
  - RF-011: Renovación
    ├─ Excluir recertificaciones del flujo de renovación
    └─ Test: TC-011d (no listar recertificadas)
  
  - RF-013: Dashboard
    ├─ Mostrar recertificaciones separadas
    └─ Test: TC-013e (separar por tipo)

Tabla afectada: certification_record
  - Nueva columna: record_type (renovation|recertification)
  - Query impacto: WHERE record_type = 'recertification'
  - Índices: Agregar (collaborator_id, record_type)
  
Total cambios:
  - 2 APIs nuevas
  - 1 tabla (1 columna nueva, 1 índice)
  - 7 test cases
  - 1 proceso nuevo
  - 2 flujos impactados
```

---

## 6. Cómo Usar Esta Matriz

### Para Developer que Cambia Código

```
1. Identifica el RF que cambias:
   ej: RF-006 = "Registrar certificación obtenida"

2. Revisa qué está conectado (esta matriz):
   - Procesos: alta-certificacion, gestion-evidencias
   - APIs: POST /records, POST /evidences
   - Tablas: certification_record, evidence_document
   - Tests: TC-006a, TC-006b, TC-006c

3. Identifica qué SE PUEDE ROMPER:
   - ¿Cambio API? → Revisar todos los clientes (UI, agente, integraciones)
   - ¿Cambio tabla? → Revisar query impact en otros RFs
   - ¿Cambio lógica? → Revisar tests

4. Actualiza:
   - Código
   - Tests (TC-006x)
   - Esta matriz
   - Documentación (procesos, API.md)
```

### Para QA que Diseña Casos de Prueba

```
1. Obtén el RF (ej: RF-011 = Renovación)

2. De esta matriz, extrae:
   - Proceso: renovacion-certificacion.md (lee detalles)
   - APIs: POST /renewals, POST /renewals/{id}/validate
   - Tablas: certification_record, evidence_document
   - SLA: 30d para carga, 10d para validación

3. Diseña casos de prueba cubriendo:
   - Happy path: renovación completada
   - Errores: vencimiento durante proceso, sin permisos
   - SLA: validar tiempos
   - Datos: entrada/salida correcta
   - Auditoria: registrado en audit_log

4. Etiqueta: TC-011a, TC-011b, TC-011c, etc.
```

### Para Architect que Evalúa Impacto

```
1. Cambio propuesto: ej "Agregar campo X a tabla Y"

2. Busca tabla Y en Mapeo por Tabla:
   - Qué RFs la usan
   - Qué índices existen
   - Qué queries se ven afectadas

3. Revisa Análisis de Impacto:
   - Cuántos endpoints cambian
   - Cuántos procesos se tocan
   - Riesgo de romper dependencias

4. Presenta impacto a equipo:
   - "Cambio afecta 3 RFs, 2 APIs, 1 tabla, requiere 5 test cases"
```

---

## 7. Actualización de Esta Matriz

**Cuándo actualizar:**
- ✅ Nuevo RF aprobado → agrega a matriz master
- ✅ Nuevo endpoint API → mapea a RF + proceso + tabla
- ✅ Nueva tabla o columna → registra dependencias

**Quién:**
- Architect aprueba cambios
- Developer actualiza
- QA valida cobertura

**Check:**
```bash
# Verificar que RFs en matriz == RFs en requerimientos-funcionales.md
grep "^| RF-" docs/TRAZABILIDAD.md | wc -l
grep "^| RF-" docs/01-analisis-funcional/requerimientos-funcionales.md | wc -l
# Deben ser iguales
```

---

**Última actualización:** 2026-05-07  
**Estado:** Baseline - actualizar con cada RF nueva
