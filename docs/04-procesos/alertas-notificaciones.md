# Alertas y Notificaciones (RF-018)

Sistema de comunicaciones multicanal que notifica a usuarios sobre eventos en el ciclo de vida de certificaciones (asignaciones, validaciones, vencimientos, renovaciones).

**Ruta crítica:** `Evento disparador → Crea notification → Job envía → Retry logic → Tracking`

---

## 1. Fases del Proceso

### Fase 1: Creación de Notificación (Trigger)

**Disparadores de Notificación:**

| Evento | Tipo | Recipient | Cuándo | Prioridad |
|--------|------|-----------|--------|-----------|
| Certificación asignada | assignment_created | Colaborador + Manager | Inmediato | high |
| Validación iniciada | validation_pending | Validator | Inmediato | high |
| Certificación aprobada | validation_approved | Colaborador | Inmediato | high |
| Certificación rechazada | validation_rejected | Colaborador | Inmediato | high |
| Se requiere más info | info_requested | Colaborador | Inmediato | high |
| Próxima vencer (30d) | expiration_alert | Colaborador + Manager | Automático | medium |
| Próxima vencer (7d) | expiration_alert_critical | Colaborador + Manager + Owner | Automático | high |
| Ya expirada | expiration_alert_expired | Colaborador + Manager + Owner | Inmediato | critical |
| Renovación disponible | renewal_available | Colaborador | Automático | medium |
| Renovación aprobada | renewal_completed | Colaborador + Manager | Inmediato | high |

**Almacenamiento (INSERT):**

```sql
INSERT INTO notification (
  notification_id, recipient_id, type, 
  subject, body, priority,
  related_entity_type, related_entity_id,
  status, created_at, scheduled_for
) VALUES (
  UUID(), 
  collaborator_id,
  'assignment_created',
  'Nueva certificación asignada',
  'Se te asignó AWS SAA con vencimiento 2026-12-31',
  'high',
  'certification_assignment', assignment_id,
  'pending', NOW(), NOW()
);
```

---

### Fase 2: Enriquecimiento de Contexto

**Disparador:** Notification creada con status='pending'

**Actor:** Job async `backend/jobs/notification_enrichment_job.py`

**Flujo:**
1. Obtener notification no procesada
2. Enriquecer con datos contextuales
3. Generar canales y templates
4. Guardar en BD (notification_channel)

**Datos Enriquecidos:**
- Nombre colaborador, email, teléfono
- Nombre certificación, vendor
- Manager nombre/email
- Configuraciones de notificación del usuario (do not disturb, preferred channels)

**Ejemplo Enriquecido:**

```json
{
  "notification_id": "notif-abc123",
  "recipient": {
    "id": "collab-123",
    "name": "John Smith",
    "email": "john@nttdata.com",
    "phone": "+1234567890",
    "preferences": {
      "channels": ["email", "sms"],
      "do_not_disturb_until": "2026-05-08T19:00:00Z"
    }
  },
  "context": {
    "certification": {
      "id": "cert-456",
      "name": "AWS Solutions Architect Associate",
      "vendor": "Amazon"
    },
    "assignment": {
      "due_date": "2026-12-31",
      "priority": "high"
    }
  },
  "templates": [
    {
      "channel": "email",
      "template_id": "assignment_created_email",
      "variables": {
        "collaborator_name": "John",
        "certification_name": "AWS SAA",
        "due_date": "2026-12-31",
        "priority": "Alta"
      }
    },
    {
      "channel": "sms",
      "template_id": "assignment_created_sms",
      "variables": { ... }
    }
  ]
}
```

**Almacenamiento:**

```sql
INSERT INTO notification_channel (
  notification_id, channel, status,
  recipient_address, template_id, rendered_content,
  retry_count, last_attempt_at
) VALUES (
  'notif-abc123', 'email', 'pending',
  'john@nttdata.com', 'assignment_created_email',
  '...rendered HTML...',
  0, NULL
);

INSERT INTO notification_channel (
  notification_id, channel, status,
  recipient_address, template_id, rendered_content,
  retry_count, last_attempt_at
) VALUES (
  'notif-abc123', 'sms', 'pending',
  '+1234567890', 'assignment_created_sms',
  'Tu certificación AWS SAA asignada. Vence 2026-12-31.',
  0, NULL
);
```

---

### Fase 3: Envío por Canal

**Disparador:** notification_channel.status='pending'

**Actor:** Job async `backend/jobs/notification_sender_job.py`

**Flujo por Canal:**

#### Email

```python
# 1. Construir email
to = collaborator.email
subject = "Nueva certificación asignada: AWS SAA"
body = rendered_template_html
reply_to = "support@cert-app.com"

# 2. Enviar via SES / SendGrid
ses_client.send_email(
    Source='noreply@cert-app.com',
    Destination={'ToAddresses': [to]},
    Message={
        'Subject': {'Data': subject},
        'Body': {'Html': {'Data': body}}
    }
)

# 3. Log result
UPDATE notification_channel 
SET status='sent', sent_at=NOW(), response_code=200
WHERE notification_channel_id=?;
```

