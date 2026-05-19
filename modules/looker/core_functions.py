# MÓDULO LOOKER STUDIO: GENERADOR, VALIDADOR, EXPLICADOR, EVALUADOR, CHAT Y DOCUMENTADOR
# EQUIVALENTE AL MÓDULO POWER BI PERO ADAPTADO A LA SINTAXIS Y CONCEPTOS DE LOOKER STUDIO

import re
import json
import time
from core.llm import call_llm
from config.settings import BATCH_SIZE_DOC, DOC_CALL_PAUSE


# ══════════════════════════════════════════════════════════════════════════════
# GENERADOR DE EXPRESIONES LOOKER
# ══════════════════════════════════════════════════════════════════════════════


def _limpiar_resumen(texto):
    import json as _j
    texto = texto.strip()
    if texto.startswith("{") or texto.startswith("["):
        try:
            p = _j.loads(texto)
            if isinstance(p, dict):
                for k in ("resumen","summary","descripcion"):
                    if k in p and isinstance(p[k], str):
                        return p[k].strip()[:600]
        except Exception:
            pass
    texto = re.sub(r"^#{1,4}\s+.+$", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    return re.sub(r"\n{2,}", " ", texto).strip()[:600]

def generate_looker_expression(schema: dict, query: str) -> str:
    """GENERA UN CAMPO CALCULADO PARA LOOKER STUDIO A PARTIR DE UNA DESCRIPCIÓN"""
    system_msg = (
        f"Eres un experto en Looker Studio y campos calculados. SCHEMA disponible: {json.dumps(schema)}.\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "1. Breve explicación de lo que vas a hacer.\n"
        "2. Cada expresión en su propio bloque:\n"
        "```looker\n-- Nombre\nEXPRESION\n```\n"
        "3. Tras cada bloque, una línea explicando qué hace.\n"
        "4. NUNCA pongas código fuera de un bloque ```looker```.\n"
        "5. Usa funciones nativas de Looker Studio: CASE, IF, REGEXP_EXTRACT, COALESCE, etc.\n"
        "6. Responde siempre en español."
    )
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": query},
        ],
        temperature=0.1, max_tokens=2000,
    )


def generate_campos_recomendados(schema: dict) -> str:
    """ANALIZA EL SCHEMA Y PROPONE LOS 5-7 CAMPOS CALCULADOS MÁS ÚTILES"""
    system_msg = (
        f"Eres experto en Looker Studio. SCHEMA disponible: {json.dumps(schema)}.\n\n"
        "Analiza el schema y propón los 5-7 CAMPOS CALCULADOS MÁS ÚTILES para este modelo.\n\n"
        "CRITERIOS:\n"
        "- Detecta métricas (columnas numéricas) y propón KPIs derivados\n"
        "- Detecta dimensiones de texto y propón categorizaciones\n"
        "- Detecta fechas y propón segmentaciones temporales\n"
        "- Prioriza campos que aporten valor analítico real\n\n"
        "FORMATO:\n"
        "1. Párrafo breve describiendo el tipo de datos detectado.\n"
        "2. Cada campo en bloque:\n"
        "```looker\n-- Nombre\nEXPRESION\n```\n"
        "3. Línea explicando por qué es útil para ESTE modelo.\n"
        "4. Responde en español."
    )
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": "Analiza el schema y recomienda los campos calculados más útiles."},
        ],
        temperature=0.2, max_tokens=3000,
    )


# ══════════════════════════════════════════════════════════════════════════════
# VALIDADOR DE EXPRESIONES LOOKER
# ══════════════════════════════════════════════════════════════════════════════

