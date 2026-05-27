---
name: tool-creator
description: Transforma especificaciones de APIs, cURL, URLs HTTP, detalles de requests o descripciones funcionales en tools consumibles por agentes de IA, creando siempre un archivo Python con la función `tool` y un archivo Markdown de contexto pareado en el directorio solicitado. Usa esta skill siempre que el usuario pida crear, refinar, documentar o convertir una API, endpoint, cURL, operación de negocio o integración en una tool, o cuando pida generar el contexto/README de una tool existente, incluso si no dice explícitamente "tool" o "herramienta".
---

# Tool Creator

Tu tarea es transformar especificaciones de APIs, comandos cURL o descripciones funcionales en tools claras, compactas y robustas para agentes de IA, y producir simultáneamente el contexto que el agente leerá para invocarlas correctamente.

El objetivo final son dos artefactos pareados en el directorio solicitado:

- `<nombre>.py`: implementación de la tool con un único `payload` Pydantic.
- `<nombre>.md`: contexto que documenta solo cómo construir ese `payload`.

## Flujo obligatorio

1. Analiza el input del usuario.
2. Detecta si corresponde una tool tipo código (hay detalles HTTP) o una tool tipo API (solo descripción funcional).
3. Si hay una petición HTTP, identifica método, URL, path params, query params, body params y headers relevantes.
4. Si hay ambigüedades de parámetros, no generes la tool todavía: muestra una tabla de supuestos y pregunta al usuario.
5. Cuando todo esté claro, escribe los dos archivos en el directorio solicitado.
6. Antes de cerrar, verifica que el `.md` solo documente el payload y que el `.py` esté completo.

## Artefactos de salida obligatorios

La invocación de esta skill debe terminar creando dos archivos en el mismo directorio donde el usuario pidió la tool:

```text
<nombre>.py
<nombre>.md
```

Reglas:

- Ambos archivos deben tener el mismo basename.
- Si el usuario proporciona una ruta `.py`, usa esa ruta para el código y crea el `.md` junto a ella con el mismo basename.
- Si el usuario proporciona solo un directorio, deriva el basename desde el nombre de la tool.
- Si el usuario no proporciona directorio ni ruta, pregunta dónde guardar los archivos antes de crear la tool.
- No entregues solo bloques de código en el chat cuando tengas permisos de escritura en el workspace; escribe los archivos.
- Al final, informa las rutas creadas y los cambios hechos en el `.py` (si hubo clarificación de campos).

## Detección del tipo de tool

Genera una **tool tipo código** cuando el usuario proporcione cualquiera de estos elementos:

- Un cURL.
- Una URL HTTP.
- Método, endpoint, headers, body o detalles técnicos de una request HTTP.
- Una integración que claramente requiere llamar a un servicio externo.

Genera una **tool tipo API** cuando el usuario proporcione únicamente:

- Una descripción funcional.
- Una intención de negocio.
- Una operación abstracta sin detalles HTTP.

Si hay duda entre ambos tipos, prioriza **tool tipo código** cuando exista cualquier señal concreta de request HTTP.

Para tools tipo API, no inventes endpoints, credenciales ni comportamiento de red. Si la operación abstracta no permite código útil sin más datos, pregunta antes de crear los archivos.

## Manejo de ambigüedad

Si un parámetro, tipo, origen o forma de obtención no es claro, no generes inmediatamente la tool final. Primero presenta esta tabla preliminar:

| Parámetro | Tipo asumido | Significado asumido | Cómo se obtiene |
| --- | --- | --- | --- |

Después pregunta al usuario si las suposiciones son correctas. La tool final solo debe generarse cuando los campos necesarios estén claros.

Cuando documentes un campo en el `.md` y no puedas describirlo con confianza (nombre genérico, sin validación ni uso claro, tipo opaco), no dejes la ambigüedad solo en el Markdown. Resuélvela en el código fuente del `.py` con el mínimo cambio necesario:

1. Añade `Field(description="...")` en el modelo Pydantic, o
2. Docstring en la clase del payload explicando cada campo, o
3. Comentario breve encima del campo si `Field` no aplica.

Luego vuelve a derivar el `.md` desde el modelo actualizado. El código fuente debe quedar autodocumentado para futuras ejecuciones.

## Nombre de la tool

Usa kebab-case y esta estructura:

```text
{producto}-{operacion}-code
```

Ejemplos:

- `performance-evaluations-delete-result-ranges-code`
- `users-create-code`
- `surveys-get-results-code`

