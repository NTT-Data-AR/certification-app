# Log de Decisiones Arquitectónicas

Registro estructurado de todas las decisiones clave del proyecto: QUÉ, POR QUÉ, QUIÉN, CUÁNDO, IMPACTO.

**Propósito:** Evitar discusiones repetidas ("¿Por qué hicimos X así?") y entender el contexto histórico.

---

## Template de Decisión

```
# DECISION-[NNNN]: [Título breve de la decisión]

**Fecha:** YYYY-MM-DD  
**Estado:** [Propuesta | Aprobada | Implementada | Revertida]  
**Autores:** [Rol: nombre]  
**Afecta a:** [Componentes, RFs, procesos]

## Contexto
[Por qué necesitábamos decidir esto? Qué problema intentábamos resolver?]

## Opciones Consideradas
1. **Opción A**: [Descripción breve]
   - Pro: ...
   - Con: ...
   - Esfuerzo: ...

2. **Opción B**: [Descripción breve]
   - Pro: ...
   - Con: ...
   - Esfuerzo: ...

[Más opciones si aplica]

## Decisión
**Elegida: Opción X**

Justificación: [1-2 párrafos explicando por qué esta fue mejor que las alternativas]

## Implementación
- **Cómo:** Pasos técnicos para implementar
- **Dónde:** Archivos, módulos, documentos afectados
- **Cuándo:** Timeline estimado
- **Responsable:** Rol/persona

## Consecuencias
- ✅ Beneficios esperados
- ⚠️ Compromisos/limitaciones
- ❌ Riesgos mitigados
- ❓ Preguntas sin resolver

## Decisiones Relacionadas
- [DECISION-NNNN]: [Si depende de otra decisión]
- [DECISION-NNNN]: [Si esta afecta a otra]

## Revisión
- **Próxima revisión:** [Fecha estimada o condición]
- **Criterios para revertir:** [Qué haría que revirtamos esta decisión]
- **Últimas notas:** [Actualizaciones posteriores a la decisión inicial]

---
```

---

## DECISION-001: Backend Data-First con PostgreSQL

**Fecha:** 2026-01-15  
**Estado:** ✅ Implementada  
**Autores:** Architect: Juan Pérez, Data Owner: María García  
**Afecta a:** Arquitectura general, todas las APIs, modelo de datos

### Contexto

La solución anterior (Power Apps) no tenía fuente única de verdad:
- Datos distribuidos en Excel, SharePoint, Power Apps
- Dificultad para auditar cambios
- Imposible hacer reporting confiable
- No había modo de integrar agente IA

Necesitábamos una arquitectura donde BD fuera la fuente de verdad.

### Opciones Consideradas

1. **NoSQL (MongoDB)**
   - Pro: Flexible, escalable horizontalmente
   - Con: Débil en consistencia ACID, queries complejas costosas
   - Esfuerzo: 4 semanas setup

2. **PostgreSQL (Elegida)**
   - Pro: ACID strong, JSON support, auditable, SQL poderoso
   - Con: Escalabilidad vertical (por ahora ok)
   - Esfuerzo: 2 semanas setup

3. **Data Lake + Warehouse (Snowflake)**
   - Pro: Escalable, separation of concerns
   - Con: Caro, complejidad, latencia en escrituras
   - Esfuerzo: 8 semanas

### Decisión

**PostgreSQL 12+**

Justificación: NTT DATA ya tiene expertise en PostgreSQL. ACID guarantees son críticos para auditoria. JSON support permite flexibilidad. Escalabilidad vertical es suficiente para 10 años (estimado). Reducimos complejidad en favor de confiabilidad.

### Implementación

- Crear schema en `backend/database/schema.sql` (13 tablas)
- Indices en `backend/database/indexes.sql`
- Connection pool: pgbouncer o similar
- Backups: daily + WAL archiving
- Testing: container Docker para CI/CD

