# Knowledge Base

## Objetivo

Proveer datos de referencia **aprobados y curados** al agente IA para responder consultas sobre:

- Credenciales perdiendo vigencia de mercado y recomendaciones de migración
- Brechas de skills por rol, unidad o proyecto
- Planes de formación personalizados por categoría y área de expertise

El agente IA utiliza esta base de conocimiento para:

1. Separar **hechos internos** (vencimientos, cobertura, requisitos) de **señales de mercado**
2. Fundamentar recomendaciones con datos aprobados y trazables
3. Responder sin exponer PII, secretos, evidencias ni dumps

---

## Contenido

### 1. `market-and-training.md` — Especificación técnica y contrato de datos

Define:

- Objetivo y alcance del Knowledge Base
- Fuentes permitidas (datos internos + tablas de referencia curadas)
- Taxonomías estándar (`market_status`, `replacement_type`, `collaborator_category`, etc.)
- Reglas obligatorias para respuestas del agente IA
- **Estructura esperada de 6 tablas de referencia** (CSVs):
  - `certification_market_signals.csv` — señales de mercado por certificación
  - `certification_replacements.csv` — mapeo de reemplazos/alternativas
  - `skills.csv` — catálogo de skills
  - `certification_skill_map.csv` — qué skills cubre cada certificación
  - `training_plans.csv` — planes de formación por categoría/área
  - `training_plan_items.csv` — items de cada plan

**Por qué:** Garantiza consistencia y confiabilidad en respuestas del agente. Toda recomendación debe fundamentarse en datos aprobados por CERTIFICATION_OWNER.

---

### 2. `certifications-metadata.csv` — Catálogo de ~80 certificaciones con metadatos de mercado

Campos clave:

- `certification_name`, `provider` (AWS, GCP, Azure, Databricks, Snowflake, etc.)
- `level` (Foundational, Associate, Professional, Specialty, etc.)
- `focus_area` (Data, AI/GenAI, Cloud, Security, etc.)
- `market_demand` (high, moderate, low)
- `is_trending` (True/False)
- `validity_months`, `renewal_pattern` (1-3 años típicamente)
- `status` (Activa, Retira fecha)

**Por qué:** Fuente de verdad para:

- Detectar certificaciones con demanda baja o en retiro
- Calcular brechas de skills disponibles en el mercado
- Informar planes de formación según tendencias

---

### 3. `roles-cert-map.csv` — Mapeo de 10+ roles a sus requisitos de certificación

Estructura:

- `role_name` (Cloud Architect, Data Engineer, ML Engineer, etc.)
- `primary_focus` (área de responsabilidad)
- `required_certs` (certificaciones obligatorias por rol)
- `recommended_certs` (alternativas o ampliación)
- `level_range` (Intermediate, Professional, Advanced)
- `renewal_frequency` (Annual, Biennial)

**Por qué:**

- Permite al agente identificar qué certificaciones son críticas por rol
- Establece baseline de requisitos para skill gaps
- Guía recomendaciones de formación según carrera/especialización

---

### 4. `processes-summary.csv` — Resumen de 9 procesos principales del sistema

Procesos cubiertos:

| Proceso | Descripción | Trigger |
| --- | --- | --- |
| P001: Alta Certificación | Collaborator registra nueva cert | Obtiene certificación |
| P002: Asignación | Manager asigna cert a equipo | Necesidad operacional |
| P003: Validación | Validator revisa evidencias | Record pending |
| P004: Gestión Evidencias | Carga y almacenamiento seguro | Upload por collaborator |
| P005: Seguimiento Vencimientos | Detección automática de expiración | Batch nightly |
| P006: Alertas | Notificaciones por evento | Cualquier proceso |
| P007: Reporting | Consultas y exportes | On-demand / scheduled |
| P008: Soporte Excepciones | Waivers y excepciones | Manager solicita |
| P009: Renovación | Ciclo de renovación automática | Cert approaching expiry |

**Por qué:**

- Contextualiza cómo el Knowledge Base se integra en los flujos operacionales
- El agente IA usa estos datos para responder sobre estado y acciones disponibles
- Referencia para SLA, escalaciones y decisión points

---

## Principios de Seguridad

✅ **Permitido:**

- Datos agregados sin identificación (ej: "50 collaborators con AWS ML Specialty")
- Señales de mercado curadas (demanda, obsolescence, tendencias)
- Planes de formación genéricos por categoría/área
- Metadata de certificaciones y mapa de reemplazos

❌ **No permitido:**

- PII (nombres, correos de colaboradores)
- Secretos (claves API, credenciales de test)
- Evidencias originales (screenshots, PDFs de exámenes)
- Dumps de bases de datos sin filtrado

---

## Flujo de Actualización

1. **Owner (CERTIFICATION_OWNER)** identifica cambios en mercado o cobertura interna
2. **Dueños de práctica** validan señales de mercado y reemplazos recomendados
3. **CSV actualizado** → validación de schema y retrocompatibilidad
4. **market-and-training.md** refleja nuevas taxonomías o reglas
5. **Agente IA** usa datos nuevos en siguiente sesión

---

## Relación con Otros Componentes

- **tools/** — Herramientas del agente IA que consultan estas tablas
- **contracts/** — Esquemas y validaciones de datos
- **tests/** — Casos de prueba que verifican consistencia de Knowledge Base
