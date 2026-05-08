# Quick Start Guide

Guía de 5-10 minutos para clonar, validar y contribuir al proyecto.

## Requisitos Previos

- **Git** 2.30+
- **Python** 3.9+
- **Make** (opcional, para comandos simplificados)

## 1. Clonar el Repositorio

```bash
git clone https://github.com/nttdata-emeal/certification-app.git
cd certification-app
```

## 2. Validar la Estructura

Verifica que el repositorio está completo y bien formado:

```bash
# Usando Make (si está disponible)
make validate

# O directamente con Python
python scripts/validate_repository.py
```

**Salida esperada:**
```
Repository structure validation passed.
```

Si falla, revisa que existan estos archivos clave:
- `README.md`
- `docs/index.md`
- `docs/01-analisis-funcional/requerimientos-funcionales.md`
- `docs/02-datos/modelo-logico.md`
- `backend/database/schema.sql`
- `backend/api/openapi.yaml`

## 3. Explorar la Documentación

### Para Entender el Proyecto (10 min)
1. Lee `docs/index.md` - visión general de carpetas
2. Lee `docs/00-contexto/vision-general.md` - contexto y evolución
3. Lee `README.md` - objetivos y principios

### Para Contribuir Código (20 min)
4. Lee `docs/01-analisis-funcional/requerimientos-funcionales.md` - qué se espera
5. Lee `docs/02-datos/modelo-logico.md` - estructura de datos
6. Lee `docs/03-arquitectura/arquitectura-general.md` - cómo se organiza
7. Lee `CONTRIBUTING.md` - reglas de contribución

### Para Trabajar con el Backend (15 min)
8. Lee `backend/ARCHITECTURE.md` - patrones técnicos
9. Lee `backend/API.md` - endpoints disponibles
10. Explora `backend/database/schema.sql` - tablas y relaciones

### Para el Agente IA (15 min)
11. Lee `docs/06-agent-ai/objetivos-agente.md` - capacidades y restricciones
12. Lee `ai-agent/prompts/system-prompt.md` - instrucciones del agente

### Para Seguridad y Operación (10 min)
13. Lee `docs/05-seguridad-cumplimiento/seguridad.md` - controles de seguridad
14. Lee `docs/08-operacion/runbook-incidentes.md` - procedimientos operativos

## 4. Estructura Principal

```
certification-app/
├── docs/                 # Análisis, arquitectura, procesos, seguridad
│   ├── 00-contexto/
│   ├── 01-analisis-funcional/
│   ├── 02-datos/
│   ├── 03-arquitectura/
│   ├── 04-procesos/
│   ├── 05-seguridad-cumplimiento/
│   ├── 06-agent-ai/
│   ├── 07-testing/
│   └── 08-operacion/
│
├── backend/              # Contratos API, SQL, servicios
│   ├── api/openapi.yaml  # Especificación de endpoints
│   ├── database/         # Scripts SQL
│   ├── services/         # Lógica de negocio
│   └── jobs/             # Procesos batch
│
├── ai-agent/             # Prompts, tools, knowledge base
│   ├── prompts/
│   ├── tools/
│   ├── knowledge-base/
│   └── evaluations/
│
├── models/               # Esquemas y ERD
│   ├── schemas/          # JSON schemas
│   ├── erd/              # Modelo entidad-relación
│   └── mappings/         # Migraciones
│
├── data/                 # Datos de referencia y muestras
│   ├── reference/        # Catálogos estáticos
│   ├── samples/          # Datos de prueba anonimizados
│   └── processed/        # Resultados de procesamiento
│
├── governance/           # Decisiones, riesgos, roadmap
│
├── .github/              # Plantillas y workflows
│
└── scripts/              # Utilidades (validación, etc.)
```

## 5. Primeros Pasos para Contribuir

### Flujo de Cambios

1. **Crea una rama** desde `main`:
   ```bash
   git checkout -b feature/mi-feature
   ```

