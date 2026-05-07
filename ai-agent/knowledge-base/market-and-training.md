# Knowledge Base: mercado, reemplazos y planes de formación

## Metadatos

- Owner: CERTIFICATION_OWNER (con participación de dueños de práctica)
- Estado: DRAFT
- Versión: 0.1.0
- Última revisión: 2026-05-07
- Alcance: Señales de mercado por certificación, mapas de reemplazo/alternativas, skills y planes de formación (sin PII)

---

## Objetivo

Proveer al agente IA criterios y datos **aprobados** para responder consultas como:

- Credenciales perdiendo vigencia de mercado.
- Reemplazos/alternativas recomendadas.
- Brechas de skills para vender/deliver por rol/unidad.
- Planes de formación recomendados por categoría y área de expertise.

---

## Fuentes permitidas

1. Datos internos del sistema (certificaciones, asignaciones, records, vencimientos, requisitos por rol).
2. Tablas de referencia manuales (curadas por NTT DATA):
   - Señales de mercado por certificación.
   - Mapa de reemplazos/alternativas.
   - Mapa certificación → skills.
   - Planes de formación y sus items.
   - (Opcional) costos/horas estimadas por certificación/curso.

---

## Taxonomías (propuestas)

### market_status
- `GROWING`: demanda creciente / recomendada.
- `STABLE`: demanda estable.
- `DECLINING`: tendencia a la baja; evaluar migración.
- `SUNSET`: descontinuada o claramente en retirada; migrar si hay reemplazo.

### replacement_type
- `REPLACEMENT`: reemplazo recomendado (migración esperada).
- `ALTERNATIVE`: alternativa válida según contexto.
- `PREREQUISITE`: prerrequisito para otra credencial.

### collaborator_category (ejemplo; a confirmar por RRHH/People)
- `JUNIOR`
- `SEMI_SENIOR`
- `SENIOR`
- `MANAGER`

### expertise_area (ejemplo; a confirmar por prácticas)
- `Cloud`
- `Data`
- `Security`
- `AppDev`
- `AI`
- `ERP`
- `Networking`

---

## Reglas de respuesta del agente (obligatorias)

1. Nunca afirmar “vigencia de mercado” si no existe señal de mercado aprobada.
2. Cuando recomiende “renovar / migrar / no renovar”, debe separar:
   - Hechos internos (vencimiento, cobertura, requerimientos).
   - Señales de mercado (market_status, demand_score, obsolescence_risk, revisión).
   - Recomendación (con explicación y supuestos).
3. Si el usuario pide “plan de formación para X persona”:
   - Solo si está autorizado y usando tools.
   - Si no hay tool/permiso, proponer plan **genérico** por categoría/área, sin PII.

---

## Estructura de datos de referencia (contracto)

> Las siguientes tablas viven como CSV en `data/reference/` y se usan para reporting y para respuestas del agente.

### 1) certification_market_signals.csv (por certificación)
Campos mínimos recomendados:
- certification_id (uuid)
- market_status (enum)
- demand_score (0-100)
- obsolescence_risk (0-100)
- notes (texto breve)
- source (texto)
- reviewed_at (YYYY-MM-DD)
- valid_until (YYYY-MM-DD)
- is_active (true/false)

### 2) certification_replacements.csv
- from_certification_id (uuid)
- to_certification_id (uuid)
- replacement_type (enum)
- rationale (texto)
- priority (HIGH/MEDIUM/LOW)
- is_active (true/false)

### 3) skills.csv
- skill_id (uuid o código)
- name
- domain
- description
- is_active

### 4) certification_skill_map.csv
- certification_id
- skill_id
- weight (0-100)
- is_active

### 5) training_plans.csv
- training_plan_id
- name
- collaborator_category
- expertise_area
- objective
- duration_weeks
- owner_role
- version
- status
- last_reviewed_at

### 6) training_plan_items.csv
- training_plan_id
- item_type (COURSE/CERTIFICATION/LAB/ASSESSMENT)
- reference_id (certification_id o id externo de curso)
- priority
- estimated_hours
- notes

---

## Ejemplos de respuestas (plantillas)

### A) “¿Qué credenciales están perdiendo vigencia de mercado?”
- Listar certificaciones con market_status DECLINING/SUNSET.
- Para cada una:
  - Señal de mercado + fecha de revisión
  - Reemplazos (si existen)
  - Impacto interno (cantidad de records activos, vencimientos próximos)
  - Recomendación (migrar/renovar/no renovar) + justificación

### B) “¿Qué skills nos faltan para vender/deliver un proyecto?”
- Identificar contexto (unidad, rol, proyecto/tecnología).
- Consultar requirements (si existen) y calcular brecha.
- Proponer:
  - certificaciones que cubren skills faltantes
  - planes de formación por categoría/área
  - prioridades por impacto vs tiempo

### C) “Qué inversión hicimos y dónde conviene renovar”
- Aclarar fuente: costos reales vs estimados.
- Calcular por:
  - unidad, vendor, categoría, estado de mercado
- Recomendar renovación/migración por impacto y vigencia.
