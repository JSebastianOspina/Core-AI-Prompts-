Esta tool crea, una a una, todas las preguntas de un questionnaire haciendo un POST por cada pregunta al endpoint que corresponde a su tipo.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para crear preguntas en un questionnaire. Debe contener estrictamente las siguientes llaves:

* **questionnaire_id (int)**: ID del questionnaire que se utilizará para construir la URL de cada POST. Obtener del chat; si falta, preguntar: ID del questionnaire. Este campo es un path parameter y NO debe enviarse en el body.

* **questions (list[dict])**: Lista de preguntas a crear, en el formato plano producido por el subagente de generación. Cada item se envía al endpoint correspondiente a su `type`. Obtener del subagente de generación de preguntas.

* **questions[].type (str)**: Identificador del tipo de pregunta. Valores soportados: `multiple_choice_single_answer`, `multiple_choice_multiple_answers`, `binary`, `closed_text`, `matching`, `essay`. Obtener del subagente.

* **questions[].statement (str)**: Enunciado de la pregunta. Obtener del subagente.

* **questions[].options (list[dict] | None)**: Opciones de respuesta para `multiple_choice_single_answer`, `multiple_choice_multiple_answers` y `binary`. Cada opción contiene `statement` (str) e `is_correct` (bool). Obtener del subagente.

* **questions[].matching_options (list[dict] | None)**: Pares de emparejamiento para `matching`. Cada item contiene `term` (str) y `match` (str). Obtener del subagente.

* **questions[].correct_statement (str | None)**: Respuesta correcta para `closed_text`. Obtener del subagente.

* **questions[].accuracy (str | None)**: Modo de comparación para `closed_text`. Valores: `"exact"` o `"approximate"`. Obtener del subagente.

* **questions[].number_words_needed (int | None)**: Mínimo de palabras esperadas para `essay`. Entero entre 1 y 100 inclusive; **no puede ser mayor a 100**. Obtener del subagente.

## payload (ejemplo)

```json
{
  "questionnaire_id": "<int>",
  "questions": [
    {
      "type": "multiple_choice_single_answer",
      "statement": "<str>",
      "options": [
        { "statement": "<str>", "is_correct": true },
        { "statement": "<str>", "is_correct": false }
      ]
    },
    {
      "type": "binary",
      "statement": "<str>",
      "options": [
        { "statement": "Verdadero", "is_correct": true },
        { "statement": "Falso", "is_correct": false }
      ]
    },
    {
      "type": "closed_text",
      "statement": "<str>",
      "correct_statement": "<str>",
      "accuracy": "exact"
    },
    {
      "type": "matching",
      "statement": "<str>",
      "matching_options": [
        { "term": "<str>", "match": "<str>" }
      ]
    },
    {
      "type": "essay",
      "statement": "<str>",
      "number_words_needed": 80
    }
  ]
}
```
