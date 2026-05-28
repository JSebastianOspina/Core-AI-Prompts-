import json

import requests
from pydantic import BaseModel
from markitdown import MarkItDown

MAX_FILE_SIZE_MB = 25
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # docx
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # xlsx
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # pptx
    "application/vnd.ms-excel",  # xls
    "text/plain",  # txt
}


class GetFileAsMdPayload(BaseModel):
    """Payload de entrada para descargar un archivo desde una URL y convertirlo a Markdown.

    - file_url: URL pública (http/https) del archivo que se descargará y convertirá a Markdown.
    """

    file_url: str
    should_validate: bool = True


def _validate_file(response: requests.Response) -> str | None:
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if len(response.content) > max_bytes:
        size_mb = len(response.content) / (1024 * 1024)
        return (
            f"El archivo excede el tamaño máximo permitido "
            f"({MAX_FILE_SIZE_MB} MB): {size_mb:.2f} MB"
        )

    content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        return (
            f"Tipo de archivo no permitido (Content-Type: {content_type or 'ausente'}). "
            "Solo se aceptan: pdf, docx, xlsx, xls, pptx."
        )

    return None


def tool(payload: GetFileAsMdPayload, metadata: dict | None = None) -> str:
    """Descarga un archivo desde la URL indicada y devuelve su contenido convertido a Markdown."""
    if not isinstance(payload, dict):
        payload = payload.model_dump()

    file_url = payload["file_url"]

    try:
        response = requests.get(file_url, timeout=30)
        response.raise_for_status()

        if payload["should_validate"]:
            validation_error = _validate_file(response)
            if validation_error:
                return json.dumps(
                    {"ok": False, "error": validation_error},
                    ensure_ascii=False,
                )

        result = MarkItDown().convert(response)

        return json.dumps(
            {
                "ok": True,
                "status_code": response.status_code,
                "data": result.text_content,
            },
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {"ok": False, "error": str(e)},
            ensure_ascii=False,
        )



file_url = "https://public-resources.ubitslearning.com/core-ai/conversation-files/9a9c9ae1-1785-4897-9b0d-59bdde302897/158928eb-fc10-4115-b78a-29b0512fd1cc_excel_con_nombres_y_edades_aleatorias.txt"
get_file_as_md = GetFileAsMdPayload(file_url=file_url, should_validate=True)
print(tool(get_file_as_md))

