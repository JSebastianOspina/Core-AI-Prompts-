Esta tool consulta la configuración de un questionnaire en Creator, incluyendo opciones de calificación, límite de tiempo, intentos y demás atributos del cuestionario.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para consultar un questionnaire. Debe contener estrictamente las siguientes llaves:

* **questionnaire_id (int)**: ID del questionnaire que se utilizará para construir la URL. Obtener del chat; si falta, preguntar: ID del questionnaire. Este campo es un path parameter y NO debe enviarse en el body.

## payload (ejemplo)

```json
{
  "questionnaire_id": "<int>"
}
```
