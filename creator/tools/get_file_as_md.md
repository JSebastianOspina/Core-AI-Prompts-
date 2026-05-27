Esta tool descarga un archivo desde una URL pública y devuelve su contenido convertido a Markdown.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para descargar y convertir el archivo. Debe contener estrictamente las siguientes llaves:

* **file_url (str)**: URL pública (http/https) del archivo a descargar y convertir a Markdown. Obtener del chat; si falta, preguntar: URL del archivo a convertir.

## payload (ejemplo)

```json
{
  "file_url": "<url_https>"
}
```