2. **Haz cambios** en documentación o código:
   - Si es funcional: actualiza `docs/01-analisis-funcional/`
   - Si es datos/modelo: actualiza `docs/02-datos/`, `models/` y `backend/database/`
   - Si es agente IA: actualiza `docs/06-agent-ai/` y `ai-agent/evaluations/`
   - Si es arquitectura: crea o actualiza ADR en `docs/03-arquitectura/adr/`

3. **Valida la estructura**:
   ```bash
   make validate
   ```

4. **Commit con mensaje claro**:
   ```bash
   git commit -m "feature: descripción de cambio"
   ```

5. **Push y crea Pull Request**:
   ```bash
   git push origin feature/mi-feature
   ```

Ver detalles en [CONTRIBUTING.md](CONTRIBUTING.md).

## 6. Comandos Útiles

```bash
# Validar estructura del repositorio
make validate

# Ver árbol de archivos (primeros 4 niveles)
make tree

# Contar documentación
find docs -name "*.md" | wc -l

# Listar procesos documentados
ls -la docs/04-procesos/

# Validar YAML de OpenAPI
# (requiere python-yaml)
python -m yaml backend/api/openapi.yaml
```

## 7. Preguntas Frecuentes

**¿Dónde veo qué hay que hacer?**
→ Ver `governance/backlog.md` y `governance/roadmap.md`

**¿Cómo documentar un nuevo proceso?**
→ Copiar `docs/templates/` y seguir el patrón en `docs/04-procesos/`

**¿Dónde reporto un bug o solicito cambio?**
→ Crear issue en GitHub usando plantillas en `.github/ISSUE_TEMPLATE/`

**¿Qué no debo subir?**
→ Datos reales, secretos, dumps de base datos. Ver `SECURITY.md`

**¿Cómo se toma una decisión arquitectónica?**
→ Crear ADR en `docs/03-arquitectura/adr/` usando `docs/templates/adr-template.md`

## 8. Recursos de Referencia

| Necesito... | Ir a... |
|-------------|---------|
| Entender un proceso | `docs/04-procesos/{nombre}.md` |
| Ver modelo de datos | `models/erd/certification_app_erd.md` |
| Consultar diccionario | `docs/02-datos/diccionario-datos.md` |
| Conocer esquemas JSON | `models/schemas/` |
| Revisar decisiones | `governance/decisiones.md` o `docs/03-arquitectura/adr/` |
| Ver APIs | `backend/API.md` |
| Entender seguridad | `docs/05-seguridad-cumplimiento/` |
| Operación y alertas | `docs/08-operacion/` |
| Conocer rol/permisos | `docs/05-seguridad-cumplimiento/roles-permisos.md` |

## 9. Stack Técnico (Baseline)

- **Backend**: API REST + Base de datos relacional (PostgreSQL 12+)
- **Database**: PostgreSQL con 13 tablas, constraints, índices
- **Authentication**: JWT Bearer tokens + OAuth/SSO compatible
- **Authorization**: RBAC (Role-Based Access Control) con 5 roles
- **Agente IA**: Conversacional con tool use (Claude/LLM compatible)
- **Documentación**: Markdown versionado (docs-as-code)
- **Infrastructure**: SQL scripts + OpenAPI 3.0.3 spec
- **Validation**: Python 3.9+, Bash, SQL

*Nota: Estos son baselines específicos. Revisar `docs/03-arquitectura/` para decisiones técnicas completas.*

## 10. Primeros Pasos Después de Setup

Una vez validado el repositorio:

### Opción A: Entender el Proyecto (Lectura)
```bash
# Ver documentación visual
cat docs/index.md          # Índice interactivo
cat CONVERSATION-HISTORY.md # Lo que se mejoró

# Ver arquitectura
cat docs/03-arquitectura/arquitectura-general.md
cat backend/ARCHITECTURE.md
```

