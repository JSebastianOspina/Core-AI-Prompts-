import json

import requests
from pydantic import BaseModel, Field


BASE_URL = "https://pub-apps.ubitslearning.com/api/questionnaire/v1"

CLOSED_TEXT_ACCURACY = {"exact", "ignore_accents", "wildcard"}

ENDPOINTS = {
    "multiple_choice_single_answer": None,
    "multiple_choice_multiple_answers": None,
    "binary": None,
    "matching": "matching",
    "essay": "essay",
    "closed_text": "closed-text",
}


class OptionItem(BaseModel):
    """Opción de respuesta para multiple_choice_* y binary."""

    statement: str = Field(description="Texto de la opción.")
    is_correct: bool = Field(description="Si la opción es correcta.")


class MatchingItem(BaseModel):
    """Par de emparejamiento para preguntas tipo matching."""

    term: str = Field(description="Término de la columna izquierda.")
    match: str = Field(description="Término de la columna derecha que empareja con `term`.")


class QuestionItem(BaseModel):
    """Pregunta en formato plano producida por el subagente generate_questions.

    Solo se incluyen los campos que apliquen al `type` indicado.

    - type: identificador del tipo de pregunta (uno de los soportados en ENDPOINTS).
    - statement: enunciado de la pregunta.
    - options: opciones (multiple_choice_*, binary).
    - matching_options: pares term/match (matching).
    - correct_statement: respuesta corta correcta (closed_text; obligatorio).
    - accuracy: precisión de closed_text ("exact" | "ignore_accents" | "wildcard"; obligatorio).
    - number_words_needed: mínimo de palabras esperadas (essay).
    """

    type: str
    statement: str
    options: list[OptionItem] | None = None
    matching_options: list[MatchingItem] | None = None
    correct_statement: str | None = None
    accuracy: str | None = None
    number_words_needed: int | None = None


class CreateQuestionsPayload(BaseModel):
    """Payload para crear, una a una, todas las preguntas de un questionnaire.

    - questionnaire_id: ID del questionnaire (path parameter) donde se crearán las preguntas.
    - questions: lista de preguntas en formato plano; cada item se envía al endpoint que
      corresponde a su `type`.
    """

    questionnaire_id: int = Field(
        description="ID del questionnaire usado como path parameter en cada POST."
    )
    questions: list[QuestionItem] = Field(
        description="Preguntas a crear, en el formato plano producido por el subagente."
    )


def _build_jsonapi_body(question: dict) -> dict | None:
    """Construye el body JSON:API para el endpoint correspondiente al `type` de la pregunta.

    Retorna None si faltan campos obligatorios para ese tipo.
    """
    q_type = question["type"]
    statement = question["statement"]

    attributes = {"type": q_type, "statement": statement}
    relationships: dict = {}

    if q_type in ("multiple_choice_single_answer", "multiple_choice_multiple_answers", "binary"):
        options = question.get("options") or []
        if not options:
            return None
        relationships["question_options"] = {
            "data": [
                {"statement": opt["statement"], "is_correct": opt["is_correct"]}
                for opt in options
            ]
        }

    elif q_type == "matching":
        pairs = question.get("matching_options") or []
        if not pairs:
            return None
        relationships["question_matching_options"] = {
            "data": [{"term": p["term"], "match": p["match"]} for p in pairs]
        }

    elif q_type == "closed_text":
        correct = question.get("correct_statement")
        accuracy = question.get("accuracy")
        if not correct or not accuracy or accuracy not in CLOSED_TEXT_ACCURACY:
            return None
        relationships["question_closed_text"] = {
            "data": {"statement": correct, "accuracy": accuracy}
        }

    elif q_type == "essay":
        if question.get("number_words_needed") is None:
            return None
        relationships["question_essay"] = {
            "data": {"number_words_needed": question["number_words_needed"]}
        }

    else:
        return None

    body: dict = {"data": {"type": "question", "attributes": attributes}}
    if relationships:
        body["data"]["relationships"] = relationships
    return body


def tool(payload: CreateQuestionsPayload, metadata: dict | None = None) -> str:
    """Crea, una a una, las preguntas del payload en el questionnaire indicado."""
    if not isinstance(payload, dict):
        payload = payload.model_dump()

    meta = metadata or {}
    token = meta.get("token")

    if not token:
        return json.dumps(
            {"ok": False, "error": "Missing authentication token"},
            ensure_ascii=False,
        )

    questionnaire_id = payload["questionnaire_id"]
    questions = payload["questions"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    results = []
    success_count = 0
    failure_count = 0

    for index in range(len(questions)):
        question = questions[index]
        q_type = question.get("type")

        if q_type not in ENDPOINTS:
            failure_count += 1
            results.append(
                {
                    "index": index,
                    "type": q_type,
                    "ok": False,
                    "error": f"Unsupported question type: {q_type}",
                }
            )
            continue

        suffix = ENDPOINTS[q_type]

        # questionnaire_id es path parameter: solo construye la URL y no va en el body.
        base = f"{BASE_URL}/questionnaires/{questionnaire_id}/questions"
        url = base if suffix is None else f"{base}/{suffix}"

        body_payload = _build_jsonapi_body(question)
        if body_payload is None:
            failure_count += 1
            results.append(
                {
                    "index": index,
                    "type": q_type,
                    "ok": False,
                    "error": f"Missing required fields for type: {q_type}",
                }
            )
            continue

        try:
            response = requests.post(
                url,
                headers=headers,
                json=body_payload,
                timeout=30,
            )

            try:
                response_data = response.json()
            except Exception:
                response_data = response.text

            entry = {
                "index": index,
                "type": q_type,
                "ok": response.ok,
                "status_code": response.status_code,
                "data": response_data,
            }
            if response.ok:
                success_count += 1
            else:
                failure_count += 1
            results.append(entry)

        except Exception as e:
            failure_count += 1
            results.append(
                {
                    "index": index,
                    "type": q_type,
                    "ok": False,
                    "error": str(e),
                }
            )

    return json.dumps(
        {
            "ok": failure_count == 0,
            "total": len(questions),
            "success": success_count,
            "failed": failure_count,
            "results": results,
        },
        ensure_ascii=False,
    )
