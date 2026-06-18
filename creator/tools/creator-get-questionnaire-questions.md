Esta tool obtiene las preguntas de un questionnaire en Creator y devuelve, para cada una, su enunciado y tipo (por ejemplo, opción múltiple, emparejamiento, texto cerrado o ensayo).

**Parámetros**

* **payload (dict)**: Diccionario de entrada para consultar las preguntas de un questionnaire. Debe contener estrictamente las siguientes llaves:

* **questionnaire_id (int)**: ID del questionnaire que se utilizará para construir la URL. Obtener del chat; si falta, preguntar: ID del questionnaire. Este campo es un path parameter y NO debe enviarse en el body.

## payload (ejemplo)

```json
{
  "questionnaire_id": "<int>"
}
```
