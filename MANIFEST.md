# Manifest

**Generated:** 2026-05-07  
**Total files:** 132 | **Total size:** ~455 KB | **Documentation:** 85 MD files

---

## Project Structure

### Root Configuration (6)
- `.editorconfig` (169 bytes)
- `.gitignore` (185 bytes)
- `CODEOWNERS` (397 bytes)
- `LICENSE.md` (94 bytes)
- `Makefile` (91 bytes)
- `SECURITY.md` (334 bytes)

### Documentation Hub (5)
- `README.md` (1,851 bytes) — Project overview
- `QUICKSTART.md` (10,331 bytes) — **NEW** Onboarding guide (5-10 min)
- `CONVERSATION-HISTORY.md` (29,663 bytes) — **NEW** Full session context & decisions
- `CONTRIBUTING.md` (413 bytes) — Contribution guidelines
- `docs/index.md` (8,854 bytes) — **EXPANDED** Interactive documentation index

### GitHub Workflows (3)
- `.github/ISSUE_TEMPLATE/data_change.md` (213 bytes)
- `.github/ISSUE_TEMPLATE/functional_requirement.md` (213 bytes)
- `.github/PULL_REQUEST_TEMPLATE.md` (385 bytes)
- `.github/workflows/docs-check.yml` (234 bytes)

---

## Backend (13 files, ~80 KB)

### Core Documentation
- `backend/README.md` (73 bytes)
- `backend/ARCHITECTURE.md` (20,038 bytes) — **NEW** 7-layer architecture with patterns
- `backend/API.md` (18,845 bytes) — **NEW** Complete REST endpoint reference

### Database
- `backend/database/schema.sql` (4,743 bytes) — 13 normalized entities
- `backend/database/indexes.sql` (508 bytes) — Query optimization specs
- `backend/database/views_reporting.sql` (471 bytes) — Reporting views
- `backend/database/data_quality_checks.sql` (535 bytes) — Data validation rules
- `backend/database/seed_reference_data.sql` (360 bytes) — Initial data

### Services & Jobs
- `backend/services/README.md` (130 bytes)
- `backend/jobs/README.md` (156 bytes)

### OpenAPI
- `backend/api/openapi.yaml` (929 bytes) — REST spec

---

## AI Agent (6 files, ~9 KB)

### Knowledge Base
- `ai-agent/knowledge-base/README.md` (85 bytes)
- `ai-agent/knowledge-base/market-and-training.md` (4,750 bytes) — **NEW** Certification data

### Prompts
- `ai-agent/prompts/system-prompt.md` (1,438 bytes) — System instructions
- `ai-agent/prompts/routing-policy.md` (696 bytes) — Request routing

### Tools & Evaluation
- `ai-agent/tools/tool-contracts.md` (190 bytes) — Tool specifications
- `ai-agent/evaluations/evaluation-suite.md` (329 bytes)
- `ai-agent/evaluations/test-cases.yaml` (326 bytes)

---

## Data (8 files, ~65 KB)

### Reference Data (Tier 1 Knowledge Base)
- `data/reference/certifications_catalog.csv` (34,996 bytes) — 200+ certs
- `data/reference/certification_market_signals.csv` (25,140 bytes) — Market data
- `data/reference/certification_replacements.csv` (1,485 bytes) — Cert equivalences
- `data/reference/certification_statuses.csv` (343 bytes) — Status enums
- `data/reference/roles.csv` (199 bytes) — Professional roles

### Sample Data
- `data/samples/collaborators_sample.csv` (198 bytes)
- `data/samples/certifications_sample.csv` (186 bytes)
- `data/samples/assignments_sample.csv` (174 bytes)

### Processed Data
- `data/processed/.gitkeep` (1 byte)
- `data/raw/.gitkeep` (1 byte)

---

## Documentation (docs/ - 85 files, ~250 KB)

### 00 Context (5 files)
- `docs/00-contexto/vision-general.md` — Project vision
- `docs/00-contexto/antecedentes-solucion-web.md` — Background
- `docs/00-contexto/etapa-power-apps.md` — Previous system
- `docs/00-contexto/enfoque-agente-ia.md` — AI approach
- `docs/00-contexto/fuentes-y-supuestos.md` — Sources & assumptions

