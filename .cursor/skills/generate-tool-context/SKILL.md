---
name: generate-tool-context
description: Genera README.md para agentes LangChain multi-tool desde tool.py — descripción en lenguaje natural, sección Parámetros (viñetas por campo del payload) y ejemplo JSON; sin metadata, errores ni validaciones internas. Usa cuando pidan contexto de tool, README para agente o documentación de payload.
---

# Generate Tool Context

Genera un `README.md` en la **misma carpeta** que el `tool.py` analizado. Ese archivo es el contexto que leerá un agente LangChain para invocar la tool correctamente.

El README documenta **solo los parámetros de entrada** que el agente debe enviar en el `payload` de `tool()`. Validaciones, HTTP, timeouts, CSV, errores y respuesta los maneja la función; si algo falla, la tool lo comunica en su retorno — **no** van en el README.

## Estilo de salida: mínimo tokens, solo entrada

El README se inyecta en un **prompt multi-paso con muchas tools**. Documenta únicamente cómo construir el payload; nada más.

### Incluir (obligatorio)

1. **Descripción (lenguaje natural):** 1–3 oraciones **antes** de los parámetros. Explica qué hace la tool en términos de negocio (docstring de `tool()` + docstring del modelo `payload`). Sin detalles técnicos de implementación.
2. **Parámetros:** sección con título `**Parámetros**` y lista con viñetas:
   - Primera viñeta: `**payload (<tipo>)**:` — qué es el diccionario/objeto de entrada y que debe contener las llaves documentadas debajo.
   - Una viñeta por cada campo: `**<campo> (<tipo>)**:` + semántica (docstring/Field) + cómo obtener (`chat` / `preguntar:...` en frase corta).
   - Si el payload es anidado (objetos/listas en el modelo), documenta las llaves internas con el mismo formato (como en el ejemplo de referencia del usuario).
3. **payload (ejemplo):** bloque JSON con **todas** las claves de primer nivel (y estructura anidada si aplica) y placeholders (`<int>`, `<url_https>`, etc.).

### No incluir (prohibido)

- `metadata`, auth, token.
- Secciones **restricciones**, **validaciones**, **errores**, **respuesta**, **salida**.
- Timeouts, headers HTTP, columnas CSV, precondiciones internas, listados de mensajes `error`/`details`.
- Comportamiento inferido solo desde helpers (`validate_csv`, `send_request`, etc.) salvo para aclarar **semántica de un campo** en el docstring del modelo (paso 5).
- Valores del repo, `__main__`, rutas de carpeta como fuente de datos.

### Columna `obtener`

- `chat` o `preguntar:<pregunta corta>` — sin adornos.

### Semántica por campo

Solo texto del **docstring de la clase payload** o `Field(description=...)` de ese campo. No expandir con reglas que la tool aplica después de recibir el payload.

### Tamaño objetivo

- Tools típicas: **~20–45 líneas** (descripción + viñetas + ejemplo JSON). Prioriza claridad del ejemplo; recorta prosa redundante, no campos.

Plantilla: [references/readme-template.md](references/readme-template.md).

## Alcance estricto

Documenta **únicamente** la función cuyo nombre es exactamente `tool`:

```python
def tool(payload: ..., metadata: dict | None = None) -> str:
```

Todo lo demás (`is_request_valid`, `validate_csv`, `send_request`, clases auxiliares no usadas como tipo de entrada, etc.) son implementación interna. Puedes leerlas para inferir significado de parámetros del **payload**, pero **no** las documentes como API del agente.

## Exclusión de `metadata` (obligatorio)

La firma suele incluir `metadata: dict | None = None`. Ese argumento lo inyecta el runtime (autenticación, contexto de sesión, etc.).

**Nunca documentes `metadata` en el README**, incluyendo de forma explícita:

- La clave `token`, JWT, Bearer, API keys o credenciales.
- Tablas, secciones o ejemplos de invocación que muestren `metadata={...}`.
- Cómo obtener, validar o formatear el token.
- Errores del tipo "Missing authentication token" como guía para que el agente pida un token (puedes mencionar genéricamente "error de autenticación" sin decir qué clave enviar).

Puedes leer el uso de `metadata` en el código solo para entender el flujo interno; esa información **no** va al README. El agente LangChain documentado por este README solo debe aprender a construir el **`payload`**.

## Fuentes permitidas y prohibidas para el README

### Puedes leer (no siempre documentar)

- Funciones auxiliares solo si un campo del payload es ambiguo y no hay docstring/Field suficiente (luego fijar significado en el modelo, paso 5).
- **No** uses helpers para rellenar restricciones, errores ni formato de archivos en el README.

### Solo esto puede aparecer en el README

| Fuente | Qué extraer |
|--------|-------------|
| Firma de `tool()` | Tipo de `payload` y retorno |
| Modelo del `payload` (clase en la anotación) | Campos, tipos, req, docstring/`Field` por campo |
| Prompt del usuario en esta sesión | Solo si pidió incluir algo explícito en el README |

### Prohibido en el README

- Bloque `if __name__ == "__main__"`, `print`, llamadas de prueba al pie del archivo.
- Variables o constantes a nivel de módulo (ej. `axs_id = 6615`, `file_url = "https://..."`) como referencia, ejemplo o forma de obtener valores.
- Instrucciones del tipo “revisar el final de `tool.py`” o “ver variables de ejemplo en el código”.
- Valores concretos inventados o tomados del repo (IDs, URLs reales) **salvo** que estén **literalmente** en el docstring del modelo, en `Field(description=...)` con ejemplo explícito, o que el usuario los haya pedido incluir en el prompt.
- Nombres de carpeta/ruta del disco como sustituto de documentación (ej. inferir dominio solo por `massive_assign_csv/` si no está en docstring o parámetros).
- Historial de chat como “valor por defecto” en ejemplos del README (el chat guía al agente en runtime, no se hardcodea en el MD).

