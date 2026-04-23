# Documentación de Integración Moodle ↔ Frappe

## Arquitectura de Integración

La integración entre Moodle y Frappe utiliza un **modelo híbrido bidireccional**:

- **Frappe → Moodle**: API REST (Moodle Web Services API)
- **Moodle → Frappe**: Webhooks (Event-driven)

```
┌─────────────────┐                    ┌─────────────────┐
│                 │   API REST Call    │                 │
│     Frappe      │ ─────────────────> │     Moodle      │
│   (ERPNext)     │                    │      LMS        │
│                 │ <───────────────── │                 │
│                 │   HTTP Webhook     │                 │
└─────────────────┘                    └─────────────────┘
```


**Clasificación**: **Híbrida API REST + Event-Driven Webhooks**

- **API REST** (Request-Response): Frappe inicia la comunicación y espera respuesta
- **Webhooks** (Event-Driven): Moodle notifica cambios de forma reactiva


---

## 1. Frappe → Moodle (API REST)

### Descripción
Cuando se crea o actualiza un curso en Frappe, se utiliza la **Moodle Web Services API** para sincronizar los cambios.

### Tecnología
- **Protocolo**: HTTP/HTTPS
- **Método**: POST
- **Formato**: JSON
- **API**: Moodle Web Services (REST protocol)

### Flujo de Trabajo

1. **Evento Disparador** (en Frappe):
   - `after_insert` - Cuando se crea un curso (siempre se ejecuta)
   - `on_update` - Cuando se actualiza un curso (solo si ya tiene `moodle_course_id`)

2. **Procesamiento Asíncrono** 
   ```python
   # Para cursos nuevos (after_insert)
   frappe.enqueue(
       "education.moodle_integration.events._try_sync_new_course",
       course_name=doc.name,
       queue="short",
   )

   # Para cursos existentes (on_update)
   frappe.enqueue(
       "education.moodle_integration.events.sync_course_to_moodle",
       course_name=doc.name,
       queue="short",
   )
   ```

3. **Llamada a API de Moodle**:
   ```
   POST http://moodle-host/webservice/rest/server.php

   Parámetros:
   - wstoken: [API Token]
   - wsfunction: core_course_create_courses | core_course_update_courses
   - moodlewsrestformat: json
   - courses[0][fullname]: [Nombre del curso]
   - courses[0][shortname]: [Código del curso]
   - courses[0][categoryid]: [ID de categoría]
   ```

4. **Respuesta de Moodle**:
   ```json
   [
     {
       "id": 123,
       "shortname": "CURSO-001",
       "fullname": "Curso de Ejemplo"
     }
   ]
   ```

5. **Actualización en Frappe**:
   - Se guarda el `moodle_course_id` en el campo correspondiente del curso

### Archivos Involucrados

| Archivo | Descripción |
|---------|-------------|
| `education/education/doctype/course/course.py` | Hooks que disparan la sincronización |
| `education/moodle_integration/events.py` | Manejadores de eventos y cola |
| `education/moodle_integration/sync_manager.py` | Lógica de sincronización con Moodle API |
| `education/moodle_integration/moodle_client.py` | Cliente HTTP para Moodle Web Services |

---

## 2. Moodle → Frappe (Webhooks)

### Descripción
Cuando se crea o actualiza un curso en Moodle, se envía un **webhook HTTP** a Frappe para sincronizar automáticamente.

### Tecnología
- **Protocolo**: HTTP/HTTPS
- **Método**: POST
- **Formato**: JSON
- **Plugin**: `local_webhooks` (Moodle)

### Flujo de Trabajo

1. **Evento Disparador** (en Moodle):
   - `\core\event\course_created` - Cuando se crea un curso
   - `\core\event\course_updated` - Cuando se actualiza un curso

2. **Plugin Webhook** captura el evento:
   ```php
   // moodle/local/webhooks/classes/handler.php
   public static function events($event) {
       $data = $event->get_data();
       // Envía webhook a Frappe
   }
   ```

3. **Petición HTTP a Frappe**:
   ```
   POST http://frappe-host:8000/api/method/education.moodle_integration.api.webhook_moodle_course_updated
   Content-Type: application/json

   {
     "eventname": "\\core\\event\\course_created",
     "id": "123",
     "shortname": "CURSO-001",
     "fullname": "Curso de Ejemplo",
     "summary": "Descripción del curso"
   }
   ```

