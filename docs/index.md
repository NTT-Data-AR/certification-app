# Índice de Documentación

## 🚀 Inicio Rápido (Recomendado para Nuevos Devs)

1. [QUICKSTART.md](../QUICKSTART.md) - Guía 5-10 min para clonar, validar y contribuir
2. [README.md](../README.md) - Visión general y principios del proyecto
3. [00-contexto/vision-general.md](00-contexto/vision-general.md) - Evolución de la solución

## 📚 Documentación Técnica

### Backend y Arquitectura
- [backend/ARCHITECTURE.md](../backend/ARCHITECTURE.md) - ⭐ Especificación técnica de capas, transacciones, patrones
- [backend/API.md](../backend/API.md) - ⭐ Referencia completa de endpoints REST con ejemplos
- [03-arquitectura/arquitectura-general.md](03-arquitectura/arquitectura-general.md) - Diagrama general
- [03-arquitectura/arquitectura-backend.md](03-arquitectura/arquitectura-backend.md) - Componentes del backend

### Datos y Modelo
- [02-datos/DICCIONARIO-EJECUTABLE.md](02-datos/DICCIONARIO-EJECUTABLE.md) - ⭐ Diccionario completo (13 entidades, tipos, validaciones, ejemplos JSON)
- [02-datos/modelo-logico.md](02-datos/modelo-logico.md) - Principios y entidades
- [02-datos/modelo-conceptual.md](02-datos/modelo-conceptual.md) - Conceptos del dominio
- [02-datos/diccionario-datos.md](02-datos/diccionario-datos.md) - Definiciones de campos

## 📋 Análisis Funcional

- [01-analisis-funcional/alcance.md](01-analisis-funcional/alcance.md) - Qué incluye y excluye
- [01-analisis-funcional/actores-stakeholders.md](01-analisis-funcional/actores-stakeholders.md) - Roles y RACI
- [01-analisis-funcional/requerimientos-funcionales.md](01-analisis-funcional/requerimientos-funcionales.md) - 20 RF priorizados
- [01-analisis-funcional/requerimientos-no-funcionales.md](01-analisis-funcional/requerimientos-no-funcionales.md) - Performance, escalabilidad, etc
- [01-analisis-funcional/procesos-negocio.md](01-analisis-funcional/procesos-negocio.md) - Mapa de procesos

## ⚙️ Procesos Operativos

- [04-procesos/renovacion-certificacion.md](04-procesos/renovacion-certificacion.md) - ⭐ EJEMPLO DETALLADO: Renovación (4 fases, validaciones, excepciones)
- [04-procesos/alta-certificacion.md](04-procesos/alta-certificacion.md) - Crear nuevo registro
- [04-procesos/asignacion-certificacion.md](04-procesos/asignacion-certificacion.md) - Asignar a colaborador
- [04-procesos/validacion-aprobacion.md](04-procesos/validacion-aprobacion.md) - Validar evidencia
- [04-procesos/gestion-evidencias.md](04-procesos/gestion-evidencias.md) - Cargar y almacenar
- [04-procesos/seguimiento-vencimientos.md](04-procesos/seguimiento-vencimientos.md) - Alertas
- [04-procesos/reporting.md](04-procesos/reporting.md) - Indicadores y exportes
- [04-procesos/soporte-excepciones.md](04-procesos/soporte-excepciones.md) - Waivers y excepciones
- [04-procesos/alertas-notificaciones.md](04-procesos/alertas-notificaciones.md) - Sistema de alertas

## 🤖 Agente IA

- [06-agent-ai/objetivos-agente.md](06-agent-ai/objetivos-agente.md) - Qué debe lograr
- [06-agent-ai/capacidades.md](06-agent-ai/capacidades.md) - Qué puede hacer
- [06-agent-ai/restricciones.md](06-agent-ai/restricciones.md) - Qué NO puede hacer
- [06-agent-ai/prompts-sistema.md](06-agent-ai/prompts-sistema.md) - Instrucciones del agente
- [06-agent-ai/herramientas.md](06-agent-ai/herramientas.md) - 13 Tools disponibles
- [06-agent-ai/guardrails.md](06-agent-ai/guardrails.md) - Controles de seguridad
- [06-agent-ai/flujos-conversacionales.md](06-agent-ai/flujos-conversacionales.md) - Ejemplos de conversaciones
- [06-agent-ai/criterios-evaluacion.md](06-agent-ai/criterios-evaluacion.md) - Cómo validar
- [06-agent-ai/conocimiento-base.md](06-agent-ai/knowledge-base.md) - Datos aprobados

## 🔒 Seguridad y Cumplimiento

- [05-seguridad-cumplimiento/seguridad.md](05-seguridad-cumplimiento/seguridad.md) - Principios y controles
- [05-seguridad-cumplimiento/roles-permisos.md](05-seguridad-cumplimiento/roles-permisos.md) - RBAC
- [05-seguridad-cumplimiento/auditoria.md](05-seguridad-cumplimiento/auditoria.md) - Trazabilidad
- [05-seguridad-cumplimiento/privacidad-datos.md](05-seguridad-cumplimiento/privacidad-datos.md) - GDPR, PII
- [05-seguridad-cumplimiento/cumplimiento-normativo.md](05-seguridad-cumplimiento/cumplimiento-normativo.md) - Regulaciones
- [05-seguridad-cumplimiento/threat-model.md](05-seguridad-cumplimiento/threat-model.md) - Amenazas
- [05-seguridad-cumplimiento/ai-risk-management.md](05-seguridad-cumplimiento/ai-risk-management.md) - Riesgos del agente IA

