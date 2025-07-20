Aquí tienes el mismo **plan de 4 fases**, ahora enriquecido con:

* **Gestión por roles** (quién puede crear/editar/borrar eventos y gestionar el KB).
* Adaptación al modelo **`ChatbotKnowledgeBase`** que usas en Admin.

Integra cada bloque directamente en tu Gantt de 1 mes.

---

## 🛠️ FASE 1 – Setup, Modelado y Roles (Semana 1)

1. **Inicializar entorno**

   * Crear virtualenv e instalar: Django, DRF, firebase-admin/pyfcm, y tu paquete de auditoría (`BaseModelWithAudit`).
   * Configurar `settings.py`: BD, REST Framework, CORS, variables de entorno.

2. **Definir modelos de datos**

   * **Evento**: título, descripción, fecha, imagen\_url, publicado.
   * **Notificación**: FK a Evento, destinatario, estado, timestamp.
   * **DeviceToken**: FK a User, token, timestamp.
   * **ChatbotKnowledgeBase** (tu clase): topic, question, answer, keywords, is\_active + auditing.

3. **Configuración de roles y permisos**

   * En Admin (o migración inicial), crear **Grupos**:

     * **SuperAdmin**: todos los permisos.
     * **EventManager**: puede crear/editar/borrar Eventos y Notificaciones.
     * **Viewer**: sólo puede listar Eventos/Feed/Notificaciones.
     * **KBManager**: puede CRUD sobre `ChatbotKnowledgeBase`.
   * Asignar **permisos de modelo** a cada grupo en `admin.site`.

4. **Migraciones y verificación**

   * `makemigrations` / `migrate`.
   * Probar en shell la creación de Usuarios en cada grupo y verificar permisos básicos.

---

## 🔗 FASE 2 – API CRUD & Feed y Control de Acceso (Semana 2)

1. **Eventos CRUD**

   * Serializers + ViewSets para Evento.
   * **Permisos personalizados**:

     * `IsInGroup('EventManager')` para create/update/delete.
     * `AllowAny` o `IsAuthenticated` para list/retrieve.

2. **Feed móvil**

   * Endpoint `/api/feed/` que:

     * Filtra `Evento.objects.filter(publicado=True)`.
     * Ordena por fecha descendente.
     * Devuelve id, título, extracto descripción, fecha, imagen\_url, autor.

3. **ChatbotKnowledgeBase CRUD (Admin)**

   * Serializers + ViewSets para tu `ChatbotKnowledgeBase`.
   * **Permisos**: sólo `KBManager` y `SuperAdmin` pueden create/update/delete.
   * Endpoint público `/api/chatbot/knowledge/` `GET` para listar **sólo** entradas con `is_active=True`.

4. **Notificaciones internas**

   * Signal en Evento `post_save` si `publicado=True` → crea Notificación (`estado='pendiente'`).
   * Permisos: sólo `EventManager` puede disparar señales creando Eventos publicados.

---

## 🔔 FASE 3 – Push Notifications & Dispositivos (Semana 3)

1. **Integración Push**

   * Configurar credenciales FCM/OneSignal.
   * Script/servicio interno que:

     * Obtiene Notificaciones `estado='pendiente'`.
     * Envía push a todos los DeviceTokens.
     * Marca `estado='enviado'`.

2. **Registro de dispositivos**

   * Endpoint `POST /api/devices/` → sólo usuarios autenticados (`IsAuthenticated`) pueden registrar su token.
   * Endpoint `DELETE /api/devices/{id}/` → propietario del token o `SuperAdmin` puede eliminar.

3. **Historial in-app**

   * Endpoint `GET /api/notificaciones/` → lista notificaciones enviadas.
   * Permisos: `IsAuthenticated`.

---

## 🤖 FASE 4 – Chatbot & Búsqueda Inteligente (Semana 4)

1. **Carga de conocimiento**

   * Script de importación desde CSV/JSON a `ChatbotKnowledgeBase`, respetando `is_active`.

2. **Endpoint de Chatbot**

   * `POST /api/chatbot/` { `"question": "texto libre"` }
   * Lógica:

     1. Preprocesar texto (lowercase, strip).
     2. Filtrar `ChatbotKnowledgeBase.objects.filter(is_active=True)`.
     3. Buscar coincidencia por:

        * `keywords__icontains` o
        * `question__icontains`
     4. Ordenar por `relevance_score DESC, updated_at DESC`.
     5. Si hay al menos 1, devolver `{answer: instancia.answer}`; si no, fallback genérico.

3. **Admin & Auditoría**

   * En Admin, asegurarte que `ChatbotKnowledgeBase` tiene:

     * `list_filter = ['topic','is_active']`
     * `search_fields = ['question','keywords']`
   * El `BaseModelWithAudit` registra quién creó y modificó cada entrada.

4. **Pruebas y QA**

   * Casos: pregunta exacta, por keyword, sin match.
   * Validar permisos: sólo roles adecuados CRUD de KB.

---

## 📋 **Endpoints actualizados**

| Ruta                           | Método    | Descripción                           | Permisos                 |
| ------------------------------ | --------- | ------------------------------------- | ------------------------ |
| `/api/eventos/`                | GET       | Listar eventos                        | Any                      |
| `/api/eventos/`                | POST      | Crear evento                          | EventManager             |
| `/api/eventos/{id}/`           | PUT/PATCH | Editar evento                         | EventManager             |
| `/api/eventos/{id}/`           | DELETE    | Borrar evento                         | EventManager             |
| `/api/feed/`                   | GET       | Feed público de eventos publicados    | Any                      |
| `/api/devices/`                | POST      | Registrar token dispositivo           | Authenticated            |
| `/api/devices/{id}/`           | DELETE    | Eliminar token                        | Token owner / SuperAdmin |
| `/api/notificaciones/`         | GET       | Historial de notificaciones (enviado) | Authenticated            |
| `/api/chatbot/`                | POST      | Preguntar al chatbot                  | Any                      |
| `/api/chatbot/knowledge/`      | GET       | Listar entradas activas del KB        | Any                      |
| `/api/chatbot/knowledge/`      | POST      | Crear nueva entrada de KB             | KBManager / SuperAdmin   |
| `/api/chatbot/knowledge/{id}/` | PUT/PATCH | Editar entrada KB                     | KBManager / SuperAdmin   |
| `/api/chatbot/knowledge/{id}/` | DELETE    | Desactivar o borrar entrada KB        | KBManager / SuperAdmin   |

---

### 🚀 **Resumen de integración por roles**

| Grupo            | Permisos clave                                                     |
| ---------------- | ------------------------------------------------------------------ |
| **SuperAdmin**   | Todo acceso (API, KB, Notif, Roles).                               |
| **EventManager** | CRUD sobre eventos y notificaciones (no KB).                       |
| **Viewer**       | Sólo list y retrieve de eventos, feed y notificaciones.            |
| **KBManager**    | CRUD completo sobre `ChatbotKnowledgeBase` (no eventos ni notifs). |

Con esto tienes un **backend plenamente controlado por roles**, un **módulo de chatbot** avanzado soportado por tu nuevo modelo, y todas las **notificaciones push** integradas en tu diagrama de Gantt de 1 mes. ¡A codificar!
