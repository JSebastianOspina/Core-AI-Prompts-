import json

import requests
from pydantic import BaseModel, Field

BASE_URL = "https://pub-apps.ubitslearning.com/api/questionnaire/v1"

_HIDDEN_ATTRIBUTES = (
    "title",
    "enable_scoring",
    "enable_time_limited",
    "enable_readonly",
)


def _strip_hidden_attributes(response_data: dict | list | str) -> dict | list | str:
    """Elimina atributos que el agente no debe ver ni usar."""
    if not isinstance(response_data, dict):
        return response_data

    data = response_data.get("data")
    if isinstance(data, dict):
        attributes = data.get("attributes")
        if isinstance(attributes, dict):
            for key in _HIDDEN_ATTRIBUTES:
                attributes.pop(key, None)

    return response_data


class GetQuestionnaireInfoPayload(BaseModel):
    """Payload para consultar la configuración de un questionnaire en Creator.

    - questionnaire_id: ID del questionnaire usado como path parameter.
    """

    questionnaire_id: int = Field(
        description="ID del questionnaire usado como path parameter en la URL."
    )


def tool(payload: GetQuestionnaireInfoPayload, metadata: dict | None = None) -> str:
    """Obtiene la información completa de un questionnaire en Creator."""
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

        if isinstance(response_data, dict):
            response_data = _strip_hidden_attributes(response_data)

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
