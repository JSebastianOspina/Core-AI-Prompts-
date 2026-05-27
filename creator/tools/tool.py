import csv
import io
import json
import requests
import base64
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from pydantic import BaseModel


class TypeEnum(str, Enum):
    MULTIPLE_CHOICE_SINGLE_ANSWER = "multiple_choice_single_answer"  # Selección múltiple — una sola respuesta correcta
    MULTIPLE_CHOICE_MULTIPLE_ANSWERS = "multiple_choice_multiple_answers"  # Selección múltiple — varias respuestas correctas
    NUMERICAL_SCALE = "numerical_scale"  # Escala numérica
    OPEN_TEXT = "open_text"  # Texto abierto
    BINARY = "binary"  # Binaria (sí/No, Verdadero/Falso, etc.)
    CLOSED_TEXT = "closed_text"  # Texto cerrado (respuesta corta)
    MATCHING = "matching"  # Emparejamiento
    ESSAY = "essay"  # Ensayo / desarrollo largo

class EvaluationsPayload(BaseModel):
   questionnaire_id: int
   questions: list[int]

class Question(BaseModel):
    type: TypeEnum
    statement: str

from enum import Enum





def tool(payload: GenerateEvaluationsPayload, metadata: dict | None = None) -> str: