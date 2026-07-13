# Casos de Prueba - LeadFlow Automation

## Descripción General

Este documento detalla los **6+ casos de prueba** ejecutados para validar el flujo de automatización. Cada caso simula un escenario real de lead B2B y verifica que el sistema responda correctamente.

---

## Convenciones

- **ID**: Identificador único del test (T01-T06)
- **Categoría**: Tipo de scenario (Camino feliz, Error handling, HITL, etc.)
- **Score IA Esperado**: Rango de puntuación que debe retornar OpenAI
- **Ruta Esperada**: Por cuál nodo del flujo debe pasar
- **Resultado Esperado**: Qué debe ocurrir al finalizar
- **Criterio de Éxito**: Cómo verificar que pasó correctamente

---

## T01 - Camino Feliz: Lead VIP Calificado

### Descripción
Un lead de una empresa fintech establecida solicita automatización de procesos. Todos los datos son completos, el caso de uso es claro y hay presupuesto definido. Este es el flujo ideal que debería resultar en contacto inmediato.

### Datos de Entrada

```json
{
  "nombre": "Carlos Mendez",
  "email": "carlos@fintech-solutions.com",
  "empresa": "FinTech Solutions Argentina",
  "industria": "Finance",
  "asunto": "Consulta - Automatización de procesos de compliance",
  "mensaje": "Hola, somos una fintech con 120 empleados. Necesitamos automatizar nuestros procesos de compliance regulatorio. Enviamos ~5000 reportes mensuales que requieren validación manual. Presupuesto estimado: USD 200k. ¿Cómo podríamos empezar?"
}
```

### Expectativas

| Aspecto | Esperado |
|---------|----------|
| **Score IA** | 85-95 (VIP) |
| **Prioridad** | Alta |
| **Datos Faltantes** | [] (vacío) |
| **Categoría IA** | VIP - Lead Calificado |
| **Requiere HITL** | Sí |
| **Email Enviado** | Sí |
| **Estado Final** | Contactado |

### Ruta en el Flujo

```
Trigger (Gmail/Webhook)
  ↓
Parse Email
  ↓
Buscar Duplicado → NO existe
  ↓
Crear Lead (Estado: Pendiente IA)
  ↓
Validar Datos → OK
  ↓
OpenAI (Score 88)
  ↓
Parse Respuesta → JSON válido
  ↓
Actualizar Lead (Estado: Procesado IA)
  ↓
Score >= 40? → SÍ
  ↓
Slack HITL → Aprobación
  ↓
Esperar Webhook → Aprobado
  ↓
Gmail Enviar
  ↓
Actualizar Lead (Estado: Contactado)
  ✅ FIN - ÉXITO
```

### Criterios de Éxito

- [ ] Airtable: Registro creado con Score 88
- [ ] Airtable: Estado = "Contactado"
- [ ] Airtable: Decision Humana = "Aprobado"
- [ ] Slack: Notificación HITL recibida
- [ ] Slack: Thread ID organizado
- [ ] Gmail: Email enviado a carlos@fintech-solutions.com
- [ ] Gmail: Email en Reply-To del original
- [ ] Logs n8n: Cero errores

---

## T02 - Camino Infeliz: Email Incompleto

### Descripción
Un lead interesado pero con datos incompletos (sin empresa, email genérico). El sistema debe detectar datos faltantes, no avanzar a HITL, y enviar email automático pidiendo enriquecimiento.

### Datos de Entrada

```json
{
  "nombre": "María González",
  "email": "maria@gmail.com",
  "empresa": "[NO DETECTADA]",
  "industria": "[Desconocida]",
  "asunto": "lead - Necesito automatizar nuestro sistema",
  "mensaje": "Hola, necesitamos automatizar un proceso pero no tenemos mucho presupuesto. ¿Cuánto cuesta? Gracias"
}
```

### Expectativas

| Aspecto | Esperado |
|---------|----------|
| **Score IA** | 25-40 (Bajo) |
| **Prioridad** | Media |
| **Datos Faltantes** | ["empresa", "presupuesto", "industria", "tamaño"] |
| **Categoría IA** | Lead Incompleto - Revisión Manual |
| **Requiere HITL** | No (Score < 40) |
| **Email Enviado** | Sí (automático) |
| **Estado Final** | Pendiente Enriquecimiento |

