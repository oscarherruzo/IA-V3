# VALIDADOR DE FÓRMULAS GOOGLE SHEETS: VALIDACIÓN ESTÁTICA CONTRA SCHEMA + ANÁLISIS IA
# DEVUELVE UN DICT ESTRUCTURADO CON ERRORES, ADVERTENCIAS, PUNTUACIÓN Y ESTADO

import re
import json
from core.llm import call_llm


# FUNCIONES SHEETS NATIVAS (NO TRATAR COMO REFERENCIAS DE COLUMNA)
SHEETS_FUNCTIONS = {
    "sum", "average", "count", "counta", "countif", "countifs", "sumif", "sumifs",
    "averageif", "averageifs", "if", "ifs", "iferror", "ifna", "and", "or", "not",
    "vlookup", "hlookup", "index", "match", "xlookup", "filter", "unique", "sort",
    "sortby", "query", "importrange", "arrayformula", "mmult", "transpose",
    "regexextract", "regexmatch", "regexreplace", "split", "join", "concatenate",
    "concat", "textjoin", "left", "right", "mid", "len", "trim", "lower", "upper",
    "proper", "substitute", "replace", "find", "search", "text", "value", "datevalue",
    "today", "now", "date", "year", "month", "day", "hour", "minute", "second",
    "eomonth", "edate", "networkdays", "workday", "weekday", "weeknum", "datedif",
    "round", "roundup", "rounddown", "floor", "ceiling", "abs", "mod", "int",
    "max", "min", "large", "small", "rank", "percentile", "percentrank",
    "isblank", "isnumber", "istext", "islogical", "iserror", "isna", "isref",
    "indirect", "offset", "row", "rows", "column", "columns", "address",
    "char", "code", "exact", "rept", "flatten", "tocol", "torow", "chooserows",
    "choosecols", "hstack", "vstack", "wraprows", "wrapcols",
}


def validate_sheets_formula(formula: str, schema: dict) -> dict:
    """
    VALIDA UNA FÓRMULA GOOGLE SHEETS EN DOS FASES:
    1. VALIDACIÓN ESTÁTICA: detecta referencias a columnas que no existen en el schema
    2. VALIDACIÓN IA: analiza lógica, sintaxis y calidad

    Args:
        formula: Fórmula Sheets a validar (con o sin = inicial)
        schema:  Schema del modelo (tablas + columnas)

    Returns:
        dict con errores_criticos, advertencias, sugerencias, estado, puntuacion, resumen
    """
    # ── FASE 1: VALIDACIÓN ESTÁTICA ───────────────────────────────────────────
    columnas_schema = set()
    for t in schema.get("tables", []):
        for c in t.get("columns", []):
            columnas_schema.add(c["name"].lower())

    # BUSCAR REFERENCIAS ENTRE COMILLAS (ej: "Columna Ventas") O IDENTIFICADORES
    referencias_texto = re.findall(r'"([^"]+)"', formula)
    referencias_id    = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]+)\b', formula)

    errores_estaticos = []
    for ref in referencias_texto:
        if ref.lower() not in columnas_schema and len(ref) > 2:
            errores_estaticos.append(
                f"Columna posiblemente no encontrada en el schema: **\"{ref}\"**"
            )

    for ref in referencias_id:
        ref_lower = ref.lower()
        if (
            ref_lower not in SHEETS_FUNCTIONS
            and ref_lower not in columnas_schema
            and len(ref_lower) > 3
            and not ref_lower.startswith(("true", "false", "null"))
        ):
            errores_estaticos.append(
                f"Identificador posiblemente no encontrado en el schema: **'{ref}'**"
            )

    # ── FASE 2: VALIDACIÓN IA ─────────────────────────────────────────────────
    system_msg = (
        "Eres un experto senior en Google Sheets especializado en revisión de fórmulas.\n\n"
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
            {"role": "user",   "content": f"FÓRMULA SHEETS A VALIDAR:\n\n{formula}"},
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
        "codigo":                  formula.strip(),
        "tiene_errores_estaticos": len(errores_estaticos) > 0,
    }
