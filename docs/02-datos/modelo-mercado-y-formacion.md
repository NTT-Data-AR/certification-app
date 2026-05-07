# Modelo de datos (extensión): mercado y formación

## Propósito

Extender el modelo para que el agente IA pueda responder (con datos verificables y reglas explícitas) preguntas como:

- ¿Qué **capacidades certificadas** tenemos hoy?
- ¿Cuáles están **en riesgo** (por vencimiento, baja cobertura, baja demanda, etc.)?
- ¿Qué credenciales están **perdiendo vigencia de mercado**?
- ¿Qué **reemplazos / alternativas** existen?
- ¿Qué **skills** nos faltan para **vender/deliver** un proyecto (por rol, práctica, unidad)?
- ¿Qué **inversión** hicimos y dónde conviene **renovar**?

Además, permitir asociar **planes de formación** para colaboradores definidos por:
- **Categoría** del colaborador (seniority/carrera) y
- **Área de expertise** (práctica, disciplina, capability).

> Nota: esta extensión introduce nuevas entidades de referencia. La información “de mercado” se mantiene **manualmente** como tabla de referencia (curada por dueños de práctica/certificaciones).

---

## Principios

1. **Separar “hechos internos” vs “señales de mercado”**
   - Interno: asignaciones, records, vencimientos, cobertura, costos, horas.
   - Mercado: demanda, tendencia, reemplazos, estado del vendor, obsolescencia.
2. **No inferir mercado sin fuente**: el agente solo usa valores de referencia aprobados.
3. **Versionar y auditar** cambios de referencia (relevancia mercado, reemplazos, costos).
4. **Desnormalizar para reporting** solo en vistas/materializadas (no en tablas core).

---

## Entidades nuevas (propuestas)

### 1) certification_market_signal (referencia de mercado por certificación)

Registra la “vigencia de mercado” y reemplazos/alternativas para una certificación dada.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| market_signal_id | uuid | PK |
| certification_id | uuid | FK a `certification` |
| market_status | text | `GROWING` \| `STABLE` \| `DECLINING` \| `SUNSET` |
| demand_score | int | 0-100 (curado manualmente) |
| obsolescence_risk | int | 0-100 |
| notes | text | Justificación breve y verificable (sin claims no sustentados) |
| source | text | “Comité práctica”, “Vendor roadmap”, etc. |
| reviewed_at | date | Última revisión |
| valid_until | date | Fecha de próxima revisión/revalidación |
| is_active | boolean | Control de vigencia de la señal |

#### Reemplazos / alternativas

Se modelan como relación N a N (porque una cert puede “migrar” a varias).

**certification_replacement_map**

| Campo | Tipo | Descripción |
| --- | --- | --- |
| replacement_id | uuid | PK |
| from_certification_id | uuid | Certificación “origen” |
| to_certification_id | uuid | Certificación alternativa/reemplazo |
| replacement_type | text | `REPLACEMENT` \| `ALTERNATIVE` \| `PREREQUISITE` |
| rationale | text | Motivo (p.ej. vendor discontinuó, nueva versión, etc.) |
| priority | text | `HIGH` \| `MEDIUM` \| `LOW` |
| is_active | boolean | |

---

### 2) skill (skills internos / capabilities)

Permite mapear certificaciones a skills y luego a roles y a demanda de delivery.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| skill_id | uuid | PK |
| name | text | Nombre canonical (p.ej. “Kubernetes Administration”) |
| domain | text | Dominio (Cloud, Data, Security, AppDev, etc.) |
| description | text | Definición corta |
| is_active | boolean | |

**certification_skill_map**

| Campo | Tipo | Descripción |
| --- | --- | --- |
| map_id | uuid | PK |
| certification_id | uuid | FK `certification` |
| skill_id | uuid | FK `skill` |
| weight | int | 0-100 (cuánto aporta) |
| is_active | boolean | |

---

### 3) delivery_capability_requirement (skills requeridos para vender/deliver)

Define demanda interna (proyectos/servicios) de skills por unidad/práctica/rol.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| requirement_id | uuid | PK |
| business_unit_id | uuid | FK `business_unit` (nullable si aplica global) |
| professional_role_id | uuid | FK `professional_role` (nullable) |
| skill_id | uuid | FK `skill` |
| required_level | text | `BASIC` \| `INTERMEDIATE` \| `ADVANCED` |
| required_headcount | int | Cantidad objetivo |
| priority | text | `HIGH` \| `MEDIUM` \| `LOW` |
| valid_from | date | |
| valid_to | date | |
| source | text | Origen (p.ej. “pipeline H2 2026”) |
| is_active | boolean | |

---

### 4) training_plan (planes de formación por categoría y expertise)

