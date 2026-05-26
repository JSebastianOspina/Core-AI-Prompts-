# massive_assign_csv

Esta tool permite enviar un archivo CSV con los usuarios que pretenden ser evaluados de forma masiva en una evaluación 360, asignándolos a las evaluaciones activas correspondientes al assessment indicado. El archivo se referencia por URL pública; la tool lo descarga y procesa la asignación.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para la asignación masiva. Debe contener estrictamente las siguientes llaves:
* **assessment_id (int)**: ID del Assessment / Evaluación 360 (axs-definition). Obtener del chat; si falta, preguntar: ID de la evaluación 360.
* **file_url (str)**: URL pública del archivo CSV con los usernames a asignar (según docstring del modelo). Obtener del chat; si falta, preguntar: URL pública del CSV.

## payload (ejemplo)

```json
{
  "assessment_id": "<int>",
  "file_url": "<url_https>"
}
```
