# Generar comunicaciones

## Objetivo

Generar comunicaciones.

## Flujo base

Iniciar, validar permisos, completar datos, aplicar reglas, persistir, auditar y notificar.

## Validaciones

Identidad, autorizacion, campos obligatorios, estados, calidad de datos y confirmacion si interviene el agente.

## Excepciones

| Caso | Tratamiento |
| --- | --- |
| Datos incompletos | Solicitar correccion |
| Permisos insuficientes | Denegar y auditar |
| Duplicado | Crear incidencia |
| Error de integracion | Registrar y reprocesar |

## Agente IA

Puede guiar, consultar y preparar acciones; no omite validaciones ni aprobaciones humanas.
