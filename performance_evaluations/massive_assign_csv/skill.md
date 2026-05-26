# Asignación Masiva de Usuarios para Evaluaciones 360

## Objetivo

Esta skill dota al agente de la capacidad operativa para guiar a administradores en la asignación masiva de **evaluados** a una Evaluación de Desempeño 360. Resuelve el problema de configuración inicial utilizando un archivo CSV referenciado por URL pública; la tool descarga el archivo, valida su estructura, obtiene las evaluaciones activas del assessment y ejecuta la asignación automática de evaluadores según el organigrama.

## Restricción crítica: sin `query_file`

**Está prohibido invocar la tool `query_file` en cualquier momento de este flujo.** No podrás leer, extraer ni inspeccionar el contenido del CSV por tu cuenta ni mediante otras tools de lectura de archivos.

- El archivo lo sube el usuario en el chat; la plataforma expone su **URL pública** (`file_url`) en el contexto del mensaje o del adjunto.
- Debes usar **únicamente** esa URL en el payload de asignación. La descarga, validación y envío las realiza internamente `performance-evaluations-post-massive-assign-csv`.

## Flujo recomendado

1. **Verificar o solicitar ID:** Comprueba en tu contexto si ya posees el `assessment_id` (ID de la evaluación 360). Si no lo tienes, solicítalo al usuario explícitamente.

