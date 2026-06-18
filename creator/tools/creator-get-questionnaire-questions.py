import json

import requests
from pydantic import BaseModel, Field

BASE_URL = "https://pub-apps.ubitslearning.com/api/questionnaire/v1"


class GetQuestionnaireQuestionsPayload(BaseModel):
    """Payload para obtener las preguntas de un questionnaire en Creator.

    - questionnaire_id: ID del questionnaire usado como path parameter.
    """

    questionnaire_id: int = Field(
        description="ID del questionnaire usado como path parameter en la URL."
    )


def _extract_questions(response_data: dict | list) -> list[dict]:
    """Extrae type y statement de cada pregunta en data[n].attributes."""
    if not isinstance(response_data, dict):
        return []

    questions = []
    for item in response_data.get("data", []):
        attributes = item.get("attributes") or {}
        questions.append(
            {
                "type": attributes.get("type"),
                "statement": attributes.get("statement"),
            }
        )

    return questions


def tool(payload: GetQuestionnaireQuestionsPayload, metadata: dict | None = None) -> str:
    """Obtiene las preguntas de un questionnaire, retornando enunciado y tipo de cada una."""
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

        questions = _extract_questions(response_data)

        return json.dumps(
            {
                "ok": True,
                "status_code": response.status_code,
                "data": questions,
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {"ok": False, "error": str(e)},
            ensure_ascii=False,
        )
