# Seguridad

## Principios

Minimo privilegio, defensa en profundidad, validacion backend, auditoria por defecto, segregacion de funciones y proteccion de evidencias.

## Controles

| Area | Control |
| --- | --- |
| Auth | SSO/MFA segun politica |
| API | Object authorization, rate limit, input validation |
| Datos | Cifrado, masking, minimizacion |
| Evidencias | Storage seguro y URLs temporales |
| Agente | Allowlist, confirmacion, audit log |
| DevSecOps | PR, CODEOWNERS, secret scanning |
