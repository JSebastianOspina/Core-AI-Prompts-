import json

import requests
from pydantic import BaseModel, Field


BASE_URL = (
    "https://pub-apps.ubitslearning.com/ai_studio_micro/api/v1/agents/by-code"
)


class GetAgentPriceByCodePayload(BaseModel):
    """Payload de entrada para consultar el precio de un agente por su código.

    - agent_code: Código único del agente (por ejemplo, EXT_EVALUATION_GENERATOR).
    """

    agent_code: str = Field(
        description="Código del agente definido en el system prompt del agente."
    )


def tool(payload: GetAgentPriceByCodePayload, metadata: dict | None = None) -> str:
    """Obtiene el precio de un agente a partir de su código."""
    if not isinstance(payload, dict):
        payload = payload.model_dump()

    meta = metadata or {}
    token = meta.get("token")

    if not token:
        return json.dumps(
            {"ok": False, "error": "Missing authentication token"},
            ensure_ascii=False,
        )

    # agent_code es path parameter: solo construye la URL y no va en el body.
    url = f"{BASE_URL}/{payload['agent_code']}"

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

        price = None
        if isinstance(response_data, dict):
            attributes = response_data.get("data", {}).get("attributes", {})
            if isinstance(attributes, dict):
                price = attributes.get("price")

        return json.dumps(
            {
                "ok": response.ok,
                "price": price,
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {"ok": False, "error": str(e)},
            ensure_ascii=False,
        )
