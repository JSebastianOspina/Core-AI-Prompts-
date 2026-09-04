Crea grupos de tareas en Task Manager.

## Parámetros

- `allocation_type`: modalidad de creación. Usa `oneForAll` para un único plan compartido o `onePerUser` para un plan independiente por cada usuario. Determina el endpoint y no se envía en el body.
- `payload`: datos del plan:
  - `name` (`str`): nombre.
  - `description` (`str | None`): descripción; admite HTML básico.
  - `endDate` (`str | None`): fecha límite en formato ISO 8601.
  - `type` (`str`): `unordered` para tareas independientes u `ordered` para secuenciales. Si falta o es inválido, la tool usa `unordered`.
  - `assignedUsers` (`list[int]`): IDs numéricos de los participantes.
  - `tasks` (`list[dict]`): tareas en el mismo orden en que deben mostrarse. Cada tarea admite `title`, `description`, `endDate` y, opcionalmente, `assigneeId`.

No envíes `label`, `priority` ni `assigneeRole`: la tool fija `label` en `ai-made`, asigna `priority: 20` a cada tarea y añade `assigneeRole: collaborator` cuando existe `assigneeId`.

Devuelve un JSON serializado con `ok`, `status_code` y `data`; ante errores de ejecución devuelve `ok: false` y `error`.