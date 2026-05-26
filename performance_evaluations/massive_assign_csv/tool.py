import csv
import io
import json
import requests
import base64
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from pydantic import BaseModel


class MassiveAssignCsvPayload(BaseModel):
    """Payload de entrada para asignación masiva de participantes vía CSV.

    - assessment_id: ID numérico de la evaluación 360 (assessment / axs definition).
    - file_url: URL pública del archivo CSV con una columna 'username' (un usuario por fila).
    """

    assessment_id: int
    file_url: str


def is_request_valid(
    payload: dict, metadata: dict | None = None
) -> bool | str:
    """Valida el payload de la solicitud.

    Returns:
        True si la solicitud es válida, False si no lo es.
        Mensaje de error si la solicitud no es válida.
    """
    if not metadata or not metadata.get("token"):
        return "Missing authentication token"
    if not payload["assessment_id"] or not payload["file_url"]:
        return "Missing required fields in payload: 'file_url' and 'assessment_id' are mandatory."

    return True


def tool(payload: MassiveAssignCsvPayload, metadata: dict | None = None) -> str:
    """Consulta la información de un archivo, obtiene su URL pública, lo descarga y retorna su contenido."""
    if not isinstance(payload, dict):
        payload = payload.model_dump()

    request_validation = is_request_valid(payload, metadata)
    if isinstance(request_validation, str):
        return handle_error(request_validation)


    try:

        evaluations: list[Evaluation] = get_active_evaluations(
            payload["assessment_id"], metadata=metadata
        )
        if not evaluations:
            return handle_error("No se encontraron evaluaciones activas para el assessment.")


        file_response = requests.get(payload["file_url"], timeout=30)

        file_response.raise_for_status()

        file_content = file_response.text

        validation_error = validate_csv(file_content)
        if validation_error:
            return json.dumps(
                {
                    "ok": False,
                    "error": "Error de validación del CSV",
                    "details": validation_error,
                },
                ensure_ascii=False,
            )

        response = send_request(
            {
                "evaluations": evaluations,
                "assessment_id": payload["assessment_id"],
                "csv_content": file_content,
            },
            metadata=metadata,
        )

        return json.dumps(
            {
                "ok": True,
                "status_code": 200,
                "data": response,
            },
            ensure_ascii=False,
        )

    except HTTPError as e:
        return json.dumps(
            {
                "ok": False,
                "error": "HTTP error",
                "details": str(e),
            },
            ensure_ascii=False,
        )

    except Timeout:
        return json.dumps(
            {"ok": False, "error": "La petición excedió el tiempo límite"},
            ensure_ascii=False,
        )

    except ConnectionError:
        return json.dumps(
            {"ok": False, "error": "Error de conexión"}, ensure_ascii=False
        )

    except json.JSONDecodeError:
        return json.dumps(
            {"ok": False, "error": "La respuesta no es un JSON válido"},
            ensure_ascii=False,
        )

    except RequestException as e:
        return json.dumps(
            {
                "ok": False,
                "error": "Error general de requests",
                "details": str(e),
            },
            ensure_ascii=False,
        )

def handle_error(error: str) -> str:
    return json.dumps(
        {
            "ok": False,
            "error": error,
        },
        ensure_ascii=False,
    )

def validate_csv(
    csv_content: str,
    metadata: dict | None = None,
) -> str | None:
    """Parse y valida el contenido de un CSV asegurando que contenga la columna 'username' y que los datos no vengan vacíos.

    Returns:
        Mensaje de error si la validación falla; None si el CSV es válido.
    """
    if not csv_content or not csv_content.strip():
        return "El contenido del CSV está vacío o es nulo."

    f = io.StringIO(csv_content.strip())
    try:
        reader_lines = list(csv.reader(f))
    except csv.Error as e:
        return str(e)

    if not reader_lines:
        return "El archivo CSV está vacío después de parsear."

    headers = reader_lines[0]

    if len(headers) != 1 or headers[0].strip().lower() != "username":
        return (
            "Formato de CSV inválido. El archivo debe contener exactamente una columna "
            "con el encabezado 'username'."
        )

    usernames = []
    for row in reader_lines[1:]:
        if row:
            username = row[0].strip()
            if not username:
                return (
                    "Se encontró un registro de username vacío. "
                    "Todos los usernames deben tener un valor válido."
                )
            usernames.append(username)

    if not usernames:
        return "El archivo CSV no contiene usernames (lista de datos vacía)."

    return None