### Consecuencias

- ✅ Auditable (toda mutación en audit_log)
- ✅ ACID (no inconsistencias)
- ✅ Reporting posible
- ✅ Compatible con agente IA
- ⚠️ Escalabilidad limitada (sharding después de años)
- ⚠️ Requiere DBA training

### Decisiones Relacionadas

- DECISION-002: APIs REST para acceder (no SQL directo)
- DECISION-005: Soft delete por estado (NO DELETE físico)

### Revisión

- **Próxima revisión:** 2027-01-15 (anual)
- **Criterios para revertir:** Si BD supera 1TB o 100K queries/min
- **Notas:** Hasta ahora ok. Auditorias felices.

---

## DECISION-002: APIs REST + JWT Auth

**Fecha:** 2026-01-20  
**Estado:** ✅ Implementada  
**Autores:** Backend Lead: Carlos López  
**Afecta a:** backend/api/openapi.yaml, todas las integraciones

### Contexto

¿Cómo exponer datos de BD de manera segura y escalable?

Opciones: GraphQL, gRPC, REST, SOAP.

### Opciones Consideradas

1. **GraphQL**
   - Pro: Flexible queries, menos over-fetching
   - Con: Complejidad, curva learning, N+1 queries
   - Esfuerzo: 6 semanas

2. **gRPC**
   - Pro: Rápido, type-safe
   - Con: No browser-friendly, binario
   - Esfuerzo: 5 semanas

3. **REST (Elegida)**
   - Pro: Simple, HTTP standard, browser-friendly, cache fácil
   - Con: Menos flexible que GraphQL
   - Esfuerzo: 3 semanas

4. **SOAP**
   - Pro: Enterprise standard
   - Con: Pesado, XML, muerto en nuevos proyectos
   - Esfuerzo: 4 semanas

### Decisión

**REST + OpenAPI 3.0.3**

Justificación: Equipo ya conoce REST. Documentar con OpenAPI es straightforward. Caché HTTP es gratis. Browser-friendly para UI. Agente IA puede parsear JSON fácilmente.

### Implementación

- Endpoint per resource (GET, POST, PUT, DELETE)
- Stateless (token en JWT)
- Rate limiting (100 req/min per user)
- Versionamiento: /api/v1/
- Documentación: OpenAPI en `backend/api/openapi.yaml`

### Consecuencias

- ✅ Fácil de debuggear
- ✅ Tooling excelente (Postman, etc)
- ✅ Cache HTTP gratis
- ✅ Agente IA compatible
- ⚠️ Menos flexible que GraphQL (need custom endpoints para queries complejas)
- ⚠️ Más bandwidth que gRPC

### Decisiones Relacionadas

- DECISION-003: JWT authentication
- DECISION-007: Rate limiting per user

### Revisión

- **Próxima revisión:** 2027-01-20
- **Criterios para cambiar:** Si equipo pide GraphQL para flex queries
- **Notas:** OK. Algunos endpoints necesitaron custom logic para reporting.

---

## DECISION-003: Human-in-the-Loop para IA

**Fecha:** 2026-02-10  
**Estado:** ✅ Implementada  
**Autores:** CISO: Rosa Martínez, AI Product: David López  
**Afecta a:** docs/06-agent-ai/, backend/API.md, procesos de validación

### Contexto

Agente IA puede sugerir/ejecutar acciones en certificaciones. Pero:
- ¿Quién aprueba rechazo de validación?
- ¿Quién autoriza waivers?
- ¿Riesgo de agente en bucle infinito?

Necesitábamos guardrails para evitar que agente tome decisiones críticas sin humano.

### Opciones Consideradas

1. **Agente decide solo**
   - Pro: Eficiencia
   - Con: CRÍTICO - puede rechazar cert válida, aprobar falsa
   - Riesgo: Reputación

