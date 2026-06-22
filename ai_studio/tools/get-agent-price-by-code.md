Esta tool permite consultar el precio de un agente a partir de su código identificador.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para consultar el precio del agente. Debe contener estrictamente las siguientes llaves:

* **agent_code (str)**: Código único del agente (por ejemplo, `EXT_EVALUATION_GENERATOR`). Obtener del system prompt del agente; si falta, preguntar: código del agente. Este campo es un path parameter y NO debe enviarse en el body.

## payload (ejemplo)

```json
{
  "agent_code": "<str>"
}
```