#### SMS

```python
# 1. Validar teléfono
phone = collaborator.phone
if not is_valid_phone(phone):
    notification_channel.status = 'invalid_recipient'
    return

# 2. Enviar via Twilio / AWS SNS
sns_client.publish(
    PhoneNumber=phone,
    Message=rendered_template_sms,
    MessageAttributes={
        'AWS.SNS.SMS.SenderID': {'StringValue': 'CertApp', 'DataType': 'String'},
        'AWS.SNS.SMS.SMSType': {'StringValue': 'Transactional', 'DataType': 'String'}
    }
)

# 3. Log result
UPDATE notification_channel 
SET status='sent', sent_at=NOW(), response_code=200
WHERE notification_channel_id=?;
```

#### Teams / Slack

```python
# 1. Obtener webhook URL de preferencia
webhook_url = get_notification_webhook(recipient_id, 'teams')

# 2. Construir payload
payload = {
    'type': 'message',
    'attachments': [
        {
            'contentType': 'application/vnd.microsoft.card.adaptive',
            'contentUrl': None,
            'content': {
                'type': 'AdaptiveCard',
                'body': [
                    {'type': 'TextBlock', 'text': 'Nueva certificación asignada', 'weight': 'bolder'},
                    {'type': 'TextBlock', 'text': 'AWS SAA - Vence 2026-12-31'}
                ],
                'actions': [
                    {'type': 'Action.OpenUrl', 'title': 'Ver en app',
                     'url': 'https://app.../assignments/abc123'}
                ]
            }
        }
    ]
}

# 3. POST a webhook
requests.post(webhook_url, json=payload)
```

#### Dashboard (In-App)

```sql
-- Ya fue insertada en Fase 2, aquí solo marcar como "leída"
UPDATE notification 
SET status='delivered'
WHERE notification_id=? AND status='pending';
```

---

### Fase 4: Manejo de Fallos y Reintentos

**Disparador:** Notificación falla en envío

**Actor:** Job de reintentos con backoff exponencial

**Lógica de Reintentos:**

```python
def retry_notification(notification_channel_id):
    nc = query_notification_channel(notification_channel_id)
    
    if nc.retry_count >= MAX_RETRIES:
        # Dar por vencida
        nc.status = 'failed_permanent'
        nc.final_status_reason = 'Max retries exceeded'
        INSERT audit_log(action='notification_failed_permanent', ...)
        NOTIFY admin  # Escalada
        return
    
    # Calcular delay con backoff exponencial
    backoff_seconds = 2 ** (nc.retry_count + 1)  # 2, 4, 8, 16, 32 min
    nc.next_retry_at = NOW() + INTERVAL backoff_seconds MINUTE
    
    # Intentar envío
    try:
        send_via_channel(nc)
        nc.status = 'sent'
        nc.retry_count = nc.retry_count  # No increment
    except Exception as e:
        nc.retry_count += 1
        nc.last_error = str(e)
        nc.status = 'pending_retry'
        nc.last_attempt_at = NOW()
```

**Tabla de Reintentos:**

| Intento | Delay | Tiempo Total | Acción si falla |
|---------|-------|--------------|-----------------|
| 1 | Inmediato | 0 min | Retry en 2 min |
| 2 | 2 min | 2 min | Retry en 4 min |
| 3 | 4 min | 6 min | Retry en 8 min |
| 4 | 8 min | 14 min | Retry en 16 min |
| 5 | 16 min | 30 min | Retry en 32 min |
| 6 | 32 min | 62 min | Escalada a admin |

---

### Fase 5: Tracking y Audit

**Disparador:** Cada cambio de status en notificación

**Actor:** Sistema (trigger automático)

**Almacenamiento:**

```sql
-- Audit log para cada cambio
INSERT INTO audit_log (
  correlation_id, actor_id, action,
  entity_type, entity_id,
  before_data, after_data, occurred_at
) VALUES (
  correlation_id,
  'system',
  'notification_status_changed',
  'notification', notification_id,
  JSON_OBJECT('status', old_status),
  JSON_OBJECT('status', new_status),
  NOW()
);

-- Metrics para monitoring
INSERT INTO notification_metrics (
  date, notification_type, channel,
  sent_count, failed_count, bounce_count,
  avg_latency_ms
) VALUES (
  DATE(NOW()), 'assignment_created', 'email',
  45, 2, 0, 1250
);
```

---

## 2. Configuración de Notificaciones por Usuario

**Interfaz:** Settings → Notification Preferences

**Opciones Configurables:**

```json
{
  "collaborator_id": "collab-123",
  "notifications": {
    "assignment_created": {
      "enabled": true,
      "channels": ["email", "sms"],
      "quiet_hours": "19:00-08:00"
    },
    "expiration_alert": {
      "enabled": true,
      "channels": ["email"],
      "quiet_hours": null
    },
    "validation_result": {
      "enabled": true,
      "channels": ["email", "teams"],
      "quiet_hours": "19:00-08:00"
    },
    "do_not_disturb_until": "2026-05-08T23:59:59Z"
  }
}
```