### Ruta en el Flujo

```
Trigger → Parse → Buscar Duplicado → NO existe
  ↓
Crear Lead (Estado: Pendiente IA)
  ↓
Validar Datos → OK (aunque incompletos)
  ↓
OpenAI (Score 32)
  ↓
Parse Respuesta → JSON con datos_faltantes
  ↓
Actualizar Lead (Estado: Procesado IA)
  ↓
Score >= 40? → NO
  ↓
Nodo de Enrutamiento: Score Bajo
  ↓
Actualizar Lead (Estado: Pendiente Enriquecimiento)
  ↓
Gmail Enviar Email Automático
  ✅ FIN - ENRIQUECIMIENTO PENDIENTE
```

### Criterios de Éxito

- [ ] Airtable: Score 32
- [ ] Airtable: Datos Faltantes con array ["empresa", ...]
- [ ] Airtable: Estado = "Pendiente Enriquecimiento"
- [ ] Slack: NO notificación de HITL
- [ ] Gmail: Email automático enviado a maria@gmail.com
- [ ] Gmail: Email pidiendo datos faltantes
- [ ] Tabla Errores: NO registro (no es error, es flujo normal)

---

## T03 - Camino Infeliz: Mensaje Ambiguo

### Descripción
Lead con contacto corporativo pero propuesta vaga, sin caso de uso específico ni presupuesto. El sistema detecta score medio, dispara HITL para validación humana, pero requiere acción manual del approver.

### Datos de Entrada

```json
{
  "nombre": "Roberto Pérez",
  "email": "roberto.perez@empresa.com.br",
  "empresa": "Empresa [parcialmente detectada]",
  "industria": "Manufacturing",
  "asunto": "Re: lead consulting",
  "mensaje": "Vimos vuestro sitio web. Nos interesó. Habría que ver si es compatible con nuestro stack. Cuáles son las alternativas?"
}
```

### Expectativas

| Aspecto | Esperado |
|---------|----------|
| **Score IA** | 45-60 (Intermedio) |
| **Prioridad** | Media |
| **Datos Faltantes** | ["empresa_completa", "caso_uso", "presupuesto"] |
| **Categoría IA** | Lead Potencial - Datos Insuficientes |
| **Requiere HITL** | Sí (40 <= Score < 70) |
| **Email Enviado** | Sí (si aprobado) |
| **Estado Final** | Contactado o Rechazado |

### Ruta en el Flujo

```
Trigger → Parse → Buscar Duplicado → Validar → OpenAI (Score 51)
  ↓
Actualizar Lead (Estado: Procesado IA)
  ↓
Score >= 40? → SÍ
  ↓
Slack HITL → Notificación
  ↓
Esperar Webhook → Aprobado (5 minutos después)
  ↓
Gmail Enviar
  ↓
Actualizar Lead (Estado: Contactado)
  ✅ FIN - CONTACTADO
```

### Criterios de Éxito

- [ ] Airtable: Score 51
- [ ] Airtable: Datos Faltantes con 3+ campos
- [ ] Airtable: Estado = "Procesado IA"
- [ ] Slack: Notificación HITL enviada
- [ ] Slack: Thread ID activo
- [ ] Gmail: Email enviado tras aprobación
- [ ] Airtable: Decision Humana = "Aprobado"
- [ ] Airtable: Approver User registrado

---

## T04 - HITL Aprobado: Lead Enterprise VIP

### Descripción
Lead de empresa tech consolidada con presupuesto definido y need claro. Score VIP (94). Se envía a HITL, el approver aprueba rápidamente (2 minutos), y se contacta inmediatamente. Verifica que HITL funciona con aprobación rápida.

### Datos de Entrada

```json
{
  "nombre": "Ana López",
  "email": "ana.lopez@techcompany.io",
  "empresa": "TechCompany Innovation Labs",
  "industria": "Tech",
  "asunto": "lead - Propuesta RPA para procesos backend",
  "mensaje": "Hola, somos TechCompany. Tenemos 5 procesos backend que podrían optimizarse con RPA. Team de 50+ personas en backend. Presupuesto disponible Q3 2026: USD 250k. ¿Disponibilidad para workshop?"
}
```