### Ejemplos en el README

- Usa placeholders descriptivos: `<assessment_id>`, `<url_publica_del_csv>`, `"<entero>"`.
- Si hace falta mostrar forma, usa tipos/formato (“entero positivo”, “URL HTTP(S)”) según anotaciones y docstrings, no números o URLs del código fuente.

### Cómo obtener cada parámetro (texto en README)

Redacta solo:

1. Lo que diga el docstring/`Field` del campo (significado oficial).
2. Lo que el usuario deba aportar en la conversación al ejecutar el agente.
3. Si falta, **preguntar al usuario** — sin citar `__main__`, constantes del archivo ni rutas del proyecto.

## Flujo de trabajo

### 1. Localizar el archivo

- El usuario suele indicar una ruta (ej. `performance_evaluations/massive_assign_csv/tool.py`).
- Si no la da, busca `tool.py` en el directorio de trabajo o pregunta cuál analizar.

### 2. Extraer la firma de `tool`

Identifica:

| Elemento | Cómo obtenerlo |
|----------|----------------|
| Tipo de `payload` | Anotación del primer parámetro (ej. `MassiveAssignCsvPayload`) |
| `metadata` | Existe en la firma pero **no se documenta** (ver exclusión arriba) |
| Retorno | Anotación de retorno (típicamente `str` con JSON) |
| Docstring de `tool` | Opcional: 1 frase en README solo si ayuda a elegir entre tools similares |

### 3. Resolver el modelo de payload

1. Busca la clase referenciada en el mismo archivo (ej. `class MassiveAssignCsvPayload(BaseModel)`).
2. Lista **cada campo** del modelo con: nombre, tipo anotado, descripción, obligatoriedad.
3. Si el campo tiene `Field(description=...)` o docstring en la clase, úsalo.
4. Si el significado es ambiguo, ve al paso **4** antes de escribir el README.

### 4. Resolver ambigüedad en el código fuente

Si no puedes describir un parámetro con confianza (nombre genérico, sin validación ni uso claro, tipo opaco):

1. **Modifica el archivo `tool.py`** (mínimo cambio necesario):
   - Añade `Field(description="...")` en el modelo Pydantic, o
   - Docstring en la clase del payload explicando cada campo, o
   - Comentario breve encima del campo si `Field` no está disponible en el archivo.
2. Respeta las reglas del repo (ej. sin `print` ni `ValueError` en `performance_evaluations/`).
3. Ejecuta el validador si aplica:

```bash
python performance_evaluations/validate_restricted_builtins.py <ruta-al-archivo.py>
```

4. Vuelve a leer el modelo actualizado y continúa con el README.

No dejes parámetros ambiguos solo en el README: el código fuente debe quedar autodocumentado para futuras ejecuciones.

### 5. Escribir `README.md`

- **Ruta:** mismo directorio que `tool.py`.
- **Idioma:** español técnico (salvo que el usuario pida otro).
- **Formato:** plantilla compacta; revisa que no haya secciones duplicadas antes de guardar.

Autocontrol: ¿hay descripción en lenguaje natural antes de **Parámetros**? ¿Cada llave del payload tiene viñeta `**campo (tipo)**`? ¿JSON de ejemplo completo? ¿Sin errores/restricciones/respuesta/metadata?

### 6. Entregar al usuario

Indica:

- Ruta del `README.md` generado.
- Cambios hechos en `tool.py` (si hubo clarificación de campos).
- Parámetros que el agente debe pedir al usuario cuando falten en el chat.

## Lo que no debes hacer

- Documentar funciones auxiliares como si fueran invocables por el agente.
- Documentar `metadata`, `token`, JWT, Bearer ni ninguna credencial en el README.
- Referenciar `__main__`, variables globales de prueba o “ejemplos al final del archivo”.
- Poner en el README IDs, URLs o tokens tomados del código fuente sin estar explícitos en docstring/`Field`.
- Usar el nombre de la carpeta del repo como fuente de “cómo obtener” parámetros.
- Crear README en otra carpeta que no sea la del `tool.py`.
- Incluir restricciones, errores, respuesta, timeouts o reglas de validación internas.
- Omitir la sección **payload (ejemplo)** o el ejemplo JSON.
- Omitir modificar el código cuando un campo del payload siga ambiguo (preferir docstring/Field en el modelo).

## Ejemplo de formato (referencia)

Descripción en prosa → **Parámetros** con viñetas → JSON ejemplo. Ver estructura en [references/readme-template.md](references/readme-template.md). Para `massive_assign_csv`: payload con `assessment_id` y `file_url` según `MassiveAssignCsvPayload` (no documentar `PostCsvPayload` ni llaves internas que el agente no envía en la firma de `tool()`).

## Checklist final

- [ ] Descripción en lenguaje natural + **Parámetros** (viñetas) + **payload (ejemplo)** JSON.
- [ ] Sin restricciones, errores, respuesta, metadata.
- [ ] Sin metadata/token/`__main__`/valores del repo.
- [ ] Ambigüedad de campo resuelta en docstring/Field del modelo si hizo falta.
- [ ] `README.md` junto a `tool.py`.