### Opción B: Comenzar a Codificar (Desarrollo)
```bash
# 1. Setup del ambiente
git clone https://github.com/nttdata-emeal/certification-app.git
cd certification-app
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt  # (cuando exista)

# 2. Crear rama de feature
git checkout -b feature/my-feature main

# 3. Editar en tu IDE favorito
code .  # VSCode
pycharm .  # PyCharm

# 4. Validar cambios
make validate              # o: python scripts/validate_repository.py

# 5. Commitear
git add docs/...
git commit -m "feature: descripción"
git push origin feature/my-feature

# 6. Crear Pull Request
# En GitHub: New PR → describe cambios
```

### Opción C: Trabajar con Backend (SQL + API)
```bash
# Ver esquema de BD
cat backend/database/schema.sql

# Ver qué APIs tenemos
cat backend/API.md

# Explorar documentación de datos
cat docs/02-datos/DICCIONARIO-EJECUTABLE.md
```

### Opción D: Trabajar con Agente IA
```bash
# Revisar capacidades del agente
cat docs/06-agent-ai/objetivos-agente.md
cat docs/06-agent-ai/capacidades.md

# Ver herramientas disponibles
cat docs/06-agent-ai/herramientas.md

# Leer evaluación esperada
cat CONVERSATION-HISTORY.md | grep -A 50 "Validación Arquitectónica"
```

## 11. Troubleshooting y FAQs

### P: ¿Validación falla? ¿Qué archivos faltan?

**R:** El script chequea archivos clave. Verifica:
```bash
ls -la README.md
ls -la docs/index.md
ls -la docs/01-analisis-funcional/requerimientos-funcionales.md
ls -la backend/database/schema.sql
ls -la backend/api/openapi.yaml
```

Si faltan, descarga la última versión del repo.

### P: ¿Cómo contribuyo cambios?

**R:** Seguir flujo:
1. Fork o crear rama desde `main`
2. Editar documentación/código
3. `git commit` con mensaje claro
4. Push a rama
5. Pull Request con descripción
6. Review + merge

Ver `CONTRIBUTING.md` para reglas específicas.

### P: ¿Qué si no tengo Make?

**R:** Usa Python directamente:
```bash
python scripts/validate_repository.py
```

### P: ¿Dónde están los datos reales?

**R:** NO se suben datos reales al repo por seguridad:
- `data/reference/` - catálogos (públicos)
- `data/samples/` - datos anonimizados
- Datos personales → variables de ambiente

Ver `SECURITY.md` para reglas.

### P: ¿Cómo reporto un bug?

**R:** Usar GitHub Issues con plantilla:
```
Title: [BUG] Descripción breve
Type: bug
Severity: low/medium/high
Reproducción: Pasos para repetir
```

NO incluir datos personales. Ver `SECURITY.md`.

### P: ¿Necesito permisos especiales?

**R:** Para contribuir:
- ✅ Lectura de docs: sin permiso (público)
- ✅ Crear rama: cuéntale al manager
- ✅ Merge a main: requiere review (CODEOWNERS)
- ✅ Cambios a seguridad: revisor de seguridad

Ver `CODEOWNERS` para quién aprueba qué.

## 10. Siguiente Paso

¿Listo para contribuir? Revisa el tipo de cambio que quieres hacer:

- 📊 **Cambio de datos/modelo**: `docs/02-datos/` → `models/` → `backend/database/`
- 🔌 **Nuevo endpoint**: `backend/api/openapi.yaml` → `backend/services/` → documento proceso
- 🤖 **Mejora agente**: `ai-agent/prompts/` → `ai-agent/evaluations/` → `docs/06-agent-ai/`
- 📝 **Nuevo proceso**: `docs/04-procesos/` + actualizar `docs/index.md`
- 🏗️ **Decisión arquitectónica**: crear `docs/03-arquitectura/adr/ADR-NNNN-*.md`

**¿Preguntas?** Revisa `CONTRIBUTING.md` o contacta al CODEOWNERS del área.
