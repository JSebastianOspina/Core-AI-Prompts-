Esta tool permite verificar si la empresa del usuario tiene créditos suficientes para usar un agente, comparando el saldo actual con el precio del agente indicado.

**Parámetros**

* **payload (dict)**: Diccionario de entrada para evaluar si el agente puede usarse. Debe contener estrictamente las siguientes llaves:

* **agent_code (str)**: Código único del agente cuyo precio se comparará con el saldo de créditos de la empresa. Obtener del system prompt del agente; si falta, preguntar: código del agente.

## payload (ejemplo)

```json
{
  "agent_code": "<str>"
}
```