Si el producto no está explícito, infiérelo desde el dominio, path o recurso principal. Si no se puede inferir con confianza, pregunta.

## Análisis obligatorio de cURL o request HTTP

Cuando el input sea un cURL, URL o request HTTP, detecta automáticamente:

- Método HTTP.
- URL base.
- Path params.
- Query params.
- Body params.
- Headers relevantes.

### Headers

Ignora headers irrelevantes o propios del navegador, como:

- `user-agent`
- `origin`
- `referer`
- `sec-fetch-*`
- `sec-ch-ua-*`
- `cache-control`
- `pragma`
- `priority`

Por defecto, envía solamente:

```python
headers={
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}
```

Incluye headers adicionales solo si el usuario los especifica y son importantes para el comportamiento de la API, por ejemplo `X-Tenant-ID`, `Accept-Language` o una versión de API.

### Path parameters

Detecta dinámicamente IDs o valores variables en la URL.

Ejemplo:

```text
/api/users/123/orders/99
```

Debe transformarse a:

```text
/api/users/{user_id}/orders/{order_id}
```

Los path params:

- Deben existir como campos del modelo Pydantic de payload.
- Deben documentarse como llaves internas de `payload (dict)` en el `.md`.
- Deben usarse únicamente para construir la URL.
- No deben enviarse en el body.
- No deben enviarse como query params.
- Deben tener comentarios explícitos en el código cuando sea útil para evitar confusiones.

### Query params

Detecta query params dinámicos.

Ejemplo:

```text
/users?page=1&status=active
```

Los query params:

- Deben existir como campos del modelo Pydantic de payload.
- Deben documentarse como llaves internas de `payload (dict)` en el `.md`.
- Deben enviarse con `params=query_params`.
- No deben duplicarse en el body.

### Body params

Detecta parámetros enviados en body JSON. Infiere tipos, documéntalos en el modelo Pydantic e inclúyelos en el payload JSON.

Los body params:

- Deben existir como campos del modelo Pydantic de payload.
- Deben enviarse únicamente dentro de `json=body_payload` o `json=payload` cuando todo el payload corresponda al body.
- No deben duplicarse en la URL ni en query params.

## Payload único con Pydantic

Para tools tipo código, la tool tiene una sola entrada funcional: `payload`. La firma usa un modelo Pydantic para documentar el contrato de entrada, y `metadata` queda como último parámetro opcional para autenticación y datos de ejecución.

El modelo Pydantic sirve como contrato de entrada para el agente, pero en runtime el payload puede llegar como `dict`. Por eso, dentro del cuerpo de la función:

- Define una clase `BaseModel` con todos los campos que el agente debe proporcionar.
- Añade docstring en la clase payload o `Field(description="...")` cuando un campo necesite semántica clara para el `.md`.
- Usa `def tool(payload: NombrePayload, metadata: dict | None = None) -> str:`.
- Convierte a dict al inicio si llega un modelo Pydantic: `if not isinstance(payload, dict): payload = payload.model_dump()`.
- Accede a campos con notación de dict: `payload["campo"]`.
- No uses `payload.campo`, porque en ejecución real suele llegar como dict plano.
- Mantén todos los inputs de negocio dentro del payload, incluidos path params, query params, body params, URLs de archivos y banderas.

Cuando el body forme un objeto complejo, una estructura anidada o un array de objetos:

- Usa modelos Pydantic anidados (`list[ModeloInterno]`, `dict`, `str | None`, etc.) cuando ayuden a explicar la estructura.
- Envía al endpoint solo los campos que correspondan al body.
- Si todo el `payload` corresponde al body, puedes enviar `json=payload`.
- Si el `payload` también contiene path/query params, construye un `body_payload` excluyendo los campos que no pertenecen al body.

## Código Python obligatorio

El `.py` debe:

- Usar `requests`.
- Usar `json`.
- Usar `BaseModel` de `pydantic`.
- Usar typing moderno: `list[int]`, `dict | None`, `str`, `bool`, `float`, etc.
- Exponer una sola entrada funcional llamada `payload`, tipada con un modelo Pydantic.
- Definir modelos Pydantic para el payload completo y modelos anidados cuando existan listas u objetos internos.
- Documentar el significado de los campos en el modelo Pydantic mediante docstring o `Field(description="...")`, para que el `.md` pueda derivarse del contrato de entrada.
- Incluir `metadata: dict | None = None` como último parámetro opcional.
- Obtener el token con `metadata.get("token")`.
- Validar que exista token y devolver error serializado si falta.
- Manejar errores con `try/except`.
- Retornar siempre un JSON serializado como string.
- Usar `timeout=30`.
- Usar `params=query_params` cuando existan query params.
- Usar `json=body_payload` o `json=payload` solo cuando exista body.
- No enviar `json=` si la request no tiene body.
- Agregar comentarios aclaratorios importantes, especialmente para path params que no deben enviarse en body.