def validate_looker_expression(expr_code: str, schema: dict) -> dict:
    """VALIDA UNA EXPRESIÓN LOOKER STUDIO CONTRA EL SCHEMA Y POR LÓGICA"""
    # ── VALIDACIÓN ESTÁTICA: CAMPOS REFERENCIADOS ─────────────────────────────
    campos_schema = set()
    for t in schema.get("tables", []):
        for c in t.get("columns", []):
            campos_schema.add(c["name"].lower())

    errores_estaticos = []
    referencias = re.findall(r"\b([A-Za-z_][A-Za-z0-9_\s]*)\b(?=\s*[,\)]|\s+[A-Z])", expr_code)
    palabras_reservadas = {
        "case", "when", "then", "else", "end", "if", "and", "or", "not",
        "true", "false", "null", "regexp_extract", "coalesce", "concat",
        "substr", "length", "upper", "lower", "trim", "round", "floor",
        "ceiling", "abs", "log", "sqrt", "power", "min", "max", "sum",
        "avg", "count", "countd",
    }
    for ref in referencias:
        ref_clean = ref.strip().lower()
        if ref_clean and ref_clean not in palabras_reservadas and len(ref_clean) > 2:
            if ref_clean not in campos_schema:
                errores_estaticos.append(
                    f"Campo posiblemente no encontrado en el schema: **'{ref.strip()}'**"
                )

    # ── VALIDACIÓN IA ─────────────────────────────────────────────────────────
    system_msg = (
        "Eres un experto en Looker Studio y campos calculados.\n\n"
        f"SCHEMA DEL MODELO:\n{json.dumps(schema)}\n\n"
        "ANALIZA Y DEVUELVE ÚNICAMENTE este JSON sin markdown:\n"
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
            {"role": "user",   "content": f"EXPRESIÓN A VALIDAR:\n\n{expr_code}"},
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
            "resumen": "Error al procesar.",
        }

    return {
        "errores_criticos": errores_estaticos + ia_result.get("errores_criticos", []),
        "advertencias":     ia_result.get("advertencias", []),
        "sugerencias":      ia_result.get("sugerencias", []),
        "estado":           ia_result.get("estado", "INVALIDA"),
        "puntuacion":       ia_result.get("puntuacion", 0),
        "resumen":          ia_result.get("resumen", ""),
        "codigo":           expr_code.strip(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# EXPLICADOR DE EXPRESIONES LOOKER
# ══════════════════════════════════════════════════════════════════════════════

def explain_looker_expression(schema: dict, expression_code: str) -> str:
    """
    ANALIZA Y EXPLICA UN CAMPO CALCULADO DE LOOKER STUDIO ASOCIADO AL SCHEMA DE ORIGEN.
    """
    system_msg = (
        "Actúas como un Consultor de BI Senior experto en Looker Studio (Google Data Studio).\n"
        f"Tu tarea es explicar el campo calculado basándote ESTRICTAMENTE en este SCHEMA de origen: {json.dumps(schema)}.\n\n"
        
        "REGLAS CRÍTICAS DE AUDITORÍA:\n"
        "1. Validación de Agregación: Si la fórmula calcula un ratio o porcentaje mezclando dimensiones y métricas sin usar agregaciones correctas (ej: usar clics/impresiones en lugar de SUM(clics)/SUM(impresiones)), genera una '⚠️ ALERTA DE MÉTRICA REVENTADA' explicando por qué Looker fallará al pintar los gráficos.\n"
        "2. PROHIBICIÓN ESTRICTA: No utilices ningún tipo de emoji, icono o carácter gráfico especial en toda la respuesta.\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "1. ⚠️ ALERTA DE MÉTRICA REVENTADA (Si aplica).\n"
        "2. Propósito general en los Dashboards.\n"
        "3. Desglose de la sintaxis nativa (CASE, REGEXP, funciones matemáticas).\n"
        "4. Responde siempre en español."
    )
    
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": f"EXPRESIÓN LOOKER A EXPLICAR:\n{expression_code}"},
        ],
        temperature=0.1, max_tokens=3000,
    )


# ══════════════════════════════════════════════════════════════════════════════
# EVALUADOR DE LÓGICA DE NEGOCIO (LOOKER)
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_looker_expression(expr_code: str, schema: dict) -> str:
    """EVALÚA SI LA LÓGICA DE NEGOCIO DE LA EXPRESIÓN TIENE SENTIDO"""
    system_msg = (
        "Eres un analista senior de datos experto en Looker Studio. "
        "Tu tarea NO es buscar errores de sintaxis, sino evaluar si la lógica de la expresión "
        "tiene sentido dado el modelo de datos disponible.\n\n"
        f"SCHEMA DEL MODELO: {json.dumps(schema)}\n\n"
        "EVALÚA Y RESPONDE EN ESPAÑOL:\n\n"
        "**Propósito detectado** — qué análisis intenta hacer esta expresión.\n\n"
        "**Coherencia con el schema** — ¿tiene sentido usar estos campos?\n\n"
        "**Riesgos analíticos** — valores nulos, divisiones por cero, tipos incorrectos.\n\n"
        "**Alternativas** — hay formas más eficientes o precisas de calcular esto.\n\n"
        "**Veredicto final** — puntuación del 1 al 10.\n\n"
        "NUNCA uses bloques de código markdown."
    )
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": f"EXPRESIÓN A EVALUAR:\n\n{expr_code}"},
        ],
        temperature=0.3, max_tokens=2000,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CHAT CON EL MODELO (LOOKER)
# ══════════════════════════════════════════════════════════════════════════════

