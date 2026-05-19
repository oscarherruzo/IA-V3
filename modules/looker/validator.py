# VALIDADOR DE EXPRESIONES LOOKER STUDIO: VALIDACIÓN ESTÁTICA CONTRA SCHEMA + ANÁLISIS IA
# DEVUELVE UN DICT ESTRUCTURADO CON ERRORES, ADVERTENCIAS, PUNTUACIÓN Y ESTADO

import re
import json
from core.llm import call_llm


# PALABRAS RESERVADAS Y FUNCIONES DE LOOKER STUDIO (NO TRATAR COMO CAMPOS)
LOOKER_FUNCTIONS = {
    "case", "when", "then", "else", "end", "if", "and", "or", "not",
    "true", "false", "null", "regexp_extract", "regexp_match", "regexp_replace",
    "coalesce", "concat", "substr", "length", "upper", "lower", "trim",
    "replace", "split_part", "left", "right",
    "round", "floor", "ceiling", "abs", "log", "sqrt", "power",
    "min", "max", "sum", "avg", "count", "countd", "median",
    "date_diff", "date_trunc", "date_add", "todate", "year", "month", "day",
    "hour", "minute", "second", "quarter", "week", "dayofweek",
    "current_date", "current_datetime", "current_timestamp",
    "cast", "safe_cast", "safe_divide", "ifnull", "nullif", "isnull",
    "contains_text", "ends_with", "starts_with",
    "running_sum", "running_avg", "running_count", "running_max", "running_min",
    "rank_dense", "percentile",
}


def validate_looker_expression(expr_code: str, schema: dict) -> dict:
    """
    VALIDA UNA EXPRESIÓN LOOKER STUDIO EN DOS FASES:
    1. VALIDACIÓN ESTÁTICA: comprueba que los campos referenciados existen en el schema
    2. VALIDACIÓN IA: analiza lógica, sintaxis y calidad

    Args:
        expr_code: Expresión Looker Studio a validar
        schema:    Schema del modelo (tablas + columnas)

    Returns:
        dict con errores_criticos, advertencias, sugerencias, estado, puntuacion, resumen
    """
    # ── FASE 1: VALIDACIÓN ESTÁTICA ───────────────────────────────────────────
    campos_schema = set()
    for t in schema.get("tables", []):
        for c in t.get("columns", []):
            campos_schema.add(c["name"].lower())

    # IDENTIFICADORES QUE PODRÍAN SER CAMPOS
    referencias = re.findall(r'\b([A-Za-zÀ-ÿ_][A-Za-z0-9_\s]{2,})\b', expr_code)

    errores_estaticos = []
    for ref in referencias:
        ref_clean = ref.strip().lower()
        if (
            ref_clean
            and ref_clean not in LOOKER_FUNCTIONS
            and ref_clean not in campos_schema
            and len(ref_clean) > 3
            and not ref_clean.isdigit()
        ):
            errores_estaticos.append(
                f"Campo posiblemente no encontrado en el schema: **'{ref.strip()}'**"
            )

    # ── FASE 2: VALIDACIÓN IA ─────────────────────────────────────────────────
    system_msg = (
        "Eres un experto en Looker Studio especializado en revisión de campos calculados.\n\n"
        "SCHEMA DEL MODELO:\n"
        f"{json.dumps(schema)}\n\n"
        "ANALIZA Y REPORTA errores críticos, advertencias de lógica y sugerencias de mejora.\n"
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
            {"role": "user",   "content": f"EXPRESIÓN LOOKER A VALIDAR:\n\n{expr_code}"},
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
        "codigo":                  expr_code.strip(),
        "tiene_errores_estaticos": len(errores_estaticos) > 0,
    }