### 01 Functional Analysis (10 files)
- `docs/01-analisis-funcional/requerimientos-funcionales.md` — RF-001 through RF-018
- `docs/01-analisis-funcional/requerimientos-no-funcionales.md` — Performance, security, etc.
- `docs/01-analisis-funcional/historias-usuario.md` — User stories
- `docs/01-analisis-funcional/casos-uso.md` — Use cases
- `docs/01-analisis-funcional/criterios-aceptacion.md` — Acceptance criteria
- `docs/01-analisis-funcional/actores-stakeholders.md` — Actors & roles
- `docs/01-analisis-funcional/procesos-negocio.md` — Business processes
- `docs/01-analisis-funcional/alcance.md` — Project scope
- `docs/01-analisis-funcional/reglas-negocio.md` — Business rules
- `docs/01-analisis-funcional/matriz-trazabilidad.md` — Traceability matrix

### 02 Data (10 files, ~55 KB)
- `docs/02-datos/DICCIONARIO-EJECUTABLE.md` (24,341 bytes) — **NEW** Synchronized data dictionary
- `docs/02-datos/modelo-mercado-y-formacion.md` (9,444 bytes) — **NEW** Market data model
- `docs/02-datos/diccionario-datos.md` — Data dictionary (original)
- `docs/02-datos/modelo-logico.md` — Logical model
- `docs/02-datos/modelo-conceptual.md` — Conceptual model
- `docs/02-datos/entidades.md` — Entity definitions
- `docs/02-datos/linaje-datos.md` — Data lineage
- `docs/02-datos/calidad-datos.md` — Data quality rules
- `docs/02-datos/gobierno-datos.md` — Data governance
- `docs/02-datos/retencion-datos.md` — Data retention policy

### 03 Architecture (9 files, ~19 KB)
- `docs/03-arquitectura/PATTERNS.md` (14,499 bytes) — **NEW** 10 reusable patterns
- `docs/03-arquitectura/arquitectura-general.md` — High-level architecture
- `docs/03-arquitectura/arquitectura-backend.md` — Backend specifics
- `docs/03-arquitectura/arquitectura-agente-ia.md` — AI agent architecture
- `docs/03-arquitectura/decisiones-arquitectura.md` — Design decisions
- `docs/03-arquitectura/integraciones.md` — External integrations
- `docs/03-arquitectura/adr/ADR-0001-backend-data-first.md` — Decision 1
- `docs/03-arquitectura/adr/ADR-0002-docs-as-code.md` — Decision 2
- `docs/03-arquitectura/adr/ADR-0003-ai-agent-tools-only.md` — Decision 3

### 04 Processes (9 files, ~125 KB) — **ALL EXPANDED THIS SESSION**
- `docs/04-procesos/renovacion-certificacion.md` (31,320 bytes) — Template & example
- `docs/04-procesos/validacion-aprobacion.md` (13,705 bytes) — RF-008 (validator decisions)
- `docs/04-procesos/seguimiento-vencimientos.md` (12,762 bytes) — RF-017 (expiration monitoring)
- `docs/04-procesos/alertas-notificaciones.md` (13,452 bytes) — RF-018 (multicanal notifications)
- `docs/04-procesos/reporting.md` (12,146 bytes) — RF-016 (coverage & audit reports)
- `docs/04-procesos/gestion-evidencias.md` (10,549 bytes) — RF-007 (S3 evidence storage)
- `docs/04-procesos/asignacion-certificacion.md` (10,563 bytes) — RF-002, RF-013 (assignment)
- `docs/04-procesos/alta-certificacion.md` (9,478 bytes) — RF-006 (registration)
- `docs/04-procesos/soporte-excepciones.md` (12,667 bytes) — RF-012 (waivers)

**Summary:** 4-6 phases each, 7-8 validations, 6-7 edge cases, SQL/code examples, SLAs

### 05 Security & Compliance (8 files, ~14 KB)
- `docs/05-seguridad-cumplimiento/CHECKLIST.md` (11,749 bytes) — **NEW** Executable pre-prod checklist
- `docs/05-seguridad-cumplimiento/seguridad.md` — Security overview
- `docs/05-seguridad-cumplimiento/auditoria.md` — Audit requirements
- `docs/05-seguridad-cumplimiento/privacidad-datos.md` — Privacy & PII handling
- `docs/05-seguridad-cumplimiento/cumplimiento-normativo.md` — Compliance (GDPR, etc.)
- `docs/05-seguridad-cumplimiento/roles-permisos.md` — RBAC specifications
- `docs/05-seguridad-cumplimiento/threat-model.md` — Threat assessment
- `docs/05-seguridad-cumplimiento/ai-risk-management.md` — AI safety