class Evaluation(BaseModel):
    id: int
    type: str


class PostCsvPayload(BaseModel):
    evaluations: list[Evaluation]
    assessment_id: int
    csv_content: str


def send_request(payload: PostCsvPayload, metadata: dict) -> str:
    """Sube un archivo CSV y asigna participantes masivamente a evaluaciones activas de un Assessment."""

    # Extracción de parámetros desde el payload único
    assessment_id = payload["assessment_id"]
    evaluations: list[Evaluation] = payload["evaluations"]
    csv_content = payload["csv_content"]

    url = "https://pub-apps.ubitslearning.com/api-talent-360/storage/upload/assignations/csv"
    

    # Extracción dinámica de variables a partir del payload del token JWT
    company_id = None
    sender_email = None
    sender_name = None

    token = metadata.get("token")

    try:
        # Extraer y decodificar el payload del token (segunda parte del JWT)
        payload_part = token.split(".")[1]
        # Añadir padding requerido por base64
        payload_part += "=" * (-len(payload_part) % 4)
        decoded_payload = json.loads(
            base64.urlsafe_b64decode(payload_part).decode("utf-8")
        )

        # Extracción de propiedades según la estructura validada
        company_id = decoded_payload.get("user_metadata", {}).get("company_id")
        sender_email = decoded_payload.get("username")
        sender_name = decoded_payload.get("username")
    except:
        return json.dumps(
            {
                "ok": False,
                "error": "Failed to decode token for required fields. Token parsing error.",
            },
            ensure_ascii=False,
        )

    # Construir el JSON de metadata que el backend espera dentro del multipart
    form_metadata = {
        "evaluations": [evaluation for evaluation in evaluations],
        "axsId": assessment_id,
        "companyId": company_id,
        "senderEmail": sender_email,
        "senderName": sender_name,
    }

    try:
        # Se omite el header de Content-Type deliberadamente; requests lo asigna
        # automáticamente a 'multipart/form-data' junto con su boundary dinámico.
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            data={"metadata": json.dumps(form_metadata)},
            files={
                "file": ("plantilla-asignacion-masiva.csv", csv_content, "text/csv")
            },
            timeout=30,
        )
        response.raise_for_status()

        return json.dumps(
            {
                "ok": response.ok,
                "status_code": response.status_code,
                "message": "Se asignaron los participantes masivamente a las evaluaciones activas. Por favor, verifique el estado de las asignaciones en el sistema.",
            },
            ensure_ascii=False,
        )

    except HTTPError as http_exc:
        # Si es una excepción HTTP, dejar pasar/subir (propagar)
        raise http_exc


def get_active_evaluations(
    axs_definition_id: int, metadata: dict | None = None
) -> list[Evaluation]:
    """Obtiene los tipos de evaluación para una evaluación 360."""

    url = "https://pub-apps.ubitslearning.com/api-talent-360/evaluations"

    # axs_definition_id es un query parameter, NO debe incluirse en payload
    query_params = {"axs_definition_id": axs_definition_id}


    token = metadata.get("token")

    try:
        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            params=query_params,
            timeout=30,
        )
        response.raise_for_status()
        response_data = response.json()

        evaluations = [
            {"id": evaluation["id"], "type": evaluation["evaluation_type"]}
            for evaluation in response_data
            if evaluation.get("active")
        ]

        return evaluations

    except HTTPError as http_exc:
        # Si es una excepción HTTP, dejar pasar/subir (propagar)
        raise http_exc
    except:
        return handle_error("Error al obtener las evaluaciones activas")


