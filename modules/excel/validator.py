# VALIDADOR DE FÓRMULAS EXCEL: VALIDACIÓN ESTÁTICA CONTRA SCHEMA + ANÁLISIS IA
# DEVUELVE UN DICT ESTRUCTURADO CON ERRORES, ADVERTENCIAS, PUNTUACIÓN Y ESTADO

import re
import json
from core.llm import call_llm


# FUNCIONES EXCEL NATIVAS (NO TRATAR COMO REFERENCIAS DE COLUMNA)
EXCEL_FUNCTIONS = {
    "sum", "average", "count", "counta", "countblank", "countif", "countifs",
    "sumif", "sumifs", "averageif", "averageifs", "sumproduct", "aggregate",
    "if", "ifs", "iferror", "ifna", "and", "or", "not", "xor", "switch",
    "vlookup", "hlookup", "index", "match", "xlookup", "xmatch",
    "filter", "unique", "sort", "sortby", "sequence", "randarray",
    "offset", "indirect", "address", "row", "rows", "column", "columns",
    "choose", "choosecols", "chooserows", "hstack", "vstack", "torow", "tocol",
    "left", "right", "mid", "len", "trim", "lower", "upper", "proper",
    "substitute", "replace", "find", "search", "text", "value", "concat",
    "concatenate", "textjoin", "textbefore", "textafter", "textsplit",
    "today", "now", "date", "datevalue", "year", "month", "day",
    "hour", "minute", "second", "eomonth", "edate", "networkdays",
    "workday", "weekday", "weeknum", "datedif",
    "round", "roundup", "rounddown", "floor", "ceiling", "abs", "mod",
    "int", "trunc", "power", "sqrt", "log", "log10", "exp", "fact",
    "max", "min", "large", "small", "rank", "percentile", "percentrank",
    "stdev", "var", "median", "mode", "quartile", "correl", "forecast",
    "isblank", "isnumber", "istext", "islogical", "iserror", "isna",
    "isref", "iseven", "isodd", "cell", "info", "n", "na", "type",
    "true", "false", "pi", "phi", "rnd",
}


def validate_excel_formula(formula: str, schema: dict) -> dict:
    """
    VALIDA UNA FÓRMULA EXCEL EN DOS FASES:
    1. VALIDACIÓN ESTÁTICA: detecta referencias a columnas que no existen en el schema
    2. VALIDACIÓN IA: analiza lógica, sintaxis, calidad y compatibilidad 365/Clásico

    Args:
        formula: Fórmula Excel a validar (con o sin = inicial)
        schema:  Schema del modelo (tablas + columnas)

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

    # REFERENCIAS CON CORCHETES ESTILO TABLA EXCEL: Tabla[Columna]
    patron_tabla_col = re.findall(r'(\w+)\[([^\]]+)\]', formula)
    # REFERENCIAS ENTRE COMILLAS EN FUNCIONES COMO VLOOKUP
    referencias_texto = re.findall(r'"([A-Za-zÀ-ÿ_][^"]{2,})"', formula)

    errores_estaticos = []
    for tabla, columna in patron_tabla_col:
        tabla_l  = tabla.lower()
        col_l    = columna.lower()
        clave    = f"{tabla_l}.{col_l}"
        if tabla_l not in tablas_schema and clave not in columnas_schema:
            errores_estaticos.append(f"Tabla no encontrada en el schema: **'{tabla}'**")
        elif clave not in columnas_schema and col_l not in columnas_schema:
            errores_estaticos.append(
                f"Columna **'{columna}'** no encontrada en la tabla **'{tabla}'**"
            )

    for ref in referencias_texto:
        if ref.lower() not in columnas_schema and ref.lower() not in tablas_schema:
            errores_estaticos.append(
                f"Referencia posiblemente no encontrada en el schema: **\"{ref}\"**"
            )

    # ── FASE 2: VALIDACIÓN IA ─────────────────────────────────────────────────
    system_msg = (
        "Eres un experto senior en Excel especializado en revisión de fórmulas.\n\n"
        "SCHEMA DEL MODELO:\n"
        f"{json.dumps(schema)}\n\n"
        "ANALIZA Y REPORTA errores críticos, advertencias de lógica, sugerencias de mejora "
        "y compatibilidad (Excel 365 vs clásico).\n"
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
            {"role": "user",   "content": f"FÓRMULA EXCEL A VALIDAR:\n\n{formula}"},
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