### Plantilla base

Ajusta `requests.METHOD` al método real en minúsculas (`requests.get`, `requests.post`, `requests.patch`, etc.). No mantengas placeholders en la respuesta final.

```python
import json
import requests
from pydantic import BaseModel


class ToolPayload(BaseModel):
    """Payload de entrada para ejecutar la operación.

    - resource_id: ID del recurso usado para construir la URL.
    - name: Nombre que se enviará en el body.
    - active: Estado que se enviará en el body.
    """

    resource_id: int
    name: str
    active: bool


def tool(payload: ToolPayload, metadata: dict | None = None) -> str:
    """Ejecuta la operación sobre el recurso indicado."""
    if not isinstance(payload, dict):
        payload = payload.model_dump()

    meta = metadata or {}
    token = meta.get("token")

    if not token:
        return json.dumps(
            {
                "ok": False,
                "error": "Missing authentication token",
            },
            ensure_ascii=False,
        )

    # resource_id es path parameter: solo construye la URL y no va en el body.
    url = f"https://api.example.com/resources/{payload['resource_id']}"

    body_payload = {
        "name": payload["name"],
        "active": payload["active"],
    }

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=body_payload,
            timeout=30,
        )

        try:
            response_data = response.json()
        except Exception:
            response_data = response.text

        return json.dumps(
            {
                "ok": response.ok,
                "status_code": response.status_code,
                "data": response_data,
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {
                "ok": False,
                "error": str(e),
            },
            ensure_ascii=False,
        )
```

### Variante con path params

```python
import json
import requests
from pydantic import BaseModel


class GetOrderPayload(BaseModel):
    """Payload de entrada para consultar una orden.

    - user_id: ID del usuario usado como path parameter.
    - order_id: ID de la orden usado como path parameter.
    """

    user_id: int
    order_id: int


def tool(payload: GetOrderPayload, metadata: dict | None = None) -> str:
    """Obtiene una orden específica de un usuario."""
    if not isinstance(payload, dict):
        payload = payload.model_dump()

    meta = metadata or {}
    token = meta.get("token")

    if not token:
        return json.dumps(
            {"ok": False, "error": "Missing authentication token"},
            ensure_ascii=False,
        )

    # user_id y order_id son path parameters: solo construyen la URL y no van en body.
    url = (
        "https://api.example.com/api/users/"
        f"{payload['user_id']}/orders/{payload['order_id']}"
    )

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        try:
            response_data = response.json()
        except Exception:
            response_data = response.text

        return json.dumps(
            {
                "ok": response.ok,
                "status_code": response.status_code,
                "data": response_data,
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {"ok": False, "error": str(e)},
            ensure_ascii=False,
        )
```

### Variante con query params

```python
query_params = {
    "page": payload["page"],
    "status": payload["status"],
}

response = requests.get(
    url,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    },
    params=query_params,
    timeout=30,
)
```

### Variante sin body

Si el endpoint no tiene body, no envíes `json=`.

```python
response = requests.delete(
    url,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    },
    timeout=30,
)
```

## Archivo `.md` de contexto

El `.md` se inyecta en un prompt multi-paso con muchas tools. Su único objetivo es enseñarle al agente cómo construir el `payload` que se enviará a `tool()`. No es un README humano ni documentación técnica de implementación.

### Alcance estricto

Documenta **únicamente** la función cuyo nombre es exactamente `tool`:

```python
def tool(payload: ..., metadata: dict | None = None) -> str:
```

Todo lo demás (`is_request_valid`, `validate_csv`, `send_request`, clases auxiliares no usadas como tipo de entrada, etc.) es implementación interna. Puedes leerlas para inferir el significado de los campos del payload, pero no las documentes como API del agente.

### Exclusión de `metadata`

La firma incluye `metadata: dict | None = None`. Ese argumento lo inyecta el runtime (autenticación, contexto de sesión, etc.).

Nunca documentes `metadata` en el `.md`, incluyendo de forma explícita:

- La clave `token`, JWT, Bearer, API keys o credenciales.
- Tablas, secciones o ejemplos de invocación que muestren `metadata={...}`.
- Cómo obtener, validar o formatear el token.
- Errores tipo "Missing authentication token" como guía para que el agente pida un token (puedes mencionar genéricamente "error de autenticación" sin decir qué clave enviar).

El agente documentado por este `.md` solo debe aprender a construir el `payload`.

### Estructura obligatoria

Incluye únicamente:

1. Una descripción en lenguaje natural de 1 a 3 oraciones antes de los parámetros. Explica qué hace la tool en términos de negocio (docstring de `tool()` + docstring del modelo `payload`). Sin detalles técnicos de implementación.
2. Una sección `**Parámetros**` con viñetas:
   - Primera viñeta: `**payload (<tipo>)**:` — qué es el diccionario de entrada y que debe contener las llaves documentadas debajo.
   - Una viñeta por cada campo del payload: `**<campo> (<tipo>)**:` + semántica (docstring/`Field`) + cómo obtenerlo.
   - Si el payload es anidado (objetos o listas en el modelo), documenta las llaves internas con el mismo formato (`data[].order`, `data[].maxValue`, etc.).
3. Una sección `## payload (ejemplo)` con un bloque JSON que cubra todas las claves de primer nivel (y estructura anidada si aplica) usando placeholders descriptivos (`<int>`, `<url_https>`, `<str>`, `<float>`, etc.).

### Columna `obtener`

Para cada campo, indica brevemente cómo obtenerlo:

- `chat` cuando viene de la conversación.
- `preguntar: <pregunta corta>` cuando hay que pedírselo explícitamente al usuario.

Sin adornos ni párrafos largos.

### Semántica por campo

La descripción de cada campo proviene únicamente de:

1. El docstring de la clase payload.
2. `Field(description=...)` en ese campo.
3. Lo que el usuario aporte en la conversación.

No expandas con reglas que la tool aplique después de recibir el payload (validaciones, mensajes de error, headers, timeouts).

### No incluir

No incluyas en el `.md`:

- `metadata`, auth, token, JWT, Bearer, API keys ni credenciales.
- Secciones de restricciones, validaciones, errores, respuesta o salida.
- Headers HTTP, timeouts, status codes, columnas CSV, precondiciones internas, listados de mensajes de error/detalles.
- Comportamiento inferido solo desde helpers (`validate_csv`, `send_request`, etc.) salvo para aclarar la semántica de un campo del modelo.
- Funciones auxiliares como si fueran invocables por el agente.
- Valores reales tomados del repo, variables de prueba, bloques `if __name__ == "__main__"`, tokens, IDs o URLs locales.
- Constantes a nivel de módulo (por ejemplo `axs_id = 6615`, `file_url = "https://..."`) como referencia o forma de obtener valores.
- Instrucciones tipo "revisar el final de `tool.py`" o "ver variables de ejemplo en el código".
- Nombres de carpeta o ruta del disco como sustituto de documentación.
- Historial de chat como valor por defecto en los ejemplos (el chat guía al agente en runtime, no se hardcodea en el `.md`).

### Tamaño objetivo

Tools típicas: ~20–45 líneas (descripción + viñetas + ejemplo JSON). Prioriza claridad del ejemplo; recorta prosa redundante, no campos.

### Plantilla del `.md`

````markdown
Esta tool permite ...

**Parámetros**

* **payload (dict)**: Diccionario de entrada de la tool. Debe contener estrictamente las siguientes llaves:

* **campo (tipo)**: Semántica del campo. Obtener del chat; si falta, preguntar: <pregunta corta>.

## payload (ejemplo)

```json
{
  "campo": "<tipo_o_placeholder>"
}
```
````

### Ejemplo simple

````markdown
Esta tool permite consultar una orden específica asociada a un usuario.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para consultar una orden de usuario. Debe contener estrictamente las siguientes llaves:

* **user_id (int)**: ID del usuario que se utilizará para construir la URL. Obtener del chat; si falta, preguntar: ID del usuario. Este campo es un path parameter y NO debe enviarse en el body.

* **order_id (int)**: ID de la orden que se utilizará para construir la URL. Obtener del chat; si falta, preguntar: ID de la orden. Este campo es un path parameter y NO debe enviarse en el body.

## payload (ejemplo)

```json
{
  "user_id": "<int>",
  "order_id": "<int>"
}
```
````

### Ejemplo con payload complejo

````markdown
Esta tool permite definir y crear la escala y los rangos de resultados de una evaluación 360.