---

## 3. Templates de Notificación

**Email Template (assignment_created_email):**

```
To: {{ collaborator.email }}
Subject: Nueva certificación asignada: {{ certification.name }}

---

Hola {{ collaborator.first_name }},

Se te ha asignado la siguiente certificación:

Certificación: {{ certification.name }}
Vendor: {{ certification.vendor }}
Vencimiento: {{ assignment.due_date | format_date }}
Prioridad: {{ assignment.priority | capitalize }}

Puedes registrar tu certificación obtenida en:
{{ app_url }}/assignments/{{ assignment.id }}

Preguntas? Contacta a {{ manager.email }}

---

CertApp Team
```

**SMS Template (assignment_created_sms):**

```
{{ collaborator.first_name }}: {{ certification.name }} asignada. Vence {{ assignment.due_date | short_date }}. Registra aquí: {{ short_url }}
```

---

## 4. Validaciones y Casos de Borde

| Caso | Precondición | Comportamiento | Validación |
|------|--------------|-----------------|-----------|
| **Email inválido** | collaborator.email NULL o malformado | status='invalid_recipient', no retentar | Validation antes de INSERT |
| **Teléfono inválido** | collaborator.phone no match E.164 | SMS skipped, solo email | Validation REGEX +[0-9]... |
| **Usuario deshabilitado** | collaborator.status='inactive' | Notificación creada pero no enviada | Check en Fase 2 |
| **Do not disturb activo** | notification.created_at en quiet_hours | Schedulear para fin de quiet_hours | Calculate scheduled_for |
| **Webhook incorrecto** | Webhook Teams/Slack devuelve 404 | Retry lógica, escalada si persistente | Track response codes |
| **Duplicado** | Misma notificación creada 2 veces | UNIQUE constraint impide + log | DB constraint |
| **Excesivas notificaciones** | 100+ notificaciones en 1 minuto | Throttle a 10/min por usuario | Rate limiter en Fase 2 |

---

## 5. SLAs

| Hito | Tiempo Máximo | Responsable | Alerta |
|------|---------------|-------------|--------|
| Notification creada | Inmediato | Trigger | Async |
| Enriquecimiento | 5 segundos | Enrichment job | Monitor latency |
| Email enviado | 2 minutos | Email service | Retry logic |
| SMS enviado | 30 segundos | SMS service | Retry logic |
| Entrega confirmada | 5 minutos (timeout) | Email/SMS provider | Bounce handling |

---

## 6. Ejemplo de Línea de Tiempo

```
Martes 07-may, 09:00 — Carlos asigna AWS SAA a John
  ✓ INSERT assignment
  ✓ Trigger: INSERT notification(status='pending')

Martes 07-may, 09:00:05 — Enrichment job procesa
  ✓ Obtiene notification pendiente
  ✓ Enriquece con datos contextuales
  ✓ Genera templates (email + SMS)
  ✓ INSERT notification_channel x2

Martes 07-may, 09:00:10 — Sender job intenta envío
  ✓ Email: POST a SES
  ✓ SES retorna 200 OK
  ✓ UPDATE notification_channel status='sent'
  ✓ SMS: POST a Twilio
  ✓ Twilio retorna 200 OK
  ✓ UPDATE notification_channel status='sent'

Martes 07-may, 09:01 — John ve emails y SMS
  ✓ Email inbox: "AWS SAA asignada"
  ✓ SMS: "AWS SAA asignada. Vence 2026-12-31"
  ✓ Dashboard: notification widget "1 new"
```

---

## 7. Integración con Otros Procesos

```
ALERTAS-NOTIFICACIONES
  ├─ Disparada por: ASIGNACIÓN, VALIDACIÓN, SEGUIMIENTO, RENOVACIÓN
  ├─ Depende de: Collaborator preferences
  └─ Registrada en: audit_log
```

---

## 8. Checklist de Implementación

- [ ] notification table en BD con status/priority/type
- [ ] notification_channel table (email, sms, teams)
- [ ] Notification triggers: 10+ tipos de eventos
- [ ] Enrichment job: `backend/jobs/notification_enrichment_job.py`
- [ ] Sender job: `backend/jobs/notification_sender_job.py`
- [ ] Email service integration (SES/SendGrid)
- [ ] SMS service integration (Twilio/SNS)
- [ ] Teams/Slack webhook support
- [ ] Retry logic con backoff exponencial
- [ ] Notification preferences UI
- [ ] Template engine (Jinja2 o similar)
- [ ] Monitoring: delivery rate, bounce rate, latency
- [ ] Test cases: TC-018a (email), TC-018b (sms), TC-018c (retry)
- [ ] Runbook: "Notificación no enviada", "Bounce handling"

---

**Última actualización:** 2026-05-07  
**Estado:** Implementado con multicanal support  
**Relacionado:** RF-018, TC-018a/b/c