token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InhvNDRLZmlsQ0VBS1dUU3hFMFh2bCJ9.eyJ1c2VybmFtZSI6InBydWViYTM2MC5zZWd1bmRvQGdtYWlsLmNvbSIsImxvZ2luc0NvdW50IjoxMTAsInVzZXJfbWV0YWRhdGEiOnsiYXJlYSI6IlRlY2giLCJjaXR5IjoiQWd1YWNoaWNhIiwiY29tcGFueV9pZCI6MjkyMywiY29tcGFueV9uYW1lIjoiRW1wcmVzYSBwYXNlMDIwMzIwMjQiLCJjb3VudHJ5IjoiQ08iLCJsYXN0X21ldGFkYXRhX3VwZGF0ZSI6IjIwMjYtMDUtMjVUMTQ6MzY6MDAuNzQ5WiIsIm1kbF91X2NvbXBhbnlfaWQiOjI5MjMsIm1kbF91X3VzZXJfaWQiOjk5NzQ3Mywib3JnYW5pemF0aW9uX2xldmVsIjoidGFjdGljX3dpdGhvdXRfc3RhZmYiLCJwZXJtaXNzaW9ucyI6WyJhY2Nlc3M6bGVhcm4iLCJhY2Nlc3M6cHJvZHVjdG9zLWJhc2UiLCJhY2Nlc3M6ZXZhbHVhY2lvbmVzLTM2MCIsInVwZGF0ZS1oaXJpbmctbW92ZS1yZWplY3QtY2FuZGlkYXRlczpyZWNsdXRhbWllbnRvIiwicmVhZC11cGRhdGUtaGlyaW5nLXdvcmtmbG93czpyZWNsdXRhbWllbnRvIiwicmVhZC1oaXJpbmctYWdlbnQtYWk6cmVjbHV0YW1pZW50byIsInJlYWQtaGlyaW5nLWNvbmZpZ3VyYXRpb246cmVjbHV0YW1pZW50byIsInVwZGF0ZS1kZWxldGUtaGlyaW5nLWpvYnM6cmVjbHV0YW1pZW50byIsInJlYWQtaGlyaW5nLWpvYnM6cmVjbHV0YW1pZW50byIsInJlYWQtaGlyaW5nLWRhc2hib2FyZDpyZWNsdXRhbWllbnRvIiwiYWNjZXNzOnJlY2x1dGFtaWVudG8iLCJkZWxldGUtdGVtcGxhdGVzOnRhcmVhcy15LXBsYW5lcyIsIndyaXRlLXRlbXBsYXRlczp0YXJlYXMteS1wbGFuZXMiLCJyZWFkLXRlbXBsYXRlczp0YXJlYXMteS1wbGFuZXMiLCJkZWxldGUtcmVwb3J0czp0YXJlYXMteS1wbGFuZXMiLCJkZWxldGUtYWxsOnRhcmVhcy15LXBsYW5lcyIsInVwZGF0ZS1yZXBvcnRzOnRhcmVhcy15LXBsYW5lcyIsInVwZGF0ZS1hbGw6dGFyZWFzLXktcGxhbmVzIiwicmVhZC1yZXBvcnRzOnRhcmVhcy15LXBsYW5lcyIsInJlYWQtYWxsOnRhcmVhcy15LXBsYW5lcyIsImFjY2Vzczp0YXJlYXMteS1wbGFuZXMiLCJjcmVhdGUtdGVtcGxhdGUtc3VydmV5czplbmN1ZXN0YXMiLCJidWxrLXVwbG9hZC1wYXJ0aWNpcGFudHMtc3VydmV5czplbmN1ZXN0YXMiLCJ2aWV3LXJlc3VsdHMtc3VydmV5czplbmN1ZXN0YXMiLCJleHBvcnQtcmVzdWx0cy1zdXJ2ZXlzOmVuY3Vlc3RhcyIsImRvd25sb2FkLXFyLXN1cnZleXM6ZW5jdWVzdGFzIiwic2hhcmUtc3VydmV5czplbmN1ZXN0YXMiLCJhc3NpZ24tcGFydGljaXBhbnRzLXN1cnZleXM6ZW5jdWVzdGFzIiwiZHVwbGljYXRlLXN1cnZleXM6ZW5jdWVzdGFzIiwic2VuZC1yZW1pbmRlci1zdXJ2ZXlzOmVuY3Vlc3RhcyIsInVwZGF0ZS1zdXJ2ZXlzOmVuY3Vlc3RhcyIsImRlbGV0ZS1zdXJ2ZXlzOmVuY3Vlc3RhcyIsImNyZWF0ZS1zdXJ2ZXlzOmVuY3Vlc3RhcyIsImxpc3Qtc3VydmV5czplbmN1ZXN0YXMiLCJhY2Nlc3M6ZW5jdWVzdGFzIiwiYWNjZXNzOmFzc2Vzc21lbnQiLCJtYW5hZ2U6dXN1YXJpb3MiLCJhY2Nlc3M6dXN1YXJpb3MiXSwicG9zaXRpb24iOiJEZXYiLCJyb2xlX2F1dGgwX2lkIjoicm9sX1d6TWU1d2NpdXU5MGRieFIiLCJyb2xlX2F1dGgwX25hbWUiOiJBZG1pbkhSIC0gQWRtaW4gR2VuZXJhbCIsInJvbGVfaWQiOjExLCJyb2xlX3Nob3J0bmFtZSI6InJyaGgiLCJyb2xlcyI6WyJDb2xhYm9yYWRvciIsIkFkbWluaXN0cmFkb3IiXSwidXNlcl9pZCI6ODk1NTc4fSwiaXNzIjoiaHR0cHM6Ly9sb2dpbi51Yml0c2xlYXJuaW5nLmNvbS8iLCJzdWIiOiJhdXRoMHw2NmEzZDEyNjc2ODZhNjQ5YTRkYWQxOWQiLCJhdWQiOlsiaHR0cHM6Ly91Yml0cy1hcGktYXV0aG9yaXphdGlvbiIsImh0dHBzOi8vdWJpdHMtYXV0aC51cy5hdXRoMC5jb20vdXNlcmluZm8iXSwiaWF0IjoxNzc5NzQzNzczLCJleHAiOjE3Nzk3NTA5NzMsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJhenAiOiI1TkhqdG90dHl1OE5aRFFkYXRMdmtjRW5nd296VU9nNCIsInBlcm1pc3Npb25zIjpbXX0.FSlxH2GuuBezvCyNH6JjdTcV-x4-pEQB_zSGRUlrNY4sqgfL5HqOK7lsJMmxjznsgCCaRa2KCF3IVdqXU5c_4vqLS7CrgaTOltfGfLVCQLYtQdDuQkjPRT8jgLhG4wiTd-BciZIBu1soZVPtVhactWd09xy5v6SgyVL31WqpAZU3hX5f8H7V3dwyZ7oPkybqXcS3rIJ3QkcbcDciu5g_ePUApR-ZAvmGjRYI9kfKQHB4nQJFhA_o7iVrrsEo-zdF8m_sssOR5vze67pqMsilbnc94UaAfW9_nkf3GtvOahdC8udfynENyQTwUP8_G29MxwxJga-Q26jJgyd6lMELng"
axs_id = 6615
file_url = "https://public-resources.ubitslearning.com/core-ai/conversation-files/540f5e1d-b509-4fe0-b665-5c9dad838032/a910eeb1-0905-4924-8eb5-60c5cebdc6c2_a436f911-5e38-46e5-8de5-586c03fdde86_53ccf7aa-f842-48a1-ab46-e20584f6452c_massive-assignations_1__1_.csv"
invalid_file_url = "https://public-resources.ubitslearning.com/core-ai/conversation-files/540f5e1d-b509-4fe0-b665-5c9dad838032/ef64beb8-7ee6-47f1-abc6-05841f7c7fb4_excel_con_nombres_y_edades_aleatorias.txt"
if __name__ == "__main__":
    resultado = tool(
        {"file_url": file_url, "assessment_id": axs_id},
        metadata={"token": token},
    )
    print(resultado)