**Parámetros**

* **payload (dict)**: Diccionario complejo que contiene la configuración de la escala y los rangos de resultados. Debe contener estrictamente las siguientes llaves principales:

* **scale (str)**: Escala seleccionada por el usuario. Obtener del chat; si falta, preguntar: escala a configurar.

* **data (list[dict])**: Lista de diccionarios que representan los rangos de resultados a crear. Debe construirse a partir de la información indicada por el usuario.

* **data[].order (int)**: Orden del rango dentro de la escala. Obtener del chat; si falta, preguntar: orden de cada rango.

* **data[].maxValue (float)**: Valor máximo del rango. Obtener del chat; si falta, preguntar: valor máximo de cada rango.

* **data[].minValue (float)**: Valor mínimo del rango. Obtener del chat; si falta, preguntar: valor mínimo de cada rango.

* **data[].parameter (str)**: Clave o identificador del rango. Obtener del chat; si falta, preguntar: clave del rango.

* **data[].customLabel (str | None)**: Etiqueta personalizada del rango o null. Obtener del chat; si falta, preguntar: etiqueta personalizada o confirmar null.

* **data[].id (None)**: Valor nulo para creación. Obtener del contrato de la tool.

* **data[].tableUuid (None)**: Valor nulo para creación. Obtener del contrato de la tool.

* **data[].axsDefinitionId (int)**: ID de la definición de evaluación 360 asociada a los rangos. Obtener del chat; si falta, preguntar: ID de la evaluación 360.

## payload (ejemplo)

```json
{
  "data": [
    {
      "id": null,
      "order": "<int>",
      "maxValue": "<float>",
      "minValue": "<float>",
      "parameter": "<str>",
      "tableUuid": null,
      "customLabel": "<str_o_null>",
      "axsDefinitionId": "<int>"
    }
  ],
  "scale": "<str>"
}
```
````

## Fuentes permitidas para construir el `.md`

Solo esto puede aparecer en el `.md`:

| Fuente | Qué extraer |
|--------|-------------|
| Firma de `tool()` | Tipo de `payload` y retorno |
| Modelo del `payload` (clase en la anotación) | Campos, tipos, obligatoriedad, docstring o `Field` por campo |
| Prompt del usuario en esta sesión | Solo si pidió incluir algo explícito en el `.md` |

Funciones auxiliares: léelas solo si un campo del payload sigue ambiguo después del docstring/`Field`. Si las usas para resolver ambigüedad, fija el significado en el modelo Pydantic (paso de "Manejo de ambigüedad"), no en el `.md`.

Para los placeholders del JSON de ejemplo, usa formas descriptivas (`<assessment_id>`, `<url_publica_del_csv>`, `"<entero>"`, "URL HTTP(S)") según anotaciones y docstrings. No uses números, IDs o URLs del código fuente salvo que estén literalmente en el docstring o `Field` con ejemplo explícito.

## Reglas de calidad

La tool final debe:

- Crear los dos artefactos: `<nombre>.py` y `<nombre>.md`, con el mismo basename y directorio.
- Ser fácilmente consumible por agentes.
- Evitar ambigüedad.
- Explicar cómo obtener cada parámetro en el `.md`.
- Separar correctamente path, query y body params.
- No duplicar parámetros entre URL, query y body.
- Producir código funcional listo para ejecutar cuando sea tipo código.
- Mantener el `.md` corto y centrado solo en el payload que el agente debe enviar.

## Checklist final

Antes de cerrar la entrega, revisa:

- ¿El tipo de tool elegido coincide con el input?
- ¿Hay ambigüedades que deban preguntarse primero?
- ¿La función se llama exactamente `tool`?
- ¿`payload` es un modelo Pydantic y `metadata` es el último parámetro opcional?
- ¿Los path params solo están en la URL?
- ¿Los query params solo están en `params=`?
- ¿El body solo contiene campos que pertenecen al body?
- ¿Los headers irrelevantes fueron omitidos?
- ¿El retorno siempre es un string JSON?
- ¿Existe un `.md` con el mismo basename que el `.py`?
- ¿El `.md` documenta solo la función `tool` y omite helpers internos?
- ¿El `.md` omite `metadata`, auth, errores, headers, timeouts, validaciones internas y valores del repo?
- ¿El `.md` incluye descripción, `**Parámetros**` y `## payload (ejemplo)` con placeholders?
- ¿La ambigüedad de cada campo quedó resuelta en docstring o `Field` del modelo Pydantic?
