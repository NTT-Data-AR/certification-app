# Enfoque agente IA

## Posicionamiento

El agente es una capa de interaccion y orquestacion. No es fuente de verdad, no decide permisos y no aprueba certificaciones por si mismo.

## Patron

```mermaid
sequenceDiagram
  participant U as Usuario
  participant A as Agente IA
  participant API as Backend API
  participant DB as Base de datos
  U->>A: Solicitud
  A->>API: Tool autorizada
  API->>DB: Lee/escribe con reglas
  API-->>A: Resultado estructurado
  A-->>U: Respuesta minimizada
```

## Reglas

Usar herramientas aprobadas, confirmar escrituras, minimizar datos personales, registrar invocaciones y escalar ambiguedades.
