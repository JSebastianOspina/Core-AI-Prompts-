import json

import requests
from pydantic import BaseModel, Field

BASE_URL = "https://pub-apps.ubitslearning.com/api/questionnaire/v1"


class PutQuestionnaireInfoPayload(BaseModel):
    """Payload para actualizar la configuración de un questionnaire en Creator.

    - questionnaire_id: ID del questionnaire usado como path parameter.
    - title: Título de la evaluación.
    - enable_scoring: Activa calificación con puntaje mínimo de aprobación.
    - min_scoring_approve: Porcentaje mínimo para aprobar (1–100); aplica si enable_scoring es true.
    - enable_time_limited: Indica si la evaluación tiene límite de tiempo.
    - time_limit: Debe coincidir con enable_time_limited.
    - time_limit_value: Duración en minutos; null si no hay límite de tiempo.
    - enable_attempts: Indica si se configuran intentos limitados.
    - attempt_limit: Activa el límite de intentos en la API.
    - attempt_limit_value: Número máximo de intentos cuando attempt_limit es true.
    - attempt_limit_message: Mensaje al agotar intentos sin aprobar.
    - enable_readonly: Modo solo lectura del cuestionario.
    - questions_random_order: Orden aleatorio de preguntas.
    - answers_random_order: Orden aleatorio de respuestas.
    - limit_num_questions: Limita cuántas preguntas se muestran por intento.
    - num_questions_display: Cantidad de preguntas a mostrar cuando limit_num_questions es true.
    """

    questionnaire_id: int = Field(
        description="ID del questionnaire usado como path parameter en la URL."
    )
    title: str = Field(description="Título de la evaluación.")
    enable_scoring: bool = Field(
        description="Activa calificación; si es false, min_scoring_approve puede ignorarse."
    )
    min_scoring_approve: int = Field(
        description="Porcentaje mínimo para aprobar (entero 1–100)."
    )
    enable_time_limited: bool = Field(
        description="true si la evaluación tiene límite de tiempo."
    )
    time_limit: bool = Field(
        description="Debe enviarse con el mismo valor que enable_time_limited."
    )
    time_limit_value: int | None = Field(
        default=None,
        description="Minutos de límite; null si no hay límite de tiempo.",
    )
    enable_attempts: bool = Field(
        description="true si el usuario configuró límite de intentos."
    )
    attempt_limit: bool = Field(
        description="Activa el límite de intentos en el cuestionario."
    )
    attempt_limit_value: int | None = Field(
        default=None,
        description="Número máximo de intentos cuando attempt_limit es true.",
    )
    attempt_limit_message: str | None = Field(
        default=None,
        description="Mensaje mostrado al agotar intentos sin alcanzar la nota mínima.",
    )
    enable_readonly: bool = Field(description="Modo solo lectura del cuestionario.")
    questions_random_order: bool = Field(description="Orden aleatorio de preguntas.")
    answers_random_order: bool = Field(description="Orden aleatorio de respuestas.")
    limit_num_questions: bool = Field(
        description="true para mostrar solo un subconjunto de preguntas por intento."
    )
    num_questions_display: int | None = Field(
        default=None,
        description="Cantidad de preguntas por intento cuando limit_num_questions es true.",
    )


def tool(payload: PutQuestionnaireInfoPayload, metadata: dict | None = None) -> str:
    """Actualiza la configuración de un questionnaire en Creator."""
    if not isinstance(payload, dict):
        payload = payload.model_dump()

    meta = metadata or {}
    token = meta.get("token")

    if not token:
        return json.dumps(
            {"ok": False, "error": "Missing authentication token"},
            ensure_ascii=False,
        )

    # questionnaire_id es path parameter: solo construye la URL y no va en el body.
    questionnaire_id = payload["questionnaire_id"]
    url = f"{BASE_URL}/questionnaires/{questionnaire_id}"

    attributes = {
        "title": payload["title"],
        "enable_scoring": payload["enable_scoring"],
        "enable_time_limited": payload["enable_time_limited"],
        "enable_attempts": payload["enable_attempts"],
        "enable_readonly": payload["enable_readonly"],
        "min_scoring_approve": payload["min_scoring_approve"],
        "questions_random_order": payload["questions_random_order"],
        "answers_random_order": payload["answers_random_order"],
        "limit_num_questions": payload["limit_num_questions"],
        "num_questions_display": payload["num_questions_display"],
        "time_limit": payload["time_limit"],
        "time_limit_value": payload["time_limit_value"],
        "attempt_limit": payload["attempt_limit"],
        "attempt_limit_value": payload["attempt_limit_value"],
        "attempt_limit_message": payload["attempt_limit_message"],
    }

    body_payload = {
        "data": {
            "type": "questionnaire",
            "attributes": attributes,
        }
    }

    try:
        response = requests.put(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=body_payload,
            timeout=30,
        )

        try:
            response_data = response.json()
        except Exception:
            response_data = response.text

        if response.status_code == 202:
            return json.dumps(
                {
                    "ok": True,
                    "status_code": 202,
                    "message": (
                        "La configuración del cuestionario fue aceptada y se está procesando. "
                        "Puedes continuar con el siguiente paso del flujo."
                    ),
                    "data": response_data,
                },
                ensure_ascii=False,
            )

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
