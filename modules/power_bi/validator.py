# VALIDADOR DE MEDIDAS DAX: VALIDACIÓN ESTÁTICA CONTRA SCHEMA + ANÁLISIS IA
# DEVUELVE UN DICT ESTRUCTURADO CON ERRORES, ADVERTENCIAS, PUNTUACIÓN Y ESTADO

import re
import json
from core.llm import call_llm
from config.settings import DAX_FUNCTIONS


def validate_dax(dax_code: str, schema: dict) -> dict:
    """
    VALIDA UNA MEDIDA DAX EN DOS FASES:
    1. VALIDACIÓN ESTÁTICA: comprueba que las tablas y columnas existen en el schema
    2. VALIDACIÓN IA: analiza lógica, sintaxis y calidad

    Args:
        dax_code: Código DAX a validar
        schema:   Schema del modelo (tablas + columnas)

    Returns:
        dict con errores_criticos, advertencias, sugerencias, estado, puntuacion, resumen
    """
    # ── FASE 1: VALIDACIÓN ESTÁTICA ───────────────────────────────────────────
    tablas_schema   = {t["name"].lower() for t in schema.get("tables", [])}
    columnas_schema = set()
    for t in schema.get("tables", []):
        for c in t.get("columns", []):
            columnas_schema.add(f"{t['name'].lower()}.{c['name'].lower()}")
            columnas_schema.add(c["name"].lower())

    patron_col  = re.findall(r"'([^']+)'\[([^\]]+)\]", dax_code)
    patron_col += [
        (tabla, col)
        for tabla, col in re.findall(r"(\w+)\[([^\]]+)\]", dax_code)
        if tabla.lower() not in DAX_FUNCTIONS
    ]

    errores_estaticos = []
    for tabla, columna in patron_col:
        clave = f"{tabla.lower()}.{columna.lower()}"
        if tabla.lower() not in tablas_schema and clave not in columnas_schema:
            errores_estaticos.append(f"Tabla no encontrada en el schema: **'{tabla}'**")
        elif clave not in columnas_schema and columna.lower() not in columnas_schema:
            errores_estaticos.append(f"Columna **'{columna}'** no encontrada en la tabla **'{tabla}'**")

    # ── FASE 2: VALIDACIÓN IA ─────────────────────────────────────────────────
    tablas_ref = {t.lower() for t, _ in patron_col}
    schema_red = {
        "tables": [t for t in schema.get("tables", []) if t["name"].lower() in tablas_ref]
    }
    schema_ia = schema_red if schema_red["tables"] else schema

    system_msg = (
        "Eres un experto senior en DAX y Power BI especializado en revisión de código.\n\n"
        "SCHEMA DEL MODELO:\n"
        f"{json.dumps(schema_ia)}\n\n"
        "DEBES ANALIZAR Y REPORTAR errores críticos, advertencias de lógica y sugerencias de mejora.\n"
        "FORMATO — devuelve ÚNICAMENTE este JSON sin markdown:\n"
        "{\n"
        '  "errores_criticos": [...],\n'
        '  "advertencias": [...],\n'
        '  "sugerencias": [...],\n'
        '  "estado": "VALIDA" | "VALIDA CON ADVERTENCIAS" | "INVALIDA",\n'
        '  "puntuacion": 8,\n'
        '  "resumen": "frase corta"\n'
        "}"
    )
    raw = call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": f"MEDIDA DAX A VALIDAR:\n\n{dax_code}"},
        ],
        temperature=0.1, max_tokens=1500,
    )
    raw = re.sub(r"```(?:json)?\n?", "", raw.strip()).strip().rstrip("```").strip()

    try:
        ia_result = json.loads(raw)
    except Exception:
        ia_result = {
            "errores_criticos": ["No se pudo parsear la respuesta de la IA."],
            "advertencias": [], "sugerencias": [],
            "estado": "INVALIDA", "puntuacion": 0,
            "resumen": "Error al procesar la validación.",
        }

    return {
        "errores_criticos":        errores_estaticos + ia_result.get("errores_criticos", []),
        "advertencias":            ia_result.get("advertencias", []),
        "sugerencias":             ia_result.get("sugerencias", []),
        "estado":                  ia_result.get("estado", "INVALIDA"),
        "puntuacion":              ia_result.get("puntuacion", 0),
        "resumen":                 ia_result.get("resumen", ""),
        "codigo":                  dax_code.strip(),
        "tiene_errores_estaticos": len(errores_estaticos) > 0,
    }