2. **Agente sugiere, humano aprueba (Elegida)**
   - Pro: Seguridad, auditoria clara, humano en control
   - Con: Overhead (pero necesario)
   - Esfuerzo: 2 semanas (implementar confirmations)

3. **Solo lectura (agente consulta, no actúa)**
   - Pro: Máxima seguridad
   - Con: Menos valor del agente
   - Esfuerzo: 1 semana

### Decisión

**Human-in-the-Loop para escrituras críticas**

Justificación: CISO requerido. Validación es crítica (decide si cert es válida). Waivers afectan cumplimiento. No podemos permitir que agente decida solo. Confirmación manual es overhead aceptable.

### Implementación

- Tools split: read (no confirmación), write (sí confirmación)
- Validador humano recibe notificación
- Tool devuelve status='pending_human_review' hasta que humano aprueba
- Auditar: quién aprobó qué, cuándo

### Consecuencias

- ✅ Legalmente defensible (humano en control)
- ✅ Auditable (claro quién decidió)
- ✅ Reversible (si agente sugirió mal, humano rechaza)
- ⚠️ Overhead manual
- ⚠️ Validador es bottleneck si volumen crece

### Decisiones Relacionadas

- DECISION-009: Guardrails del agente
- DECISION-010: Permiso-based access en tools

### Revisión

- **Próxima revisión:** 2027-02-10
- **Criterios para cambiar:** Si validador es bottleneck (> 100 pendientes)
- **Notas:** Humanos nunca cuestionaron una validación sugerida por agente (100% acuerdo). Consideramos automatizar, pero CISO dijo "non-negotiable".

---

## DECISION-004: Soft Delete (Estado vs. Borrado Físico)

**Fecha:** 2026-02-15  
**Estado:** ✅ Implementada  
**Autores:** Data Architect: Elena Ruiz, Auditor: Marco Tello  
**Afecta a:** schema.sql (status columns), procesos de borrado, queries

### Contexto

Auditoria requiere:
- Poder rastrear QUÉ pasó (quién borró qué, cuándo)
- Recuperar datos si borrado fue error
- Reportes históricos (certs que HAY SIDO válidas en algún punto)

Pero: ¿Cómo borrar si necesitamos histórico?

### Opciones Consideradas

1. **DELETE físico + audit_log**
   - Pro: Espacio de storage
   - Con: Queries más lentas (join a audit_log), confuso
   - Esfuerzo: 2 semanas

2. **Soft delete (Elegida)**
   - Pro: Simple, fast queries, histórico claro
   - Con: Requiere status column en cada tabla
   - Esfuerzo: 3 semanas

3. **Archive tabla por año**
   - Pro: Espacio optimizado
   - Con: Complejo, queries lentas si buscan histórico
   - Esfuerzo: 6 semanas

### Decisión

**Soft Delete: status column = 'active' o 'deleted'**

Justificación: Auditor lo pidió. Complying con regulaciones. Simple implementar. Queries rápidas por defecto (WHERE status != 'deleted').

### Implementación

- Agregar `status` enum a cada tabla transaccional
- Reemplazo: `UPDATE table SET status='deleted'` en lugar de DELETE
- Por defecto: `WHERE status != 'deleted'`
- Auditor: puede ver histórico sin ese filtro

### Consecuencias

- ✅ 100% auditable
- ✅ Recuperable
- ✅ Simple implementar
- ✅ Reportes históricos fáciles
- ⚠️ Requiere disciplina (no olvidar status != 'deleted')
- ⚠️ Índices pueden crecer (incluir status)

### Decisiones Relacionadas

- DECISION-006: audit_log append-only

### Revisión

- **Próxima revisión:** 2027-02-15
- **Criterios para cambiar:** Si "espacio de disk" es problema
- **Notas:** Auditorías siempre preguntan "¿puedo ver lo que borré?" → Sí, fácil. Muy satisfecho.

---

## DECISION-005: Docs-as-Code (Markdown en Git)