2. **Instruir al usuario:**

   - Entrega el formato oficial de carga: [Descargar Plantilla CSV](https://lxp.cdn.ubitslearning.com/assets/csv-templates/talent/360/massive-assignations.csv).
   - Explica brevemente la lógica: el archivo debe tener **una sola columna** con encabezado `username` y un username de **evaluado** por fila. El sistema buscará a los evaluadores en el organigrama (pares, líderes, subordinados, autovaloración, etc., según las evaluaciones activas del assessment). Advierte que un organigrama desactualizado generará asignaciones erróneas.
   - Si el usuario pregunta qué tipos de evaluación aplican o para quiénes rige el proceso, consulta la sección **Consulta de tipos de evaluación (opcional)** más abajo. En el flujo normal de carga **no** consultes tipos por adelantado.

3. **Recepción del archivo y URL:**

   - Cuando el usuario suba un CSV, localiza en el contexto la **URL pública** del adjunto (`file_url`). No intentes validar, resumir ni leer el contenido del archivo.
   - **REGLA DE ACCIÓN DIRECTA:** Si el usuario sube un archivo nuevo en cualquier momento (corrección o segundo intento), **ignora todo archivo o URL anterior y actúa de inmediato**. NO pidas confirmación ni preguntes si desea continuar.
   - Si falta `assessment_id` o `file_url`, pide solo lo que falte antes de ejecutar la tool.

4. **Ejecución de asignación:** Ejecuta automáticamente `performance-evaluations-post-massive-assign-csv` pasando un único argumento **`payload`** (`dict`) con `assessment_id` (entero) y `file_url` (cadena HTTPS de la URL pública del CSV).

5. **Cierre:** Si la respuesta indica éxito (`ok: true`), informa al usuario que la validación y el envío fueron correctos, que el proceso es asíncrono y que podrá ver los resultados en la plataforma en unos minutos (o recibirá un correo si hay un fallo interno). Traduce el mensaje de la tool a lenguaje claro; no cites JSON crudo salvo que ayude a corregir el CSV.

## Consulta de tipos de evaluación (opcional)

Usa `performance-evaluations-get-evaluation-types-code` **solo** si el usuario pregunta **explícitamente** por sus evaluaciones, qué tipos están activos o para quiénes aplicará la asignación. En ese caso:

- Ejecuta la tool de forma oculta con el `assessment_id` y guarda mentalmente los campos `id` y `type` de las evaluaciones activas para explicar al usuario.
- Lista **únicamente** las evaluaciones activas. Si "Cliente Interno" está activa, advierte que su asignación **no** se hace por este medio (debe ser manual o por su propio flujo). Si está inactiva, ignórala por completo.
- Esta consulta **no** forma parte del payload de asignación: la tool de asignación masiva resuelve internamente las evaluaciones activas.

## Validaciones (responsabilidad del agente antes de llamar la tool)

- **`payload`:** Objeto `dict` con exactamente las llaves `assessment_id` y `file_url`. No envíes campos adicionales.
- **`payload.assessment_id`:** Siempre número entero (`int`). Obtener del contexto o pedirlo al usuario.
- **`payload.file_url`:** Siempre cadena (`str`) con la URL HTTPS pública del CSV tal como la entrega la plataforma al subir el archivo. No construyas URLs inventadas ni uses rutas locales.
- **No inferir enums ni armar `evaluations`:** La tool obtiene y filtra las evaluaciones activas; el agente no debe traducir ni adivinar tipos (`PEER`, `DOWNWARD`, etc.) dentro del `payload`.

## Manejo de errores

Interpreta la respuesta JSON de `performance-evaluations-post-massive-assign-csv` (`ok`, `error`, `details`, `message`):

- **Error de validación del CSV** (contenido inválido, columna incorrecta, username vacío, archivo vacío, etc.): Traduce `details` a lenguaje amable y no técnico. Indica la regla o fila que falló cuando la tool lo precise. Pide al usuario que corrija el archivo y lo suba de nuevo; al recibir el nuevo adjunto, aplica la regla de acción directa con la nueva `file_url`.
- **Error al descargar el archivo** (HTTP, URL inválida o inaccesible): Indica que no se pudo acceder al CSV y que verifique que el archivo se subió correctamente o que vuelva a subirlo.
- **Sin evaluaciones activas:** Explica que no hay evaluaciones activas para ese assessment y que revise la configuración en la plataforma.
- **Error 4xx/5xx u otros fallos de red:** Para fallos temporales del servidor, responde: *"Ha ocurrido un problema temporal en nuestros servidores al intentar procesar tu solicitud. Por favor, espera unos minutos y vuelve a intentarlo."*
- **Token o campos obligatorios faltantes:** No expongas detalles técnicos del token; indica que no se pudo completar la operación y que intente de nuevo desde la sesión.

## Uso de tools

| Tool | Propósito | Parámetro | Tipo | Requerido | Cómo obtenerlo | Transformación | Ejemplo |
|------|-----------|-----------|------|-----------|----------------|----------------|---------|
| `performance-evaluations-post-massive-assign-csv` | Descargar el CSV desde la URL, validar su estructura, resolver las evaluaciones activas del assessment y ejecutar la asignación masiva de evaluadores según el organigrama | **`payload`** (`dict`): objeto de entrada con **solo** estas llaves obligatorias.<br><br>• **`assessment_id`** (`int`): ID numérico de la evaluación 360 (assessment / axs definition).<br>• **`file_url`** (`str`): URL **HTTPS pública** del CSV subido por el usuario; una columna `username` y un evaluado por fila (la tool valida el formato al descargarlo).<br><br>No incluyas `evaluations`, `csv_content` ni otros campos: la tool los resuelve internamente. | `dict` | Sí | **`assessment_id`:** contexto del chat o pedir explícitamente el ID de la evaluación 360.<br>**`file_url`:** URL pública del adjunto al subir el CSV en el chat; nunca uses `query_file` ni rutas locales. | Enviar el objeto `payload` tal cual; `assessment_id` como entero y `file_url` sin modificar la URL | `{"assessment_id": 8594, "file_url": "https://public-resources.ubitslearning.com/.../massive-assignations.csv"}` |

**Tool opcional (fuera del flujo de carga):** `performance-evaluations-get-evaluation-types-code` — solo si el usuario pregunta qué evaluaciones están activas; parámetro `assessment_id` (`int`), mismo ID del assessment. Ver sección **Consulta de tipos de evaluación (opcional)**.

**Tools prohibidas en este flujo:** `query_file` y cualquier herramienta equivalente de lectura de archivos.

## Ejemplos

**Ejemplo de interacción exitosa y rápida**

**Usuario:** "Tengo este archivo para asignar evaluados en la evaluación 8594." *[Sube usuarios.csv]*

**Agente (pensamiento interno):**

1. Detecto `assessment_id` 8594 y `file_url` del adjunto en el contexto.
2. Ejecuto `performance-evaluations-post-massive-assign-csv` con `payload`: `{"assessment_id": 8594, "file_url": "<url del adjunto>"}`.
3. La tool valida el CSV, resuelve evaluaciones activas y envía la asignación. Retorna éxito.

**Agente (respuesta):** "He procesado el archivo que subiste para la evaluación 8594. El documento pasó la validación y envié la solicitud de asignación masiva según las evaluaciones activas y tu organigrama. El proceso es asíncrono; en unos minutos verás los resultados en la plataforma."

**Ejemplo de loop de corrección (sin pedir confirmación)**

**Usuario:** "Aquí está el archivo corregido." *[Sube usuarios_v2.csv]*

**Agente (pensamiento interno):**

1. Nuevo adjunto: ignoro la URL anterior y tomo la nueva `file_url`.
2. Ejecuto de inmediato `performance-evaluations-post-massive-assign-csv` con `payload` actualizado: mismo `assessment_id` del contexto y la nueva `file_url`.
3. Si falla validación, explico el error y pido otra corrección; si tiene éxito, confirmo el envío.

**Ejemplo: usuario pregunta qué evaluaciones aplican**

**Usuario:** "¿Qué tipos de evaluación se asignan con este CSV en la 8594?"

**Agente:** Ejecuta `performance-evaluations-get-evaluation-types-code` con `8594`, lista solo las activas, advierte sobre Cliente Interno si aplica, y **no** ejecuta la asignación hasta que el usuario suba un archivo.

## Estructura de `payload` (referencia)

```json
{
  "assessment_id": 8594,
  "file_url": "https://public-resources.ubitslearning.com/core-ai/conversation-files/.../massive-assignations.csv"
}
```

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `assessment_id` | `int` | Sí | ID de la evaluación 360 sobre la que se ejecuta la asignación masiva. |
| `file_url` | `str` | Sí | URL HTTPS pública del CSV con encabezado `username` y un username de evaluado por fila. |
