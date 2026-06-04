import json

from pydantic import BaseModel


class FinishWorkflowPayload(BaseModel):
    """Payload vacío: la tool no requiere parámetros de negocio."""


def tool(payload: FinishWorkflowPayload | dict | None = None, metadata: dict | None = None) -> str:
    """Marca el flujo de generación de evaluaciones como completado con éxito."""
    if payload is not None and not isinstance(payload, dict):
        payload = payload.model_dump()

    return json.dumps(
        {
            "ok": True,
            "message": "Flujo completado de forma exitosa.",
        },
        ensure_ascii=False,
    )
