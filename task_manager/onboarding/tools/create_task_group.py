import json
import requests


def tool(
    allocation_type: str, payload: dict, metadata: dict | None = None
) -> str:
    """Crea un plan en Task Manager administrando dinámicamente la distribución

    por usuario, forzando prioridades a 20 y manteniendo la estructura original de tareas.
    """

    meta = metadata or {}
    token = meta.get("token")

    if not token:
        return json.dumps(
            {"ok": False, "error": "Missing authentication token"},
            ensure_ascii=False,
        )

    # ENRUTAMIENTO: Selección de URL según el tipo de distribución
    if allocation_type == "onePerUser":
        url = "https://pub-apps.ubitslearning.com/task-manager/api/v1/task-groups/per-user"
    else:
        url = (
            "https://pub-apps.ubitslearning.com/task-manager/api/v1/task-groups"
        )

    # REGLA DE NEGOCIO OBLIGATORIA: Forzar la etiqueta requerida del sistema
    payload["label"] = "ai-made"

    # VALIDACIÓN DEL TYPE: Asegurar un comportamiento por defecto válido
    plan_type = payload.get("type")
    if plan_type not in ["ordered", "unordered"]:
        payload["type"] = "unordered"

    # REGLA DE NEGOCIO CRÍTICA: Forzar prioridad de tareas en 20 para evitar
    # que planes extensos sean rechazados por restricciones de volumen del backend.
    if "tasks" in payload and isinstance(payload["tasks"], list):
        total_tasks = len(payload["tasks"])
        for i in range(total_tasks):
            task = payload["tasks"][i]
            if isinstance(task, dict):
                task["priority"] = 20

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