def chat_con_looker(pregunta: str, schema: dict, historial: list) -> str:
    """CHAT MULTITURNO CON CONTEXTO DEL SCHEMA DE LOOKER STUDIO"""
    campos_nombres = [c["name"] for t in schema.get("tables", []) for c in t.get("columns", [])]
    system_msg = (
        "Eres un experto en Looker Studio, campos calculados y análisis de datos. "
        "Responde preguntas sobre el schema del usuario con claridad, en español.\n\n"
        f"SCHEMA DISPONIBLE:\n{json.dumps(schema)}\n\n"
        f"CAMPOS: {', '.join(campos_nombres[:30])}\n\n"
        "Si el usuario pide código Looker, incluye bloques ```looker ... ```.\n"
        "Mantén tono profesional pero conversacional."
    )
    messages = [{"role": "system", "content": system_msg}]
    for turno in historial[-10:]:
        messages.append({"role": "user",      "content": turno["pregunta"]})
        messages.append({"role": "assistant", "content": turno["respuesta"]})
    messages.append({"role": "user", "content": pregunta})
    return call_llm(messages=messages, temperature=0.3, max_tokens=2000)


# ══════════════════════════════════════════════════════════════════════════════
# GENERADOR DE CAMPOS BASE POR LOTES
# ══════════════════════════════════════════════════════════════════════════════

def _generate_campos_lote(campos_lote: list, schema_sel: dict, instruccion: str) -> list:
    schema_lote = {
        "tables": [
            {"name": t["name"], "columns": [c for c in t.get("columns", []) if c["name"] in campos_lote]}
            for t in schema_sel.get("tables", [])
        ]
    }
    partes = [
        "Eres experto en Looker Studio y campos calculados.",
        "SCHEMA: " + json.dumps(schema_lote),
        instruccion,
        "Devuelve SOLO lista JSON sin markdown. Claves: tabla, nombre, codigo, descripcion, nivel.",
        "Usa solo campos del schema. Usa IF, CASE, REGEXP_EXTRACT, funciones nativas de Looker.",
    ]
    raw = call_llm([{"role": "user", "content": "\n\n".join(partes)}], temperature=0.1, max_tokens=3000)
    raw = raw.strip().replace("```json", "").replace("```", "").strip()
    if "[" in raw:
        raw = raw[raw.index("["):]
    if "]" in raw:
        raw = raw[:raw.rindex("]") + 1]
    try:
        m = json.loads(raw)
        return m if isinstance(m, list) else []
    except Exception:
        return []


def generate_campos_base(
    fuentes_seleccionadas: list,
    nivel: str,
    schema: dict,
    progress_callback=None,
) -> list:
    """
    GENERA CAMPOS CALCULADOS BASE/AVANZADOS POR LOTES PARA LAS FUENTES SELECCIONADAS

    Args:
        fuentes_seleccionadas: Nombres de tablas/fuentes a incluir
        nivel:                "Basicos" | "Avanzados" | "Ambos"
        schema:               Schema del modelo Looker
        progress_callback:    fn(idx, total, nombres) para UI

    Returns:
        list de dicts {tabla, nombre, codigo, descripcion, nivel}
    """
    nombres_sel = {t.lower() for t in fuentes_seleccionadas}
    schema_sel  = {"tables": [t for t in schema.get("tables", []) if t["name"].lower() in nombres_sel]}

    if nivel == "Basicos":
        ins = "Genera 2 campos BASICOS por tabla (IF, CASE, concatenaciones simples). nivel=Basico."
    elif nivel == "Avanzados":
        ins = "Genera 3 campos AVANZADOS por tabla (REGEXP_EXTRACT, nested CASE, cálculos complejos). nivel=Avanzado."
    else:
        ins = "Genera 2 BASICOS (nivel=Basico) y 2 AVANZADOS (nivel=Avanzado) por tabla."

    tablas_nombres = [t["name"] for t in schema_sel["tables"]]
    lotes  = [tablas_nombres[i:i + 5] for i in range(0, len(tablas_nombres), 5)]
    todas  = []

    for idx, lote in enumerate(lotes):
        lote_campos = [
            c["name"]
            for t in schema_sel["tables"]
            if t["name"] in lote
            for c in t.get("columns", [])
        ]
        if progress_callback:
            progress_callback(idx + 1, len(lotes), lote)
        todas.extend(_generate_campos_lote(lote_campos, schema_sel, ins))
        if idx < len(lotes) - 1:
            time.sleep(1)

    return todas


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENTADOR DE LOOKER STUDIO
# ══════════════════════════════════════════════════════════════════════════════

def _parse_json_response(raw: str) -> list:
    raw = re.sub(r"```(?:json)?\n?", "", raw).strip().rstrip("```").strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return parsed.get("tablas", [parsed])
        return []
    except Exception:
        return []