## 🧪 Testing

- [07-testing/estrategia-testing.md](07-testing/estrategia-testing.md) - Niveles y enfoque
- [07-testing/casos-prueba-funcionales.md](07-testing/casos-prueba-funcionales.md) - E2E
- [07-testing/pruebas-datos.md](07-testing/pruebas-datos.md) - Calidad y migraciones
- [07-testing/pruebas-seguridad.md](07-testing/pruebas-seguridad.md) - Validación de controles
- [07-testing/pruebas-agente-ia.md](07-testing/pruebas-agente-ia.md) - Evaluación del agente
- [07-testing/checklist-release.md](07-testing/checklist-release.md) - Antes de producción

## 📊 Operación

- [08-operacion/monitoreo.md](08-operacion/monitoreo.md) - Métricas y dashboards
- [08-operacion/metricas-kpi.md](08-operacion/metricas-kpi.md) - KPIs del negocio
- [08-operacion/runbook-incidentes.md](08-operacion/runbook-incidentes.md) - Cómo responder
- [08-operacion/soporte.md](08-operacion/soporte.md) - Procesos de soporte

## 📖 Contexto Histórico

- [00-contexto/antecedentes-solucion-web.md](00-contexto/antecedentes-solucion-web.md) - Solución web original
- [00-contexto/etapa-power-apps.md](00-contexto/etapa-power-apps.md) - Migración a Power Apps
- [00-contexto/enfoque-agente-ia.md](00-contexto/enfoque-agente-ia.md) - Visión del agente IA
- [00-contexto/fuentes-y-supuestos.md](00-contexto/fuentes-y-supuestos.md) - Bases del análisis

## 🏗️ Arquitectura y Decisiones

- [03-arquitectura/decisiones-arquitectura.md](03-arquitectura/decisiones-arquitectura.md) - Qué y por qué
- [03-arquitectura/adr/](03-arquitectura/adr/) - Architecture Decision Records
  - [ADR-0001-backend-data-first.md](03-arquitectura/adr/ADR-0001-backend-data-first.md) - Data-first architecture
  - [ADR-0002-docs-as-code.md](03-arquitectura/adr/ADR-0002-docs-as-code.md) - Documentación versionada
  - [ADR-0003-ai-agent-tools-only.md](03-arquitectura/adr/ADR-0003-ai-agent-tools-only.md) - Solo tools, sin SQL
- [03-arquitectura/integraciones.md](03-arquitectura/integraciones.md) - HR, Power Apps, Reporting

## 📝 Otros Recursos

- [CONVERSATION-HISTORY.md](../CONVERSATION-HISTORY.md) - Historial completo de mejoras realizadas
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Cómo contribuir
- [QUICKSTART.md](../QUICKSTART.md) - Setup inicial
- [templates/adr-template.md](templates/adr-template.md) - Crear nuevo ADR
- [templates/requirement-template.md](templates/requirement-template.md) - Template de requerimiento

## 🎯 Atajos por Rol

### Para Desarrollador Backend
1. QUICKSTART.md
2. backend/ARCHITECTURE.md
3. backend/API.md
4. docs/02-datos/DICCIONARIO-EJECUTABLE.md
5. Procesos (ej: 04-procesos/renovacion-certificacion.md)

### Para Desarrollador Frontend
1. QUICKSTART.md
2. backend/API.md (endpoints)
3. 04-procesos/ (flujos)
4. docs/06-agent-ai/flujos-conversacionales.md

### Para Especialista de IA
1. docs/06-agent-ai/ (todos)
2. backend/API.md (tools disponibles)
3. docs/02-datos/DICCIONARIO-EJECUTABLE.md (datos)
4. CONVERSATION-HISTORY.md (gaps identificados)

### Para Architect
1. docs/03-arquitectura/ (todos)
2. backend/ARCHITECTURE.md
3. CONVERSATION-HISTORY.md (validación)
4. docs/05-seguridad-cumplimiento/ (todos)

### Para QA/Testing
1. docs/07-testing/ (todos)
2. 04-procesos/ (casos de prueba)
3. CONVERSATION-HISTORY.md (test strategy)

---

## 📌 Documentos Esenciales (⭐)

Estos 5 documentos te dan 80% de contexto:

1. **QUICKSTART.md** - Cómo empezar
2. **backend/ARCHITECTURE.md** - Cómo funciona técnicamente
3. **backend/API.md** - Qué puedes llamar
4. **docs/02-datos/DICCIONARIO-EJECUTABLE.md** - Qué son los datos
5. **CONVERSATION-HISTORY.md** - Qué se mejoró y por qué

---

## 🔄 Sincronización y Validación

Para asegurar que documentación + código + tests estén sincronizados:

```bash
# Validar estructura
python scripts/validate_repository.py

# Buscar TODOs y gaps
grep -r "TODO\|FIXME\|XXX\|BRECHA" docs/

# Contar líneas por sección
find docs -name "*.md" | xargs wc -l | sort -n | tail -10
```

---

## 📅 Changelog

- **2026-05-07:** Creados documentos Tier 1 (QUICKSTART, ARCHITECTURE, API, DICCIONARIO, renovacion detallado)
- **2026-05-07:** Creado CONVERSATION-HISTORY.md con historial completo
- **2026-05-07:** Expandido este índice con navegación por rol

---

**Última actualización:** 2026-05-07  
**Mantenedor:** Equipo de Documentación  
**Estado:** Baseline listo para revisión
