Esta tool consulta un questionnaire en Creator y devuelve la cantidad de preguntas que contiene. Si el cuestionario no tiene preguntas, el resultado es cero.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para consultar la cantidad de preguntas de un questionnaire. Debe contener estrictamente las siguientes llaves:

* **questionnaire_id (int)**: ID del questionnaire que se utilizará para construir la URL. Obtener del chat; si falta, preguntar: ID del questionnaire. Este campo es un path parameter y NO debe enviarse en el body.

## payload (ejemplo)

```json
{
  "questionnaire_id": "<int>"
}
```