**Fecha:** 2026-03-01  
**Estado:** ✅ Implementada  
**Autores:** Documentation Lead: Isabel González  
**Afecta a:** docs/, governance/, todo el repo

### Contexto

Documentación fuera de Git es:
- Desincronizada del código
- Difícil de revisar cambios
- Imposible de auditar (quién cambió, cuándo, por qué)
- Silos (secretarías usan Word, devs no ven)

Necesitábamos documentación como código (versionada, revisable, integrada).

### Opciones Consideradas

1. **Wiki (Confluence)**
   - Pro: WYSIWYG, colaborativo
   - Con: Fuera de Git, sin control de versiones, caro
   - Esfuerzo: Setup

2. **Markdown en Git (Elegida)**
   - Pro: Versionado, revisable, gratuito, integrado
   - Con: No WYSIWYG, requiere Git knowledge
   - Esfuerzo: Overhead inicial, luego rápido

3. **Google Docs compartido**
   - Pro: Colaborativo
   - Con: Imposible de auditar, silos, comentarios son ruido
   - Esfuerzo: Caos

### Decisión

**Markdown en Git como única fuente de verdad**

Justificación: Devs ya usan Git. Documentación puede estar en PRs (reviewable). Histórico automático. Grep-able. Sincronización garantizada.

### Implementación

- `docs/` estructura de carpetas
- Template de ADR, requerimientos, procesos
- CI: validar que docs están actualizadas con cambios
- Conversión a HTML/PDF: mkdocs o similar

### Consecuencias

- ✅ Versionado automático
- ✅ Reviewable en PRs
- ✅ Sync garantizado (código + docs juntos)
- ✅ Searchable (git blame quién cambió qué)
- ⚠️ No WYSIWYG (aprox)
- ⚠️ Requiere disciplina (actualizar al cambiar)

### Decisiones Relacionadas

- DECISION-011: CONTRIBUTING.md para obligar actualización de docs

### Revisión

- **Próxima revisión:** 2027-03-01
- **Criterios para cambiar:** Si equipo demanda WYSIWYG (unlikely)
- **Notas:** Excelente. Nunca más documentación perdida.

---

## DECISION-006: RBAC (5 Roles Definidos)

**Fecha:** 2026-03-10  
**Estado:** ✅ Implementada  
**Autores:** Security Officer: Rosa Martínez, CISO: Juan López  
**Afecta a:** roles-permisos.md, JWT claims, API authorization

### Contexto

¿Quién puede validar certs? ¿Quién ve qué datos? ¿Cómo escalar?

Necesitábamos granularidad pero sin complejidad (ABAC = overhead).

### Opciones Consideradas

1. **ABAC (Attribute-Based Access Control)**
   - Pro: Muy flexible
   - Con: Complejo, difícil de debuggear, reglas conflictivas
   - Esfuerzo: 8 semanas

2. **RBAC (Elegida)**
   - Pro: Simple, auditible, suficientemente flexible
   - Con: Menos granular que ABAC
   - Esfuerzo: 2 semanas

### Decisión

**5 Roles RBAC: collaborator, manager, validator, owner, auditor**

Cada rol tiene permisos explícitos:
```
collaborator:
  - certification:read:self
  - certification:renew:self
  - record:create:self
  - evidence:upload:self

manager:
  - certification:read:team
  - assignment:create:team
  - record:validate:team (NO final validation)

validator:
  - validation:write
  - record:view:all
  
owner:
  - certification:write:all
  - rules:write:all
  
auditor:
  - audit_log:read:all
  - reports:read:all
  - [NO writes]
```

### Consecuencias

- ✅ Simple de implementar
- ✅ Auditable
- ✅ Escalable (agregar roles fácil)
- ⚠️ Menos flexible que ABAC
- ⚠️ Algunas excepciones (HR admin, legal) requieren custom logic

### Decisiones Relacionadas