### Expectativas

| Aspecto | Esperado |
|---------|----------|
| **Score IA** | 90-98 (Enterprise VIP) |
| **Prioridad** | Alta |
| **Datos Faltantes** | [] (vacío) |
| **Categoría IA** | VIP - Lead Enterprise |
| **HITL Timeout** | 2 minutos (aprobación rápida) |
| **Email Enviado** | Sí |
| **Estado Final** | Contactado |

### Ruta en el Flujo

```
Trigger (Webhook) → Parse → OpenAI (Score 94)
  ↓
Slack HITL a #leads-vip
  ↓
Esperar Aprobación → 2 minutos
  ↓
Aprobado por director@empresa.com
  ↓
Gmail Enviar (con propuesta workshop)
  ↓
Actualizar Lead (Contactado, Decision = Aprobado)
  ✅ FIN - VIP CONTACTADO EXITOSAMENTE
```

### Criterios de Éxito

- [ ] Airtable: Score 94
- [ ] Airtable: Prioridad = "Alta"
- [ ] Airtable: Estado = "Contactado"
- [ ] Slack: Notificación en canal VIP
- [ ] Slack: Thread con 4+ mensajes (flow + aprobación + confirmación)
- [ ] Gmail: Email personalizado con propuesta de workshop
- [ ] Airtable: Decision Humana = "Aprobado"
- [ ] Airtable: Approver User = "director@empresa.com"
- [ ] Timing: Menos de 3 minutos de inicio a fin

---

## T05 - HITL Rechazado: Lead Fuera de ICP

### Descripción
Lead de startup early-stage muy pequeña (3 empleados), presupuesto USD 5k. Score muy bajo (28). Sistema filtra automáticamente sin enviar a HITL. NO se contacta al cliente, solo email amable de rechazo.

### Datos de Entrada

```json
{
  "nombre": "Lucas Romero",
  "email": "lucas.romero@startup.com",
  "empresa": "StartUp XYZ",
  "industria": "Tech",
  "asunto": "lead - Herramienta de automatización",
  "mensaje": "Hola, soy founder de una startup early-stage. Buscamos herramientas baratas de automatización. Tenemos 3 empleados y budget USD 5k max."
}
```

### Expectativas

| Aspecto | Esperado |
|---------|----------|
| **Score IA** | 20-35 (Muy Bajo) |
| **Prioridad** | Baja |
| **Categoría IA** | Fuera de ICP - Lead Demasiado Pequeño |
| **HITL Ejecutado** | No (filtro automático) |
| **Email Enviado** | Sí (rechazo amable) |
| **Estado Final** | Error / No Calificado |

### Ruta en el Flujo

```
Trigger → Parse → Validar → OpenAI (Score 28)
  ↓
Actualizar Lead (Estado: Procesado IA)
  ↓
Score >= 40? → NO
  ↓
Nodo de Enrutamiento: Rechazar
  ↓
Actualizar Lead (Estado: No Calificado, Decision: Rechazado Sistema)
  ↓
Gmail Enviar Email Automático (rechazo educado)
  ✅ FIN - NO CONTACTADO (CORRECTO)
```

### Criterios de Éxito

- [ ] Airtable: Score 28
- [ ] Airtable: Estado = "Error" o "No Calificado"
- [ ] Airtable: Decision Humana = "Rechazado" (Sistema)
- [ ] Slack: NO notificación de HITL
- [ ] Gmail: Email de rechazo amable enviado
- [ ] Gmail: Email maniene puerta abierta para futuro
- [ ] Logs n8n: Flujo pasó por nodo de "No Contactar" correcto
- [ ] Tabla Errores: NO registro

---

## T06 - Error Handling: Fallo API OpenAI

### Descripción
Se dispara un webhook pero OpenAI falla (timeout, 503, credencial inválida). El sistema debe capturar el error, registrarlo en tabla Errores, NO contactar al cliente, notificar admin por Slack, y dejar el lead en estado recoverable para reintento.