4. **Procesamiento en Frappe**:
   - Busca si el curso existe (por `moodle_course_id`, `shortname`, o `fullname`)
   - Si existe: actualiza los campos modificados
   - Si no existe: crea un nuevo curso

5. **Respuesta a Moodle**:
   ```json
   {
     "status": "created|updated|skipped",
     "course": "CURSO-001",
     "moodle_id": "123"
   }
   ```


---

## 3. Optimizaciones de Rendimiento

### Sincronización Asíncrona (Frappe)

La sincronización se ejecuta en background mediante colas de trabajo para no bloquear el guardado:

```python
# Encolar trabajo en background
frappe.enqueue(
    "education.moodle_integration.events._try_sync_new_course",
    course_name=doc.name,
    queue="short",
)
```

**Resultado**: Guardado instantáneo (< 2 segundos), sincronización procesada por worker en background.


## 4. Campos Sincronizados

| Campo en Moodle | Campo en Frappe | Dirección | Notas |
|-----------------|-----------------|-----------|-------|
| `id` | `moodle_course_id` | Ambas | Clave de vinculación |
| `fullname` | `course_name` | Ambas | Nombre completo del curso |
| `shortname` | `name` | Ambas | Código/ID del curso |
| `summary` | `description` | Ambas | Descripción del curso |
| `categoryid` | - | Frappe → Moodle | ID de categoría en Moodle |

---

## 5. Configuración

### En Frappe

**DocType**: `Moodle Integration Settings`

```python
{
  "enabled": 1,                    # Habilitar integración
  "sync_on_create": 1,            # Sincronizar al crear
  "sync_on_update": 1,            # Sincronizar al actualizar
  "moodle_url": "http://moodle-host",
  "api_token": "your-api-token",
  "default_category_id": 1
}
```

### En Moodle

1. **Habilitar Web Services**:
   - Site administration → Advanced features → Enable web services
      - Habilitar servicios web 
      - Habilitar servicios web para dispositivos mobiles 

2. **Crear el servicio externo**
   - Administración del sitio → Plugins → Web services → External services
      - Clic en **Agregar**

      - Nombre: `Escazu Education`

      - Habilitado: sí

      - Guardar

      Luego clic en **Funciones** del servicio recién creado y agregar:

        | Función |
        |---------|
        | core_webservice_get_site_info |
        | core_course_get_courses_by_field |
        | core_course_create_courses |
        | core_course_update_courses |
        | core_user_create_users |
        | core_user_get_users_by_field |
        | core_user_update_users |
        | enrol_manual_enrol_users |
        | enrol_manual_unenrol_users |

2. **Crear Token API**:
    - Administración del sitio → Plugins → Web services → Manage tokens → Crear token
      - Usuario: `admin`
      - Servicio: `Escazu Education`
      - Fecha de expiración: un año adelante o mas 
      - Guardar

3. **Instalar Plugin Webhooks**:
   - Ubicación: `moodle/local/webhooks/`
   - Configurar webhook apuntando a Frappe



4. **Configurar el webhook (plugin local/webhooks)**
  
- Administración del sitio → server → Webhooks → Agregar nuevo registro**

Llenar el formulario con:

| Campo | Valor |
|---|---|
| Title | `sync to frappe` |
| Request URL | `http://host.docker.internal:8000/api/method/education.moodle_integration.api.webhook_moodle_course_updated` |
| Type | `json` |
| Token | el mismo token generado anteriormente (opcional)|
| Enable | sí |
| Events | `\core\event\course_updated` y `\core\event\course_created` |


y Guardar.


> Request URL la IP real del contenedor Frappe.



## 6. Endpoints API

### Frappe Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/method/education.moodle_integration.api.webhook_moodle_course_updated` | POST | Recibe webhooks de Moodle (creación/actualización de cursos) |
| `/api/method/education.moodle_integration.settings.test_connection` | POST | Probar conexión con Moodle |

### Moodle Web Services

| Función | Descripción |
|---------|-------------|
| `core_course_create_courses` | Crear cursos |
| `core_course_update_courses` | Actualizar cursos |
| `core_course_get_courses_by_field` | Obtener cursos por campo |





