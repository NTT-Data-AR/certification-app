# Criterios de aceptacion

## Globales

Autenticacion obligatoria, permisos backend, auditoria, minimizacion, estados validos y respuestas IA sin invencion.

## Gherkin ejemplo

```gherkin
Scenario: Crear asignacion mediante agente IA
  Given un manager con alcance sobre el colaborador
  When solicita crear una asignacion
  And confirma el resumen
  Then el backend crea la asignacion
  And registra auditoria con origen AI_AGENT
```
