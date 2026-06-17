import io
import json
import os
from urllib.parse import urlparse

import requests
from pydantic import BaseModel
from markitdown import MarkItDown, StreamInfo

# --- Límites de seguridad ---------------------------------------------------
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
DOWNLOAD_CHUNK_SIZE = 64 * 1024  # 64 KB por chunk para cortar descargas grandes pronto

# Timeouts finos: (conexión, lectura). Evita cuelgues por servidores lentos.
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 30

# --- Restricción de origen (anti-SSRF) -------------------------------------
# Solo se permite descargar desde esta URL base. Esto evita que una URL
# arbitraria apunte a recursos internos o de metadatos de la nube.
# Parametrizable: cambia este valor para autorizar otro origen.
ALLOWED_BASE_URL = "https://public-resources.ubitslearning.com"

# --- Validación de tipo de archivo -----------------------------------------
# Cada extensión declara sus Content-Types aceptados y sus firmas mágicas.
# La validación cruza extensión + Content-Type + firma mágica para no depender
# únicamente de las cabeceras del servidor remoto.
_OOXML_MAGIC = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")  # zip (docx/xlsx/pptx)
_OLE_MAGIC = (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",)  # documentos Office legacy (xls)

EXTENSION_RULES: dict[str, dict] = {
    ".pdf": {
        "content_types": {"application/pdf"},
        "magic": (b"%PDF",),
    },
    ".docx": {
        "content_types": {
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        },
        "magic": _OOXML_MAGIC,
    },
    ".xlsx": {
        "content_types": {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        },
        "magic": _OOXML_MAGIC,
    },
    ".pptx": {
        "content_types": {
            "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        },
        "magic": _OOXML_MAGIC,
    },
    ".xls": {
        "content_types": {"application/vnd.ms-excel"},
        "magic": _OLE_MAGIC + _OOXML_MAGIC,
    },
    ".txt": {
        "content_types": {"text/plain"},
        "magic": None,  # texto plano no tiene firma mágica fiable
    },
}

ALLOWED_CONTENT_TYPES = {
    ct for rule in EXTENSION_RULES.values() for ct in rule["content_types"]
}


class GetFileAsMdPayload(BaseModel):
    """Payload de entrada para descargar un archivo desde una URL y convertirlo a Markdown.

    - file_url: URL pública (https) del archivo que se descargará y convertirá a Markdown.
    """

    file_url: str
    should_validate: bool = True


def _error(message: str) -> str:
    return json.dumps({"ok": False, "error": message}, ensure_ascii=False)


def _handle_error(exc: Exception) -> str:
    """Traduce una excepción de descarga a un mensaje de error legible."""
    if isinstance(exc, requests.exceptions.Timeout):
        return _error("Tiempo de espera agotado al descargar el archivo.")
    if isinstance(exc, requests.exceptions.SSLError):
        return _error("Error de certificado SSL al conectar con el servidor.")
    if isinstance(exc, requests.exceptions.ConnectionError):
        return _error("No se pudo establecer conexión con el servidor.")
    if isinstance(exc, requests.exceptions.HTTPError):
        status = exc.response.status_code if exc.response is not None else "?"
        return _error(f"El servidor respondió con un error HTTP ({status}).")
    if isinstance(exc, ValueError):
        return _error(str(exc))
    if isinstance(exc, requests.exceptions.RequestException):
        return _error("Error al descargar el archivo desde la URL indicada.")
    return _error("Error inesperado al procesar el archivo.")


def _validate_url(file_url: str) -> str | None:
    """Valida que la URL pertenezca al dominio autorizado (defensa anti-SSRF)."""
    if file_url != ALLOWED_BASE_URL and not file_url.startswith(
        ALLOWED_BASE_URL + "/"
    ):
        return f"Dominio no autorizado. Solo se permite descargar desde: {ALLOWED_BASE_URL}."

    return None


def _extension_from_url(file_url: str) -> str:
    path = urlparse(file_url).path
    return os.path.splitext(path)[1].lower()


def _validate_content(
    file_url: str, content_type: str, head_bytes: any
) -> str | None:
    """Valida extensión + Content-Type + firma mágica."""
    extension = _extension_from_url(file_url)
    rule = EXTENSION_RULES.get(extension)
    if rule is None:
        return (
            f"Extensión de archivo no permitida ({extension or 'ausente'}). "
            f"Solo se aceptan: {', '.join(EXTENSION_RULES)}."
        )

    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        return (
            f"Tipo de archivo no permitido (Content-Type: {content_type}). "
            f"Solo se aceptan: {', '.join(EXTENSION_RULES)}."
        )

    expected_magic = rule["magic"]
    if expected_magic and not any(head_bytes.startswith(sig) for sig in expected_magic):
        return (
            "El contenido del archivo no coincide con su extensión "
            f"({extension}). Posible archivo corrupto o manipulado."
        )

    return None


def _download(file_url: str) -> tuple[any, str]:
    """Descarga en streaming sin seguir redirects y con límite estricto de bytes.

    Devuelve (contenido, content_type). Lanza ValueError con un mensaje legible
    ante cualquier condición que deba abortar la descarga.
    """
    with requests.get(
        file_url,
        stream=True,
        allow_redirects=False,  # evita rebotes hacia recursos internos
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
    ) as response:
        if response.is_redirect or 300 <= response.status_code < 400:
            raise ValueError("Redirecciones no permitidas en la descarga.")
        response.raise_for_status()

        content_type = (
            response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        )

        # Corte temprano por Content-Length anunciado (si está presente).
        declared = response.headers.get("Content-Length")
        if declared and declared.isdigit() and int(declared) > MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"El archivo excede el tamaño máximo permitido ({MAX_FILE_SIZE_MB} MB)."
            )

        buffer = io.BytesIO()
        downloaded = 0
        for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            if not chunk:
                continue
            downloaded += len(chunk)
            if downloaded > MAX_FILE_SIZE_BYTES:
                raise ValueError(
                    f"El archivo excede el tamaño máximo permitido "
                    f"({MAX_FILE_SIZE_MB} MB)."
                )
            buffer.write(chunk)

        return buffer.getvalue(), content_type


def tool(payload: GetFileAsMdPayload, metadata: dict | None = None) -> str:
    """Descarga un archivo desde la URL indicada y devuelve su contenido convertido a Markdown."""
    if not isinstance(payload, dict):
        payload = payload.model_dump()

    file_url = payload["file_url"]

    # La validación de URL (anti-SSRF) se aplica SIEMPRE, sin importar should_validate.
    url_error = _validate_url(file_url)
    if url_error:
        return _error(url_error)

    try:
        content, content_type = _download(file_url)
    except (requests.exceptions.RequestException, ValueError) as e:
        return _handle_error(e)

    if payload.get("should_validate", True):
        validation_error = _validate_content(file_url, content_type, content[:8])
        if validation_error:
            return _error(validation_error)

    # El contenido descargado en chunks se entrega como stream en memoria a
    # MarkItDown, indicando extensión y mimetype para guiar la conversión.
    try:
        stream = io.BytesIO(content)
        result = MarkItDown().convert_stream(
            stream,
            stream_info=StreamInfo(
                extension=_extension_from_url(file_url) or None,
                mimetype=content_type or None,
            ),
        )
        return result.text_content
    except Exception:
        return _error("No se pudo convertir el archivo a Markdown.")


if __name__ == "__main__":
    file_url ="https://public-resources.ubitslearning.com/core-ai/conversation-files/eed47b05-27fc-4312-b658-f55a37e97ee1/230eef3d-958f-4499-9060-9e2d11b96cff_bolilla2-transistores.pdf"
    get_file_as_md = GetFileAsMdPayload(file_url=file_url, should_validate=True)
    print(tool(get_file_as_md))