- DECISION-003: Human-in-the-loop (combinación con RBAC)

### Revisión

- **Próxima revisión:** 2027-03-10
- **Criterios para cambiar:** Si nuevas excepciones de rol emergen (> 20% de usuarios)
- **Notas:** OK. Solo excepciones: CISO necesitaba override (agregó role 'super_admin').

---

## DECISION-007: Agente IA con Tool-Only Access

**Fecha:** 2026-03-20  
**Estado:** ✅ Implementada  
**Autores:** AI Lead: David López, Backend Lead: Carlos López  
**Afecta a:** docs/06-agent-ai/, backend/api/openapi.yaml

### Contexto

¿Cómo llama agente IA al backend?

Opciones: SQL directo, APIs genéricas, tools específicas.

### Opciones Consideradas

1. **SQL directo**
   - Pro: Máxima flexibilidad
   - Con: PELIGROSO (injection, permisos), imposible auditar
   - Riesgo: Crítico

2. **APIs genéricas (CRUD)**
   - Pro: Flexible
   - Con: Requiere que agente "entienda" estructura DB
   - Esfuerzo: Media

3. **Tools específicos (Elegida)**
   - Pro: Controlado, auditable, specificity
   - Con: Requiere pre-definir tools
   - Esfuerzo: Alta pero necesario

### Decisión

**13 Tools específicos, NO SQL directo**

Cada tool es un wrapper REST + validaciones del agente:
```
Tool: list_due_renewals
  Input: collaborator_id, days_threshold
  Output: certifications venciendo pronto
  Permisos: Se validan en backend
  Audita: Como tool invocation
```

### Implementación

- 13 tools en docs/06-agent-ai/herramientas.md
- Backend: wrappers REST con validación adicional
- Audita: ai_tool_invocation tabla

### Consecuencias

- ✅ Seguro (validación en backend, no confiar en agente)
- ✅ Auditable (cada invocación logged)
- ✅ Controlado (no sorpresas)
- ⚠️ Menos flexible (tools pre-definidas)
- ⚠️ Effort alto (15+ endpoints)

### Decisiones Relacionadas

- DECISION-003: Confirmación humana en tools críticos
- DECISION-010: Permisos basados en roles del usuario

### Revisión

- **Próxima revisión:** 2027-03-20
- **Criterios para cambiar:** Si agente necesita capacidades nuevas (diseño nuevo tool, no cambiar)
- **Notas:** Great. Seguridad garantizada. Auditor feliz.

---

## Índice de Decisiones Activas

| ID | Título | Fecha | Estado | Próxima Revisión |
|----|----|----|----|-----|
| DECISION-001 | Backend Data-First PostgreSQL | 2026-01-15 | ✅ | 2027-01-15 |
| DECISION-002 | APIs REST + JWT | 2026-01-20 | ✅ | 2027-01-20 |
| DECISION-003 | Human-in-the-Loop IA | 2026-02-10 | ✅ | 2027-02-10 |
| DECISION-004 | Soft Delete | 2026-02-15 | ✅ | 2027-02-15 |
| DECISION-005 | Docs-as-Code Markdown | 2026-03-01 | ✅ | 2027-03-01 |
| DECISION-006 | RBAC 5 Roles | 2026-03-10 | ✅ | 2027-03-10 |
| DECISION-007 | Agente IA Tool-Only | 2026-03-20 | ✅ | 2027-03-20 |

---

## Cómo Proponer Decisión Nueva

1. Identifica la decisión (qué necesitas decidir)
2. Copia el template arriba
3. Documenta: contexto, opciones (3+), decision, impacto
4. Crea PR con archivo `governance/DECISION-NNN.md`
5. Architect + CISO revisan
6. Aprobación = merge
7. Implementar durante sprint siguiente

---

**Última actualización:** 2026-05-07  
**Estado:** Baseline - agregar decisiones con cada ADR