### Simulación de Error

```
Trigger Webhook → Parse Email → OK
  ↓
Validar Datos → OK
  ↓
OpenAI API → ❌ TIMEOUT (Reintentado 3 veces)
  → Error 503: Service Unavailable
```

### Expectativas

| Aspecto | Esperado |
|---------|----------|
| **Error Capturado** | API Error - 503 Service Unavailable |
| **Reintentos** | 3 intentos (1s, 2s, 4s backoff) |
| **Email Enviado** | No |
| **HITL Ejecutado** | No |
| **Tabla Errores** | Registro creado |
| **Estado Lead** | Error |
| **Notificación Admin** | Sí (Slack #tech-alerts) |

### Ruta en el Flujo

```
Trigger → Parse → Validar → OpenAI
  ↓
❌ Error Handler #1: continueOnFail = true
  ↓
Registrar en tabla Errores
  ├─ Error ID: Auto
  ├─ Origen: OpenAI API Call
  ├─ Detalle: 503 Service Unavailable
  ├─ Lead Email: [email del lead]
  ├─ Estado Error: Pendiente correccion
  └─ Intentos: 3
  ↓
Slack Alert → #tech-alerts
  ├─ Mensaje: Error en procesamiento
  └─ Tag: @sysadmin
  ↓
Actualizar Lead (Estado: Error)
  ↓
Break en flujo (NO continuar)
  ✅ FIN - ERROR MANEJADO GRACEFULLY
```

### Criterios de Éxito

- [ ] Tabla Errores: Nuevo registro creado (Error ID auto)
- [ ] Tabla Errores: Origen = "OpenAI API Call"
- [ ] Tabla Errores: Detalle contiene "503"
- [ ] Tabla Errores: Lead Email correcto
- [ ] Tabla Errores: Estado Error = "Pendiente correccion"
- [ ] Tabla Errores: Intentos Reintentos = 3
- [ ] Airtable Leads: Estado = "Error"
- [ ] Slack: Notificación en #tech-alerts
- [ ] Gmail: NO email enviado al cliente
- [ ] Logs n8n: Nodo Error Handling ejecutado sin excepciones
- [ ] Recuperabilidad: Lead puede ser reintentado manualmente

---

## Matriz de Validación General

| Test | Resultado | Route | Score | HITL | Email | Error Handler | Aprobado |
|------|-----------|-------|-------|------|-------|---------------|----------|
| T01 | ✅ PASS | Feliz | 88 | ✓ | ✓ | — | Aprobado |
| T02 | ✅ PASS | Datos Falta. | 32 | — | ✓* | — | N/A |
| T03 | ✅ PASS | Medio | 51 | ✓ | ✓ | — | Aprobado |
| T04 | ✅ PASS | VIP | 94 | ✓ | ✓ | — | Aprobado |
| T05 | ✅ PASS | Rechazo | 28 | — | ✓* | — | Rechazado |
| T06 | ✅ PASS | Error | N/A | — | — | ✓ | Error |

Legend:
- *: Email automático, no contacto cliente final
- —: No aplica en esa ruta
- ✓: Ejecutado correctamente

---

## Checklist de Ejecución

Antes de ejecutar cada test:

- [ ] Verificar que n8n está conectado y variables de entorno configuradas
- [ ] Limpiar registros previos de Airtable (opcional)
- [ ] Preparar credenciales: Gmail, Airtable, OpenAI, Slack
- [ ] Verificar que webhooks están activos
- [ ] Tomar screenshot del inicio
- [ ] Ejecutar test
- [ ] Registrar timestamp
- [ ] Verificar cada criterio de éxito
- [ ] Recopilar evidencias (screenshots, logs)
- [ ] Documentar cualquier desviación
- [ ] Pasar a siguiente test

---

## Notas Finales

- Todos los tests deben ejecutarse en orden (T01 a T06)
- Cada test es independiente (se puede ejecutar aisladamente)
- Los datos de entrada pueden adaptarse a tu contexto específico
- Los criterios de éxito son verificables (no subjetivos)
- Documentar todas las desviaciones encontradas
