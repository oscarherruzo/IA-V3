# GENERACIÓN DE FÓRMULAS GOOGLE SHEETS: DESDE DESCRIPCIÓN EN LENGUAJE NATURAL
# INCLUYE FÓRMULAS RECOMENDADAS AUTOMÁTICAS BASADAS EN EL SCHEMA

import json
from core.llm import call_llm


def generate_sheets_formula(schema: dict, query: str) -> str:
    """GENERA UNA O VARIAS FÓRMULAS GOOGLE SHEETS A PARTIR DE UNA DESCRIPCIÓN DEL USUARIO"""
    system_msg = (
        f"Eres un experto en Google Sheets y fórmulas avanzadas. Usa este SCHEMA: {json.dumps(schema)}.\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "1. Escribe una breve explicación en texto plano de lo que vas a hacer.\n"
        "2. Cada fórmula en su propio bloque:\n"
        "```sheets\n=FORMULA_AQUI\n```\n"
        "3. Tras cada bloque, una línea explicando qué hace.\n"
        "4. NUNCA pongas código fuera de un bloque ```sheets```.\n"
        "5. Usa funciones nativas: SUMIF, COUNTIF, VLOOKUP, INDEX/MATCH, ARRAYFORMULA, "
        "QUERY, FILTER, UNIQUE, SORT, IMPORTRANGE, REGEXEXTRACT, etc.\n"
        "6. Responde siempre en español.\n"
        "7. PROHIBICIÓN ESTRICTA: No utilices ningún tipo de emoji, icono o carácter gráfico especial en toda la respuesta.\n\n"
    )
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": query},
        ],
        temperature=0.1, max_tokens=2000,
    )


def generate_campos_recomendados(schema: dict) -> str:
    """ANALIZA EL SCHEMA Y PROPONE LAS 5-7 FÓRMULAS SHEETS MÁS ÚTILES AUTOMÁTICAMENTE"""
    system_msg = (
        f"Eres un experto en Google Sheets. Tienes este SCHEMA del modelo: {json.dumps(schema)}.\n\n"
        "Analiza el schema y propón las 5-7 FÓRMULAS SHEETS MÁS ÚTILES Y RELEVANTES "
        "para este modelo concreto, basándote en los nombres reales de tablas y columnas.\n\n"
        "CRITERIOS para elegir qué recomendar:\n"
        "- Detecta si hay columnas numéricas y sugiere agregaciones (SUMIF, AVERAGEIF)\n"
        "- Detecta si hay relaciones entre hojas y sugiere VLOOKUP/INDEX-MATCH\n"
        "- Detecta si hay fechas y sugiere filtros o agrupaciones temporales\n"
        "- Prioriza fórmulas que aporten valor de negocio real\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "1. Un párrafo breve explicando qué tipo de datos has detectado.\n"
        "2. Cada fórmula recomendada en su propio bloque:\n"
        "```sheets\n=FORMULA_AQUI\n```\n"
        "3. Tras cada bloque, una línea explicando por qué es útil para ESTE schema.\n"
        "4. Responde siempre en español."
    )
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": "Analiza el schema y recomienda las fórmulas Sheets más útiles."},
        ],
        temperature=0.2, max_tokens=3000,
    )
