import json
from typing import Literal

import requests


def tool(
    allocation_type: Literal["oneForAll", "onePerUser"],
    payload: dict,
    metadata: dict | None = None,
) -> str:
    """Crea uno o varios planes en Task Manager según la modalidad indicada."""

    meta = metadata or {}
    token = meta.get("token")

    if not token:
        return json.dumps(
            {"ok": False, "error": "Missing authentication token"},
            ensure_ascii=False,
        )

    if allocation_type == "onePerUser":
        url = "https://pub-apps.ubitslearning.com/task-manager/api/v1/task-groups/per-user"
    else:
        url = (
            "https://pub-apps.ubitslearning.com/task-manager/api/v1/task-groups"
        )

    payload["label"] = "ai-made"

    plan_type = payload.get("type")
    if plan_type not in ("ordered", "unordered"):
        payload["type"] = "unordered"

    tasks = payload.get("tasks")
    if isinstance(tasks, list):
        for task in tasks:
            if isinstance(task, dict):
                task["priority"] = 20
                if task.get("assigneeId") is not None:
                    task["assigneeRole"] = "collaborator"

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )

        try:
            response_data = response.json()
        except Exception:
            response_data = response.text

        return json.dumps(
            {
                "ok": response.ok,
                "status_code": response.status_code,
                "data": response_data,
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)