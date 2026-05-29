import json
import requests
from pydantic import BaseModel

class GetFileAsMdPayload(BaseModel):
    """Payload de entrada para descargar un archivo desde una URL y convertirlo a Markdown.

    - file_url: URL pública (https) del archivo que se descargará y convertirá a Markdown.
    """

    file_url: str
    should_validate: bool = True


def tool(payload: GetFileAsMdPayload, metadata: dict | None = None) -> str:
    """Descarga un archivo desde la URL indicada y devuelve su contenido convertido a Markdown."""
    file_response = requests.get(payload.file_url, timeout=30)

    file_response.raise_for_status()

    file_content = file_response.text

    return  json.dumps({
        "ok": True,
        "data": file_content
    })


file_url = "https://public-resources.ubitslearning.com/core-ai/conversation-files/eed47b05-27fc-4312-b658-f55a37e97ee1/230eef3d-958f-4499-9060-9e2d11b96cff_bolilla2-transistores.pdf"
get_file_as_md = GetFileAsMdPayload(file_url=file_url)
print(tool(get_file_as_md))