def _analyze_batch_looker(batch: list, all_source_names: list) -> list:
    system_msg = (
        "Eres experto en Looker Studio y análisis de datos. "
        "Analiza las fuentes y devuelve ÚNICAMENTE una lista JSON válida, sin markdown.\n\n"
        "Formato por fuente:\n"
        "[{\n"
        '  "nombre": "nombre_fuente",\n'
        '  "descripcion": "propósito en 1-2 frases",\n'
        '  "columnas": [{"nombre": "campo", "proposito": "qué mide o clasifica"}],\n'
        '  "relaciones": ["con qué otras fuentes se relaciona y cómo"],\n'
        '  "dax_sugeridos": [\n'
        '    {"nombre": "Nombre Campo", "codigo": "IF(condicion, valor_si, valor_no)", "descripcion": "qué calcula"}\n'
        '  ]\n'
        "}]\n\n"
        "REGLAS PARA EXPRESIONES:\n"
        "- Propón exactamente 2 campos calculados por fuente.\n"
        "- Usa: IF, CASE WHEN, REGEXP_EXTRACT, COALESCE, CONCAT, ROUND, AVG, SUM, COUNT.\n"
        "- Comenta la expresión con -- cuando sea posible.\n\n"
        f"Contexto del modelo: {', '.join(all_source_names)}\n"
        "Devuelve SOLO la lista JSON."
    )
    raw = call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": f"FUENTES A ANALIZAR: {json.dumps(batch)}"},
        ],
        temperature=0.1, max_tokens=5000,
    )
    return _parse_json_response(raw.strip())


def _generate_resumen_looker(all_source_names: list) -> str:
    raw = call_llm(
        messages=[
            {"role": "system", "content":
                "Eres experto en Looker Studio. Escribe SOLO un párrafo de 2-3 frases "
                "describiendo el modelo de datos basándote en los nombres de las fuentes. Solo texto, en español."},
            {"role": "user", "content": f"Fuentes: {', '.join(all_source_names)}"},
        ],
        temperature=0.1, max_tokens=300,
    )
    return raw.strip()

def _analyze_batch_lk_md(batch, all_names):
    """Analiza tablas y devuelve markdown puro. Sin JSON."""
    contexto = ", ".join(all_names)
    msg = (
        "Eres un experto en Looker Studio. "
        "Documenta cada tabla en markdown limpio:\n\n"
        "## NombreTabla\n\n"
        "Descripcion breve.\n\n"
        "**Columnas:**\n"
        "- `NombreColumna` - que almacena\n\n"
        "**Relaciones:**\n"
        "- Con OtraTabla por CampoX\n\n"
        "**Ejemplos campos calculados Looker:**\n"
        "```\n"
        "ejemplo\n"
        "```\n\n"
        "---\n\n"
        "REGLAS: SOLO markdown. SIN JSON. "
        "2 ejemplos de campos calculados Looker por tabla. En espanol."
    )
    system_msg = msg + "\nContexto: " + contexto
    raw = call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": "TABLAS: " + json.dumps(batch)},
        ],
        temperature=0.1, max_tokens=6000,
    )
    return re.sub(r"```json.*?```", "", raw, flags=re.DOTALL).strip()


def generate_doc_looker(schema, progress_callback=None):
    """Genera documentacion completa en markdown."""
    all_tables = schema.get("tables", [])
    all_names  = [t["name"] for t in all_tables]
    raw_res = call_llm(
        messages=[
            {"role": "system", "content": (
                "Eres experto en Looker Studio. "
                "Escribe un parrafo de 2-3 frases en texto plano. "
                "SIN JSON. SIN markdown. En espanol."
            )},
            {"role": "user", "content": "Tablas: " + ", ".join(all_names)},
        ],
        temperature=0.1, max_tokens=400,
    )
    resumen = _limpiar_resumen(raw_res)
    time.sleep(1)
    batch_size = 3 if len(all_tables) > 15 else 5
    batches    = [all_tables[i:i+batch_size] for i in range(0, len(all_tables), batch_size)]
    md_parts   = []
    for step, batch in enumerate(batches, start=1):
        names = [t["name"] for t in batch]
        if progress_callback:
            progress_callback(step, len(batches)+1, names, "Generando")
        chunk = _analyze_batch_lk_md(batch, all_names)
        if chunk:
            md_parts.append(chunk)
        time.sleep(1)
    separator = "\n\n"
    return {
        "resumen":  resumen,
        "markdown": separator.join(md_parts),
        "n_tablas": len(all_tables),
        "tablas":   [],
    }
