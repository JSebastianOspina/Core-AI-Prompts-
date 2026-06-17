Esta tool descarga un archivo desde una URL pública y devuelve su contenido convertido a Markdown.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para descargar y convertir el archivo. Debe contener estrictamente las siguientes llaves:

* **file_url (str)**: URL pública (http/https) del archivo a descargar y convertir a Markdown. Obtener del chat; si falta, preguntar: URL del archivo a convertir.

* **should_validate (bool)**: Si es `true`, la tool valida el archivo antes de convertirlo. Si es `false`, omite esa validación. Opcional; por defecto `true`. Obtener del chat cuando el agente deba forzar u omitir la validación; si no aplica, usar el valor por defecto.

## payload (ejemplo)

```json
{
  "file_url": "<url_https>",
  "should_validate": true
}
```

## Respuesta

- **Éxito:** devuelve el contenido del archivo convertido a Markdown como string (texto plano, no JSON).
- **Error:** devuelve un JSON string con la forma `{"ok": false, "error": "<mensaje>"}`.
