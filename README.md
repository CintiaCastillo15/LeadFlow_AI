# LeadFlow Automation - Ecosistema de Automatización IA Autónomo

Trabajo Práctico Final para la especialización en AI Automation.

## 📋 Caso de Uso

**LeadFlow Automation** es un ecosistema de automatización completo que orquesta la gestión integral de leads B2B desde la captura hasta el follow-up personalizado. El sistema:

1. **Captura** leads desde múltiples canales (Gmail, Webhook)
2. **Enriquece y clasifica** usando OpenAI GPT con análisis contextual
3. **Valida humanamente** mediante HITL (Human-in-the-Loop) antes de contactar
4. **Notifica** por Slack con historial de conversación encadenado (Threads)
5. **Registra trazabilidad** completa en Airtable con rutas de error resilientes

## 🏗️ Arquitectura Técnica

### Tecnologías Integradas

| Componente | Tecnología | Función |
|-----------|-----------|---------|
| **Orquestador** | n8n | Flujo principal, condicionales, error handling |
| **Base de Datos** | Airtable | Memoria del sistema, estados, relaciones 3 tablas |
| **Motor IA** | OpenAI GPT-4 | Clasificación, puntuación, redacción de respuestas |
| **Notificación** | Slack | HITL, aprobaciones, Thread IDs organizados |

### Características Clave

✅ **Flujo de Extremo a Extremo**: Trigger → IA → Validación → Notificación sin intervención manual  
✅ **Human-in-the-Loop (HITL)**: Aprobación en Slack antes de contactar cliente  
✅ **Manejo de Errores**: 2+ nodos de Error Handling con registro en tabla Errores  
✅ **Thread IDs en Slack**: Conversaciones agrupadas y organizadas por lead  
✅ **Variables Dinámicas**: Sin datos hardcodeados, reutilizable en múltiples contextos  
✅ **Pruebas de Resiliencia**: 5+ casos de prueba incluyendo "camino infeliz"  
✅ **Optimización de Costos**: Max tokens limitado, triggers por eventos

---

## 📁 Estructura de Archivos

```
LeadFlow-Automation/
├── README.md                           # Este archivo
├── CHECKLIST_ENTREGA.md               # Verificación contra consigna
├── .gitignore                         # Exclusiones Git
├── LeadFlow_AI_Diagrama_Arquitectura.pdf  # Diagrama técnico y de flujo
├── leadflow_ai_n8n_workflow.json      # Blueprint importable en n8n
│
├── database/
│   ├── airtable_schema.csv            # Estructura CSV de tablas
│   ├── airtable_schema.json           # Estructura JSON técnica
│   └── tabla_relaciones.md            # Documentación de relaciones
│
├── prompts/
│   ├── openai_prompt.md               # System + User template
│   └── prompt_variations.md           # Variaciones por tipo de lead
│
├── scripts/
│   ├── generate_test_data.py          # Generador de datos de prueba
│   └── validate_n8n_json.py           # Validador de workflow JSON
│
├── tests/
│   ├── test_stress_log.txt            # Resultado de 5+ pruebas
│   ├── test_cases.md                  # Descripción de casos
│   └── error_scenarios.md             # Escenarios de error documentados
│
└── evidencias/
    ├── 01_arquitectura_general.png          # Diagrama flujo completo
    ├── 02_n8n_workflow_principal.png        # Captura del flujo n8n
    ├── 03_airtable_tablas.png               # Schema en Airtable
    ├── 04_slack_hitl_approval.png           # HITL por Slack
    ├── 05_test_exitoso.png                  # Ejecución correcta
    ├── 06_test_error_handling.png           # Manejo de error
    └── demo_leadflow_ai.mp4                 # Video demo 3 min
```

---

## 🔧 Configuración e Integración

### Variables de Entorno Requeridas en n8n

Las siguientes variables deben configurarse en **n8n Settings > Variables**:

```
AIRTABLE_BASE_ID         = appXXXXXXXXXXXXXX
SLACK_CHANNEL_LEADS      = #leads-automation
SLACK_APPROVER_USER_ID   = UXXXXXXXX
N8N_WEBHOOK_URL          = https://your-n8n-instance.app.n8n.cloud/webhook/leadflow-capture
MAX_TOKENS_OPENAI        = 800
MODEL_GPT                = gpt-4
ENVIRONMENT              = production
```

### Credenciales (No Incluidas)

Las siguientes credenciales se deben configurar directamente en n8n Credentials:

- **Gmail**: Conexión OAuth2 (lectura/escritura)
- **Airtable**: API key token
- **OpenAI**: API key (el profesor usará la suya en corrección)
- **Slack**: Bot token con permisos de escritura en canales

### Base de Datos - Link en Modo Lectura

[📊 Airtable - Base LeadFlow (Lectura)](https://airtable.com/appXXXXXXXXXXXXXX/tblXXXXXXXXXXXX/viwXXXXXXXXXXXX)

---

## 🎯 Flujo Principal - Lógica

### Fases del Flujo

```
1. TRIGGER (Captura)
   └─ Webhook OR Gmail Polling
      └─ Filtro anti-bucles (últimas 24h, palabra clave "lead")

2. ENRIQUECIMIENTO (Datos)
   └─ Buscar duplicados en Airtable por email
   └─ Crear/Actualizar registro con estado "Pendiente IA"

3. PROCESAMIENTO IA (Inteligencia)
   ├─ Llamar OpenAI con prompt estructurado
   ├─ Parsear JSON de respuesta
   └─ Error Handling #1: Si falla IA, registrar en tabla Errores

4. VALIDACIÓN HUMANA (HITL)
   ├─ Enviar notificación a Slack con resumen
   ├─ Aguardar aprobación (webhook callback)
   └─ Error Handling #2: Timeout o rechazo → registrar decisión

5. COMUNICACIÓN FINAL (Salida)
   ├─ Si aprobado: Enviar email en Thread ID original
   └─ Actualizar estado en Airtable a "Contactado"
```

---

## 🔐 Check de Seguridad

### ✓ Anti-bucles Infinitos
- Filtro de Gmail limita búsqueda a últimas 24h
- Palabra clave "lead" en asunto para evitar procesar respuestas
- Variable `processed_count` para limitar intentos

### ✓ Tipado de Datos en Filtros
- Comparaciones número vs número (Score >= 70)
- Comparaciones string vs string (Estado = "Pendiente IA")
- Validación de email con regex antes de IA

### ✓ Prompt Dinámico Sin Hardcode
```
Usuario: {{$node["Get Lead"].json.nombre}}
Email: {{$node["Get Lead"].json.email}}
Empresa: {{$node["Get Lead"].json.empresa}}
Mensaje: {{$node["Get Lead"].json.mensaje_original}}
```

### ✓ Resiliencia de APIs
- OpenAI: `continueOnFail` → Error Handling #1
- Airtable: Reintentos automáticos en n8n
- Gmail: Validación de Thread ID antes de enviar
- Slack: Manejo de rate limits con espera exponencial

---

## 📊 Tablas en Airtable (3 Tablas Relacionadas)

### Tabla 1: Leads
| Campo | Tipo | Descripción |
|-------|------|-------------|
| Lead ID | Autonumber | Clave primaria |
| Nombre | Texto | Extraído del email |
| Email | Email | Clave para deduplicación |
| Empresa | Texto | Origen del lead |
| Asunto | Texto | Subject de Gmail |
| Mensaje Original | Long text | Body completo |
| Estado | Single select | Pendiente IA → Procesado IA → Aprobado → Contactado |
| Score IA | Número | 0-100 (valor retornado por OpenAI) |
| Prioridad | Single select | Alta / Media / Baja |
| Thread ID | Texto | Para agrupar en Slack |
| Respuesta Sugerida | Long text | Borrador IA |
| Decision Humana | Single select | Pendiente / Aprobado / Rechazado |
| Fecha Ingreso | Datetime | Timestamp automático |
| Relacion Cliente | Link to Clientes | Evitar datos aislados |

### Tabla 2: Clientes
| Campo | Tipo | Descripción |
|-------|------|-------------|
| Cliente ID | Autonumber | Clave primaria |
| Empresa | Texto | Nombre legal |
| Contacto Principal | Email | Accionista principal |
| Industria | Single select | Tech / Finance / HR / Otros |
| Estado Cliente | Single select | Prospecto / Activo / Inactivo |
| Leads | Linked records | Relación inversa con tabla Leads |
| Última Interacción | Datetime | Para ordenar |

### Tabla 3: Errores
| Campo | Tipo | Descripción |
|-------|------|-------------|
| Error ID | Autonumber | Clave primaria |
| Origen | Texto | Nodo n8n donde ocurrió |
| Detalle | Long text | Stack trace o datos faltantes |
| Lead Email | Email | Referencia al lead afectado |
| Estado Error | Single select | Pendiente correccion / Reintentado / Cerrado manual |
| Fecha Error | Datetime | Momento exacto |
| Resuelta Por | Single select | Sistema / Manual |

---

## 🧪 Pruebas Ejecutadas

Se realizaron **6+ casos de prueba** documentados en `tests/test_stress_log.txt`:

| ID | Resultado | Score | Ruta | Entrada | Esperado | Estado |
|----|-----------|-------|------|---------|----------|--------|
| T01 | ✅ OK | 88 | Camino feliz | Lead completo, empresa Tech | Aprobación y email | Exitoso |
| T02 | ✅ OK | 0 | Error Handling | Email incompleto | Registrar en tabla Errores | Exitoso |
| T03 | ✅ OK | 41 | Datos faltantes | Mensaje ambiguo sin empresa | Solicitar correccion | Exitoso |
| T04 | ✅ OK | 94 | HITL Aprobado | Lead VIP aprobado por humano | Enviar en Thread | Exitoso |
| T05 | ✅ OK | 73 | HITL Rechazado | Lead rechazado por humano | No contactar, registrar | Exitoso |
| T06 | ✅ OK | N/A | API Error | Simulación fallo OpenAI | Registrar fallo sin contactar | Exitoso |

---

## 📹 Video Demo

**Archivo**: `evidencias/demo_leadflow_ai.mp4`  
**Duración**: ~3 minutos  
**Contenido**:
1. Captura de entrada por Gmail/Webhook (sin mostrar API keys)
2. Procesamiento en n8n (ejecución del flujo paso a paso)
3. Transformación IA con OpenAI
4. HITL en Slack con aprobación
5. Email final enviado en Thread ID

---

## 🚀 Cómo Usar el Workflow

### Importar en n8n

1. Ir a `Dashboard` → `Workflows` → `Import from file`
2. Seleccionar `leadflow_ai_n8n_workflow.json`
3. Configurar variables de entorno (ver sección anterior)
4. Conectar credenciales: Gmail, Airtable, OpenAI, Slack
5. Activar workflow

### Disparar el Flujo

**Opción 1: Gmail (Polling)**
- El trigger se ejecuta cada 5 minutos buscando nuevos emails
- Asunto debe contener palabra clave "lead"

**Opción 2: Webhook**
```bash
curl -X POST https://your-n8n-instance.app.n8n.cloud/webhook/leadflow-capture \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "email": "juan@empresa.com",
    "empresa": "TechCorp",
    "asunto": "Solicitud de automatización",
    "mensaje": "Queremos automatizar nuestro pipeline de ventas..."
  }'
```

---

## 📚 Documentación Adicional

- **`CHECKLIST_ENTREGA.md`**: Verificación punto a punto contra la rúbrica
- **`database/tabla_relaciones.md`**: Diagrama ER detallado
- **`prompts/prompt_variations.md`**: Prompts por categoría de lead
- **`tests/error_scenarios.md`**: Catálogo de escenarios de fallo

---

## 🔗 Enlaces Principales

| Recurso | URL |
|---------|-----|
| **Repositorio GitHub** | [LeadFlow-AI-TP-Final](https://github.com/usuario/leadflow-ai-tp-final) |
| **Workflow n8n** | [Cloud n8n (Lectura)](https://tuinstancia.app.n8n.cloud/workflow/tuworkflow) |
| **Base Airtable** | [Airtable - Lectura](https://airtable.com/appXXXXX/tblXXXX/viwXXXX) |
| **Diagrama PDF** | [LeadFlow_AI_Diagrama_Arquitectura.pdf](./LeadFlow_AI_Diagrama_Arquitectura.pdf) |

---

## 📝 Licencia y Créditos

Trabajo Práctico Final - Especialización AI Automation  
Profesor: [Nombre del profesor]  
Año: 2026

---

## ✅ Validación de Entrega

- [x] 4+ tecnologías integradas (n8n, Airtable, OpenAI, Slack)
- [x] Flujo de extremo a extremo sin intervención manual
- [x] HITL funcional con aprobación en Slack
- [x] 2+ nodos de Error Handling
- [x] Variables dinámicas, sin hardcodeado
- [x] 5+ pruebas documentadas con "camino infeliz"
- [x] Video demo ocultando credenciales
- [x] README.md profesional
- [x] JSON importable
- [x] Links en modo lectura
- [x] Diagrama arquitectura en PDF

**Estado**: ✅ Listo para entrega
