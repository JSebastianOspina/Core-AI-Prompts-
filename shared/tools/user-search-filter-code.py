import json
import requests

def tool(
    payload: dict,
    metadata: dict | None = None) -> str:
    """Busca y filtra usuarios bajo criterios específicos y paginación."""

    meta = metadata or {}
    token = meta.get("token")

    if not token:
        return json.dumps(
            {
                "ok": False,
                "error": "Missing authentication token"
            },
            ensure_ascii=False
        )

    # La URL no recibe variables en el path, los datos se envían en el body
    url = "https://pub-apps.ubitslearning.com/user_search/api/v1/users/filter"

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
            ensure_ascii=False
        )

    except Exception as e:
        return json.dumps(
            {
                "ok": False,
                "error": str(e),
            },
            ensure_ascii=False
        )