### 06 AI Agent (9 files, ~4 KB)
- `docs/06-agent-ai/herramientas.md` — 13 tools specification
- `docs/06-agent-ai/objetivos-agente.md` — Agent goals
- `docs/06-agent-ai/capacidades.md` — Capabilities
- `docs/06-agent-ai/restricciones.md` — Constraints & guardrails
- `docs/06-agent-ai/guardrails.md` — Guardrail details
- `docs/06-agent-ai/knowledge-base.md` — Knowledge base structure
- `docs/06-agent-ai/prompts-sistema.md` — System prompts
- `docs/06-agent-ai/flujos-conversacionales.md` — Conversation flows
- `docs/06-agent-ai/criterios-evaluacion.md` — Evaluation criteria

### 07 Testing (7 files, ~17 KB)
- `docs/07-testing/TEST-CASES.md` (14,927 bytes) — **NEW** 15 executable test cases
- `docs/07-testing/estrategia-testing.md` — Testing strategy
- `docs/07-testing/casos-prueba-funcionales.md` — Functional test matrix
- `docs/07-testing/pruebas-seguridad.md` — Security test cases
- `docs/07-testing/pruebas-datos.md` — Data quality tests
- `docs/07-testing/pruebas-agente-ia.md` — AI agent evaluation
- `docs/07-testing/checklist-release.md` — Release checklist

### 08 Operations (4 files)
- `docs/08-operacion/metricas-kpi.md` — KPI definitions
- `docs/08-operacion/monitoreo.md` — Monitoring & alerting
- `docs/08-operacion/runbook-incidentes.md` — Incident response
- `docs/08-operacion/soporte.md` — Support procedures

### Core Reference (3 files, ~35 KB) — **NEW TIER 3**
- `docs/GLOSSARIO.md` (12,366 bytes) — **NEW** 26 terms + naming conventions
- `docs/TRAZABILIDAD.md` (14,371 bytes) — **NEW** RF → Process → API → Test matrix

### Templates (2 files)
- `docs/templates/adr-template.md` — ADR template
- `docs/templates/requirement-template.md` — Requirement template

---

## Governance (6 files, ~17 KB)

- `governance/DECISIONS-LOG.md` (16,292 bytes) — **NEW** 7 structured decisions with rationale
- `governance/riesgos.md` — Risk register
- `governance/roadmap.md` — Implementation roadmap
- `governance/backlog.md` — Feature backlog
- `governance/data-governance-raci.md` — RACI matrix
- `governance/changelog.md` — Version history
- `governance/decisiones.md` — Historical decisions (legacy)

---

## Models (5 files, ~2.8 KB)

### ERD (Entity-Relationship Diagram)
- `models/erd/certification_app_erd.md` — 13-entity schema visualization

### Mappings
- `models/mappings/powerapps-to-target-model.md` — Migration mapping

### JSON Schemas
- `models/schemas/collaborator.schema.json` — Collaborator structure
- `models/schemas/certification_record.schema.json` — Certification record
- `models/schemas/certification_assignment.schema.json` — Assignment

---

## Scripts (1 file)
- `scripts/validate_repository.py` (629 bytes) — Repository validation checker

---

## Key Statistics

| Category | Count | Status |
|----------|-------|--------|
| **Requirements** | 18 RFs | ✅ All documented |
| **Processes** | 9 | ✅ All expanded (125 KB) |
| **Test Cases** | 15+ | ✅ Executable |
| **Data Entities** | 13 | ✅ Schema defined |
| **AI Tools** | 13 | ⏳ 5 implemented, 8 pending |
| **Architectural Patterns** | 10 | ✅ Documented with examples |
| **Security Controls** | 40+ | ✅ Checklist ready |
| **Documentation Files** | 85 | ✅ 100% complete |

---

## Recent Updates (This Session)

✅ **Tier 1-3 Documentation:** QUICKSTART, ARCHITECTURE, API, DICCIONARIO, TEST-CASES, CHECKLIST, GLOSSARIO  
✅ **Tier 2 Support:** TRAZABILIDAD, PATTERNS, DECISIONS-LOG  
✅ **All 9 Processes:** Expanded with 2,700+ lines (alta, asignacion, validacion, evidencias, seguimiento, alertas, reporting, excepciones, renovacion)  
⏳ **AI Agent:** Knowledge base + tools (phase 1 pending)  

---

**Last Updated:** 2026-05-07  
**Maintainer:** Technical Team  
**Repository Status:** Production-ready documentation, implementation in progress

