Esta tool actualiza la configuración de un cuestionario (evaluación) en Creator mediante un PUT al servicio de questionnaires.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para actualizar el cuestionario. Debe contener estrictamente las siguientes llaves:

* **questionnaire_id (int)**: ID del cuestionario que se utilizará para construir la URL. Obtener del chat o de la respuesta de creación del questionnaire; si falta, preguntar: ID del cuestionario. Este campo es un path parameter y NO debe enviarse en el body.

* **title (str)**: Título de la evaluación. Obtener del chat; si falta, preguntar: título de la evaluación.

* **enable_scoring (bool)**: Indica si hay calificación con nota mínima de aprobación. Obtener del chat según la configuración acordada con el usuario.

* **min_scoring_approve (int)**: Porcentaje mínimo para aprobar (1–100). Obtener del chat; si falta y `enable_scoring` es true, preguntar: porcentaje mínimo de aprobación.

* **enable_time_limited (bool)**: Indica si la evaluación tiene límite de tiempo. Obtener del chat.

* **time_limit (bool)**: Debe coincidir con `enable_time_limited`. Obtener del chat (mismo valor booleano).

* **time_limit_value (int | None)**: Minutos de límite; null si no hay límite. Obtener del chat; convertir expresiones como "1 hora" a minutos (60).

* **enable_attempts (bool)**: Indica si se configuró límite de intentos. Obtener del chat.

* **attempt_limit (bool)**: Activa el límite de intentos en el cuestionario. Obtener del chat (alineado con la intención de límite de intentos).

* **attempt_limit_value (int | None)**: Número máximo de intentos cuando `attempt_limit` es true. Obtener del chat; si falta y aplica límite, preguntar: cantidad máxima de intentos.

* **attempt_limit_message (str | None)**: Mensaje al agotar intentos sin aprobar. Obtener del chat o usar el mensaje por defecto acordado; puede ser null si no aplica.

* **enable_readonly (bool)**: Modo solo lectura. Obtener del chat; si no se menciona, usar false.

* **questions_random_order (bool)**: Orden aleatorio de preguntas. Obtener del chat.

* **answers_random_order (bool)**: Orden aleatorio de respuestas. Obtener del chat.

* **limit_num_questions (bool)**: Limita cuántas preguntas se muestran por intento. Obtener del chat.

* **num_questions_display (int | None)**: Cantidad de preguntas por intento cuando `limit_num_questions` es true. Obtener del chat; si falta y aplica límite, preguntar: cuántas preguntas mostrar por intento.

## payload (ejemplo)

```json
{
  "questionnaire_id": "<int>",
  "title": "<str>",
  "enable_scoring": true,
  "min_scoring_approve": "<int>",
  "enable_time_limited": true,
  "time_limit": true,
  "time_limit_value": "<int_o_null>",
  "enable_attempts": true,
  "attempt_limit": false,
  "attempt_limit_value": "<int_o_null>",
  "attempt_limit_message": "<str_o_null>",
  "enable_readonly": false,
  "questions_random_order": true,
  "answers_random_order": true,
  "limit_num_questions": true,
  "num_questions_display": "<int_o_null>"
}
```
