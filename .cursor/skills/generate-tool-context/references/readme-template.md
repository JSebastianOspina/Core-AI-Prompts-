# Plantilla: descripción + parámetros + ejemplo

Solo **entrada** (`payload`). Sin metadata, errores, respuesta ni validaciones internas.

---

```markdown
# <nombre_corto_tool>

<1–3 oraciones en lenguaje natural: qué hace la tool para el usuario/negocio. Basado en docstring de `tool()` y del modelo payload; sin timeouts, HTTP ni listado de errores.>

**Parámetros**

* **payload (<tipo o dict>)**: <1 frase: qué agrupa y que debe incluir las llaves siguientes>.
* **<campo> (<tipo>)**: <semántica desde docstring/Field del campo>. <Obtener: chat / preguntar:... si aplica, en la misma línea o siguiente frase corta>.
* ...

## payload (ejemplo)

```json
{
  "campo": "<placeholder>"
}
```
```

- Lista con viñetas (no tabla), formato `**nombre (tipo)**:` como en el ejemplo del usuario.
- Una viñeta por cada llave del payload que el agente debe enviar.
- El JSON de ejemplo debe listar **todas** las llaves con placeholders claros.
