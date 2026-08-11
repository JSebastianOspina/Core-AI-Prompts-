import json
from typing import Any

import requests
from pydantic import BaseModel


def _normalize_org_response(data: Any) -> dict:
    if data is None:
        return {"subordinates": []}

    if isinstance(data, list):
        if len(data) == 1 and isinstance(data[0], dict):
            return data[0]
        return {"subordinates": [x for x in data if isinstance(x, dict)]}

    if isinstance(data, dict):
        if "data" in data:
            return _normalize_org_response(data["data"])
        return data

    return {"subordinates": []}


def _safe_children(node: dict) -> list[dict]:
    children = node.get("subordinates")
    return children if isinstance(children, list) else []


def _full_name(node: dict) -> str:
    name = (node.get("name") or "").strip()
    last = (node.get("last_name") or "").strip()
    return f"{name} {last}".strip()


def _dsl_escape(value: str) -> str:
    return (
        value.replace("|", "/")
        .replace("[", "(")
        .replace("]", ")")
    )


def build_dsl(node: dict) -> str:
    if node.get("is_company"):
        return "".join(build_dsl(c) for c in _safe_children(node))

    user_id = node.get("user_id") or ""
    name = _dsl_escape(_full_name(node))
    email = _dsl_escape(node.get("email") or "")
    area = _dsl_escape(node.get("area_name") or "")
    position = _dsl_escape(node.get("position") or "")

    children_dsl = "".join(build_dsl(c) for c in _safe_children(node))

    return f"{user_id}|{name}|{email}|{area}|{position}[{children_dsl}]"


def tool(metadata: dict | None = None) -> str:
    """Punto de entrada obligatorio.
    Retorna el organigrama en DSL ultra compacto.
    """
    meta = metadata or {}
    token = meta.get("token")

    url = "https://pub-apps.ubitslearning.com/org_chart_micro/api/v2/company/collaborators/org-chart?levels=-1"

    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()

        data = resp.json()
        root = _normalize_org_response(data)
        return build_dsl(root)

    except requests.RequestException as e:
        return f"##RequestException ERROR##: {str(e)}"
    except Exception as e:
        return f"## Exception ERROR##: {str(e)}"
