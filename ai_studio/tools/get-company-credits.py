import base64
import json

import requests
from pydantic import BaseModel

BASE_URL = (
    "https://pub-apps.ubitslearning.com/ai_studio_micro/api/v1/credits/company"
)


class GetCompanyCreditsPayload(BaseModel):
    """Payload vacío: la tool no requiere parámetros de negocio."""


def _extract_company_id_from_token(token: str) -> int | None:
    """Decodifica el JWT y extrae company_id de user_metadata."""
    try:
        payload_part = token.split(".")[1]
        payload_part += "=" * (-len(payload_part) % 4)
        decoded_payload = json.loads(
            base64.urlsafe_b64decode(payload_part).decode("utf-8")
        )
        company_id = decoded_payload.get("user_metadata", {}).get("company_id")
        if company_id is None:
            return None
        return int(company_id)
    except Exception:
        return None


def tool(
    payload: GetCompanyCreditsPayload | dict | None = None,
    metadata: dict | None = None,
) -> str:
    """Obtiene la cantidad de créditos actuales de la empresa del usuario autenticado."""
    if payload is not None and not isinstance(payload, dict):
        payload = payload.model_dump()

    meta = metadata or {}
    token = meta.get("token")

    if not token:
        return json.dumps(
            {"ok": False, "error": "Missing authentication token"},
            ensure_ascii=False,
        )

    company_id = _extract_company_id_from_token(token)
    if company_id is None:
        return json.dumps(
            {
                "ok": False,
                "error": "Failed to extract company_id from token user_metadata",
            },
            ensure_ascii=False,
        )

    # company_id es path parameter: solo construye la URL y no va en el body.
    url = f"{BASE_URL}/{company_id}/info"

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
            return json.dumps(
                {
                    "ok": False,
                    "status_code": response.status_code,
                    "error": "Invalid JSON response from credits endpoint",
                },
                ensure_ascii=False,
            )

        if not response.ok:
            return json.dumps(
                {
                    "ok": False,
                    "status_code": response.status_code,
                    "error": response_data,
                },
                ensure_ascii=False,
            )

        attributes = response_data.get("data", {}).get("attributes", {})
        current_balance = attributes.get("current_balance")

        if current_balance is None:
            return json.dumps(
                {
                    "ok": False,
                    "status_code": response.status_code,
                    "error": "current_balance not found in response",
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "ok": True,
                "status_code": response.status_code,
                "data": {"current_balance": current_balance},
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {"ok": False, "error": str(e)},
            ensure_ascii=False,
        )
