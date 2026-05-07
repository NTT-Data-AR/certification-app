# Certification App

Baseline de repositorio para evolucionar la gestion de certificaciones de colaboradores NTT DATA desde una solucion web y una etapa Power Apps hacia una solucion gobernada por backend de datos y asistida por un agente de IA.

## Objetivo

Construir una base funcional, tecnica y de datos lista para trabajar en GitHub: procesos documentados en Markdown, modelo de datos canonico, contratos API, seguridad, cumplimiento, gobierno, backlog y evaluacion del agente.

## Principios

- Data-first: la base de datos es la fuente de verdad.
- API-first: UI, reporting y agente acceden por servicios controlados.
- Human-in-the-loop: el agente no aprueba ni ejecuta acciones criticas sin confirmacion o rol autorizado.
- Security by design: minimo privilegio, auditoria, privacidad y segregacion de funciones.
- Docs as code: toda decision, proceso y regla se versiona en Markdown.

## Estructura

```text
certification-app/
|-- docs/          Analisis funcional, datos, arquitectura, procesos, seguridad, IA, testing y operacion
|-- backend/       Contratos API y scripts SQL
|-- ai-agent/      Prompts, tools, knowledge base y evaluaciones
|-- models/        ERD, JSON schemas y mappings de migracion
|-- data/          Datos de referencia y muestras anonimizadas
|-- governance/    Riesgos, decisiones, backlog y roadmap
|-- .github/       Plantillas y workflow inicial
```

## Lectura inicial

1. `docs/index.md`
2. `docs/00-contexto/vision-general.md`
3. `docs/01-analisis-funcional/requerimientos-funcionales.md`
4. `docs/02-datos/modelo-logico.md`
5. `models/erd/certification_app_erd.md`
6. `docs/06-agent-ai/objetivos-agente.md`
7. `docs/05-seguridad-cumplimiento/seguridad.md`

## Estado

- Generado: 2026-05-07
- Estado: baseline inicial para revision y refinamiento
- Validacion local: `python scripts/validate_repository.py`