Representa un plan recomendado (no PII) que se puede asociar a colaboradores según su perfil.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| training_plan_id | uuid | PK |
| name | text | Nombre del plan |
| collaborator_category | text | Ej: `JUNIOR` \| `SEMI_SENIOR` \| `SENIOR` \| `MANAGER` (taxonomía a definir) |
| expertise_area | text | Ej: “Cloud”, “Data”, “Security”, “AppDev”, “AI”, etc. |
| objective | text | Qué busca lograr |
| duration_weeks | int | Estimación |
| owner_role | text | Dueño (p.ej. Certification Owner) |
| version | text | Semver o similar |
| status | text | `DRAFT` \| `APPROVED` \| `DEPRECATED` |
| last_reviewed_at | date | |

**training_plan_item**

| Campo | Tipo | Descripción |
| --- | --- | --- |
| item_id | uuid | PK |
| training_plan_id | uuid | FK |
| item_type | text | `COURSE` \| `CERTIFICATION` \| `LAB` \| `ASSESSMENT` |
| reference_id | uuid/text | FK a `certification` (si aplica) o ID externo de curso |
| priority | text | `HIGH` \| `MEDIUM` \| `LOW` |
| estimated_hours | int | |
| notes | text | |

**collaborator_training_plan (asignación a personas)**

> Esta tabla sí referencia colaboradores, por lo que aplica privacidad y permisos.

| Campo | Tipo | Descripción |
| --- | --- | --- |
| assignment_id | uuid | PK |
| collaborator_id | uuid | FK `collaborator` |
| training_plan_id | uuid | FK `training_plan` |
| assigned_by | uuid | FK `collaborator` (manager) |
| status | text | `ASSIGNED` \| `IN_PROGRESS` \| `COMPLETED` \| `CANCELLED` |
| assigned_at | timestamptz | |
| target_date | date | |

---

## Métricas derivadas (definiciones para reporting)

### A) Capacidades certificadas (snapshot)

- Por `certification_record` con `status in (ACTIVE, VALIDATED)` y `expiration_date` futura (o null si no aplica).
- Agrupable por: vendor, categoría, nivel, unidad, rol profesional.

### B) Riesgo

**Riesgo por certificación (interno)** (ejemplo de score 0-100):
- +50 si `EXPIRED`
- +30 si `EXPIRING_SOON` (ventana configurable: 60/90 días)
- +20 si cobertura obligatoria < umbral (por rol/unidad)
- +10 si hay alta dependencia en pocos colaboradores (concentración)

**Riesgo por mercado**:
- +30 si `market_status = DECLINING`
- +60 si `market_status = SUNSET`
- + (obsolescence_risk * 0.4)

> El score final debe documentarse y versionarse. El agente debe explicar “por qué” con desglose.

### C) Credenciales perdiendo vigencia

- Basado en `certification_market_signal.market_status` y `demand_score`.
- Se considera “en pérdida” si:
  - `market_status in (DECLINING, SUNSET)` OR
  - `demand_score < umbral` y/o `obsolescence_risk > umbral`.
- Debe incluir alternativas desde `certification_replacement_map`.

### D) Skills faltantes para vender/deliver

- Demanda: `delivery_capability_requirement` (headcount requerido por skill/rol/unidad).
- Oferta: conteo de colaboradores con skills inferidos por certificaciones activas (via `certification_skill_map`) o skills declarados (si existiera tabla de self-assessment futuro).
- Brecha = requerido - disponible (>=0).

### E) Inversión y recomendación de renovación

Requiere capturar **costos** y/o **horas**.

Propuesta mínima:
- Agregar `training_cost` (por certificación/curso) como referencia.
- Registrar “gasto real” en una tabla de hechos (si hay integración) o manual.

**Recomendación de renovación** (heurística explicable):
- Renovar si: certificación es requerida para rol/servicio y mercado `GROWING/STABLE` y costo razonable vs impacto.
- Migrar si: mercado `DECLINING/SUNSET` y existe reemplazo `HIGH`.
- No renovar si: baja demanda + no requerida + costo alto.

---

## Consideraciones de seguridad / compliance

- `certification_market_signal` y `training_plan` pueden ser “no PII” y aptos para knowledge base.
- `collaborator_training_plan` y costos por persona son sensibles (mínimo privilegio + auditoría).
- El agente **no debe**:
  - exponer emails/employee_number,
  - listar credenciales personales,
  - inferir performance laboral.

---

## Backlog de implementación (documental y técnico)

1. Definir taxonomía cerrada para:
   - `market_status`, `replacement_type`, `collaborator_category`, `expertise_area`.
2. Crear archivos de referencia en `data/reference/` (CSV) para:
   - `certification_market_signals.csv`
   - `certification_replacements.csv`
   - `skills.csv`
   - `certification_skill_map.csv`
   - `training_plans.csv`
   - `training_plan_items.csv`
3. Actualizar procesos y reporting para usar estas referencias.
4. Actualizar prompts del agente para:
   - explicar criterios de mercado,
   - proponer reemplazos,
   - armar plan de formación por categoría/área (sin PII, salvo que el usuario esté autorizado y el tool lo permita).
