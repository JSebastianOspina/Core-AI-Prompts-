import base64
import json

import requests
from pydantic import BaseModel, Field

CREDITS_BASE_URL = (
    "https://pub-apps.ubitslearning.com/ai_studio_micro/api/v1/credits/company"
)
AGENTS_BASE_URL = (
    "https://pub-apps.ubitslearning.com/ai_studio_micro/api/v1/agents/by-code"
)


class CanUseAgentPayload(BaseModel):
    """Payload de entrada para verificar si la empresa puede usar un agente.

    - agent_code: Código único del agente cuyo precio se comparará con el saldo.
    """

    agent_code: str = Field(
        description="Código del agente definido en el system prompt del agente."
    )


def _extract_company_id_from_token(token: str) -> int:
    """Decodifica el JWT y extrae company_id de user_metadata."""
    payload_part = token.split(".")[1]
    payload_part += "=" * (-len(payload_part) % 4)
    decoded_payload = json.loads(
        base64.urlsafe_b64decode(payload_part).decode("utf-8")
    )
    company_id = decoded_payload.get("user_metadata", {}).get("company_id")
    if company_id is None:
        raise ValueError("Failed to extract company_id from token user_metadata")
    return int(company_id)


def _get_company_credits(token: str) -> int | float:
    """Consulta y retorna el saldo de créditos actual de la empresa."""
    # company_id es path parameter: solo construye la URL y no va en el body.
    company_id = _extract_company_id_from_token(token)
    url = f"{CREDITS_BASE_URL}/{company_id}/info"

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    response_data = response.json()

    current_balance = (
        response_data.get("data", {}).get("attributes", {}).get("current_balance")
    )
    if current_balance is None:
        raise ValueError("current_balance not found in response")

    return current_balance


def _get_agent_price(agent_code: str, token: str) -> int | float:
    """Consulta y retorna el precio del agente indicado."""
    # agent_code es path parameter: solo construye la URL y no va en el body.
    url = f"{AGENTS_BASE_URL}/{agent_code}"

    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    response.raise_for_status()
    response_data = response.json()

    price = response_data.get("data", {}).get("attributes", {}).get("price")
    if price is None:
        raise ValueError("price not found in response")

    return price


def tool(payload: CanUseAgentPayload, metadata: dict | None = None) -> str:
    """Verifica si la empresa tiene créditos suficientes para usar el agente indicado."""
    if not isinstance(payload, dict):
        payload = payload.model_dump()

    token = (metadata or {}).get("token")
    if not token:
        return json.dumps(
            {
                "canUse": False,
                "agentPrice": None,
                "currentBalance": None,
                "error": "Missing authentication token",
            },
            ensure_ascii=False,
        )

    try:
        current_balance = _get_company_credits(token)
    except Exception as e:
        return json.dumps(
            {
                "canUse": False,
                "agentPrice": None,
                "currentBalance": None,
                "error": str(e),
            },
            ensure_ascii=False,
        )

    try:
        agent_price = _get_agent_price(payload["agent_code"], token)
    except Exception as e:
        return json.dumps(
            {
                "canUse": False,
                "agentPrice": None,
                "currentBalance": current_balance,
                "error": str(e),
            },
            ensure_ascii=False,
        )

    if current_balance >= agent_price:
        return json.dumps(
            {
                "canUse": True,
                "agentPrice": agent_price,
                "currentBalance": current_balance,
                "error": None,
            },
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "canUse": False,
            "agentPrice": agent_price,
            "currentBalance": current_balance,
            "error": (
                f"No tienes créditos suficientes para usar este agente. "
                f"Dispones de {current_balance} créditos y el agente requiere {agent_price}."
            ),
        },
        ensure_ascii=False,
    )
