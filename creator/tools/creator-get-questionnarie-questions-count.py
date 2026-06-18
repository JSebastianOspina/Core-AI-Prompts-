import json

import requests
from pydantic import BaseModel, Field

BASE_URL = "https://pub-apps.ubitslearning.com/api/questionnaire/v1"


class GetQuestionnaireQuestionsCountPayload(BaseModel):
    """Payload para obtener la cantidad de preguntas de un questionnaire en Creator.

    - questionnaire_id: ID del questionnaire usado como path parameter.
    """

    questionnaire_id: int = Field(
        description="ID del questionnaire usado como path parameter en la URL."
    )


def _count_questions(response_data: dict | list) -> int:
    """Cuenta las preguntas en data del response. Retorna 0 si no hay preguntas."""
    if not isinstance(response_data, dict):
        return 0

    data = response_data.get("data")
    if not isinstance(data, list):
        return 0

    return len(data)


def tool(
    payload: GetQuestionnaireQuestionsCountPayload, metadata: dict | None = None
) -> str:
    """Obtiene la cantidad de preguntas de un questionnaire."""
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
    url = f"{BASE_URL}/questionnaires/{questionnaire_id}/questions"

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

        if not response.ok:
            return json.dumps(
                {
                    "ok": False,
                    "status_code": response.status_code,
                    "data": response_data,
                },
                ensure_ascii=False,
            )

        count = _count_questions(response_data)

        return json.dumps(
            {
                "ok": True,
                "status_code": response.status_code,
                "data": count,
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {"ok": False, "error": str(e)},
            ensure_ascii=False,
        )
