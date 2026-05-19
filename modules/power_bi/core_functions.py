# EXPLICADOR, EVALUADOR, CHAT, MEDIDAS BASE Y DOCUMENTADOR DE POWER BI (DAX)

import re
import json
import time
from core.llm import call_llm
from config.settings import BATCH_SIZE_MEDIDAS, DOC_CALL_PAUSE, BATCH_SIZE_DOC


# ══════════════════════════════════════════════════════════════════════════════
# EXPLICADOR DAX
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

def explain_dax(dax_code: str, schema: dict) -> str:
    """
    EXPLICA UNA MEDIDA DAX EN TONO DIDÁCTICO Y AUDITA SU INTEGRIDAD 
    CONTRA EL MODELO SEMÁNTICO EN ESTRELLA COMPLETO.
    """
    import json

    # Preparar el contexto relacional profundo (pasamos el JSON completo con columnas y relaciones)
    schema_ctx = ""
    if schema:
        schema_ctx = f"CONTEXTO DEL MODELO SEMÁNTICO REAL (Tablas, Columnas y Relaciones):\n{json.dumps(schema, ensure_ascii=False)}\n\n"

    system_msg = (
        "Actúas como un Arquitecto de Business Intelligence Senior y Auditor de Modelos Tabulares.\n"
        "Tu tarea es explicar medidas DAX de forma clara y didáctica, pero validando su coherencia con el modelo.\n\n"
        
        "REGLAS CRÍTICAS DE AUDITORÍA SEMÁNTICA:\n"
        "1. Validación Estricta de Campos: Compara minuciosamente los nombres de las tablas y columnas usadas en la fórmula con el MODELO SEMÁNTICO REAL provisto.\n"
        "2. Detección de Incoherencias: Si detectas que la fórmula intenta cruzar o asociar campos que no tienen relación lógica en el esquema (Ej: mapear 'Vendedor' contra 'ClienteID' o usar columnas inexistentes), debes iniciar tu respuesta OBLIGATORIAMENTE con un bloque destacado llamado '⚠️ ALERTA DE INTEGRIDAD SEMÁNTICA' explicando con rigor técnico el error de diseño.\n"
        "3. Buenas Prácticas DAX: Verifica si la medida usa el operador '/' (prohibido, debe usar DIVIDE) o si mezcla sintaxis al poner nombres de tablas antes de invocar una medida.\n\n"
        "4. PROHIBICIÓN ESTRICTA: No utilices ningún tipo de emoji, icono o carácter gráfico especial en toda la respuesta.\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "1. **⚠️ ALERTA DE INTEGRIDAD SEMÁNTICA** — (Solo si la fórmula contradice o inventa campos del esquema real).\n"
        "2. **Qué hace esta medida** — Resumen en 1-2 frases simples adaptadas al negocio.\n"
        "3. **Explicación línea por línea** — Desglose didáctico analizando variables (VAR), iteradores y el Contexto de Filtro (CALCULATE).\n"
        "4. **Funciones utilizadas** — Lista cada función y una descripción breve de su comportamiento tabular.\n"
        "5. **Sugerencias y Optimización** — Propón mejoras de rendimiento o la corrección exacta del código basándote en las columnas reales del esquema.\n\n"
        + schema_ctx +
        "Usa un tono didáctico, ideal para un analista junior.\n"
        "NUNCA uses bloques de código markdown generales — solo texto estructurado en español."
    )

    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": f"MEDIDA DAX A EXPLICAR:\n\n{dax_code}"},
        ],
        temperature=0.1, max_tokens=2500,
    )

# ══════════════════════════════════════════════════════════════════════════════
# EVALUADOR DAX (LÓGICA DE NEGOCIO)
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_dax(dax_code: str, schema: dict) -> str:
    """EVALÚA LA LÓGICA DE NEGOCIO DE UNA MEDIDA DAX (NO LA SINTAXIS)"""
    system_msg = (
        "Eres un consultor senior de Power BI y modelado de datos. "
        "Tu tarea NO es buscar errores de sintaxis, sino evaluar si la lógica de negocio "
        "de la medida DAX tiene sentido dado el modelo de datos disponible.\n\n"
        f"SCHEMA DEL MODELO (tablas disponibles): {json.dumps(schema)}\n\n"
        "DEBES EVALUAR Y RESPONDER EN ESPAÑOL con esta estructura:\n\n"
        "**Propósito detectado** — qué problema de negocio intenta resolver esta medida.\n\n"
        "**Coherencia con el modelo** — ¿tiene sentido usar estas tablas y columnas?\n\n"
        "**Impacto de las relaciones** — riesgos de doble conteo, filtros cruzados, etc.\n\n"
        "**Alternativas con este modelo** — forma mejor de calcular esto si la hay.\n\n"
        "**Veredicto final** — puntuación de negocio del 1 al 10.\n\n"
        "Usa un tono de consultor experto. NUNCA uses bloques de código markdown."
    )
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": f"MEDIDA DAX A EVALUAR:\n\n{dax_code}"},
        ],
        temperature=0.3, max_tokens=2000,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CHAT CON EL MODELO
# ══════════════════════════════════════════════════════════════════════════════

def chat_con_modelo(pregunta: str, schema: dict, historial: list) -> str:
    """CHAT MULTITURNO CON CONTEXTO DEL SCHEMA DEL MODELO"""
    tabla_names = [t["name"] for t in schema.get("tables", [])]
    system_msg = (
        "Eres un experto en Power BI, DAX y modelado de datos. "
        "El usuario te va a hacer preguntas sobre su modelo de datos y quiere respuestas "
        "claras, directas y en español.\n\n"
        f"MODELO DE DATOS DISPONIBLE:\n{json.dumps(schema)}\n\n"
        f"TABLAS: {', '.join(tabla_names)}\n\n"
        "Si el usuario pide código DAX, incluye bloques ```dax ... ```.\n"
        "Mantén un tono profesional pero conversacional."
    )
    messages = [{"role": "system", "content": system_msg}]
    for turno in historial[-10:]:
        messages.append({"role": "user",      "content": turno["pregunta"]})
        messages.append({"role": "assistant", "content": turno["respuesta"]})
    messages.append({"role": "user", "content": pregunta})
    return call_llm(messages=messages, temperature=0.3, max_tokens=2000)


# ══════════════════════════════════════════════════════════════════════════════
# MEDIDAS BASE (GENERACIÓN POR LOTES)
# ══════════════════════════════════════════════════════════════════════════════

def _generate_medidas_lote(tablas_lote: list, schema_sel: dict, instruccion: str) -> list:
    schema_lote = {"tables": [t for t in schema_sel["tables"] if t["name"] in tablas_lote]}
    partes = [
        "Eres experto en Power BI y DAX.",
        "SCHEMA: " + json.dumps(schema_lote),
        instruccion,
        "Devuelve SOLO lista JSON sin markdown. Claves: tabla, nombre, codigo, descripcion, nivel.",
        "Usa solo columnas del schema. En avanzadas usa VAR...RETURN. Comenta con --.",
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


def generate_medidas_base(
    tablas_seleccionadas: list,
    nivel: str,
    schema: dict,
    progress_callback=None,
) -> list:
    """
    GENERA MEDIDAS DAX BASE Y/O AVANZADAS POR LOTES PARA LAS TABLAS SELECCIONADAS

    Args:
        tablas_seleccionadas: Nombres de tablas a incluir
        nivel:               "Basicas" | "Avanzadas" | "Ambas"
        schema:              Schema completo del modelo
        progress_callback:   fn(idx, total, nombres) para actualizar UI

    Returns:
        list de dicts {tabla, nombre, codigo, descripcion, nivel}
    """
    nombres_sel = {t.lower() for t in tablas_seleccionadas}
    schema_sel  = {"tables": [t for t in schema.get("tables", []) if t["name"].lower() in nombres_sel]}

    if nivel == "Basicas":
        ins = "Genera 2 medidas BASICAS por tabla (SUM,COUNT,DIVIDE,COUNTROWS). nivel=Basica."
    elif nivel == "Avanzadas":
        ins = "Genera 3 medidas AVANZADAS por tabla (VAR...RETURN,SAMEPERIODLASTYEAR,TOTALYTD,RANKX). nivel=Avanzada."
    else:
        ins = "Genera 2 BASICAS (nivel=Basica) y 2 AVANZADAS (nivel=Avanzada) por tabla."

    tablas_nombres = [t["name"] for t in schema_sel["tables"]]
    lotes  = [tablas_nombres[i:i + BATCH_SIZE_MEDIDAS] for i in range(0, len(tablas_nombres), BATCH_SIZE_MEDIDAS)]
    todas  = []

    for idx, lote in enumerate(lotes):
        if progress_callback:
            progress_callback(idx + 1, len(lotes), lote)
        todas.extend(_generate_medidas_lote(lote, schema_sel, ins))
        if idx < len(lotes) - 1:
            time.sleep(1)

    return todas


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENTADOR (ANÁLISIS POR LOTES + RESUMEN)
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


def _analyze_batch(batch: list, all_table_names: list) -> list:
    system_msg = (
        "Eres un experto en modelado de datos, Power BI y DAX. "
        "Analiza las tablas y devuelve ÚNICAMENTE una lista JSON válida, sin markdown.\n\n"
        "Formato por tabla:\n"
        "[{\n"
        '  "nombre": "nombre_tabla",\n'
        '  "descripcion": "propósito claro en 1-2 frases",\n'
        '  "columnas": [{"nombre": "col", "proposito": "qué dato almacena"}],\n'
        '  "relaciones": ["con qué tablas se relaciona y por qué campo"],\n'
        '  "dax_sugeridos": [\n'
        '    {"nombre": "Nombre Medida", "codigo": "Medida =\\n    VAR x = ...\\n    RETURN x", "descripcion": "qué calcula"}\n'
        '  ]\n'
        "}]\n\n"
        "REGLAS PARA EL DAX:\n"
        "- Propón exactamente 2 medidas por tabla.\n"
        "- Usa: CALCULATE, DIVIDE, SUMX, AVERAGEX, RANKX, DATEADD, SAMEPERIODLASTYEAR, "
        "TOTALYTD, FILTER, ALL, ALLEXCEPT, VAR...RETURN.\n"
        "- Comenta el DAX con -- en las líneas clave.\n\n"
        f"Contexto del modelo: {', '.join(all_table_names)}\n"
        "Devuelve SOLO la lista JSON."
    )
    raw = call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": f"TABLAS A ANALIZAR: {json.dumps(batch)}"},
        ],
        temperature=0.1, max_tokens=5000,
    )
    return _parse_json_response(raw.strip())


def _generate_resumen(all_table_names: list) -> str:
    raw = call_llm(
        messages=[
            {"role": "system", "content":
                "Eres un experto en modelado de datos. Escribe SOLO un párrafo de 2-3 frases "
                "describiendo el modelo basándote en los nombres de las tablas. Solo texto, en español."},
            {"role": "user", "content": f"Tablas: {', '.join(all_table_names)}"},
        ],
        temperature=0.1, max_tokens=300,
    )
    return raw.strip()

def _analyze_batch_md(batch, all_names):
    """Analiza tablas y devuelve markdown puro. Sin JSON."""
    contexto = ", ".join(all_names)
    msg = (
        "Eres un experto en Power BI y DAX. "
        "Documenta cada tabla usando EXACTAMENTE los campos y descripciones del schema recibido.\n\n"
        "Formato obligatorio por tabla:\n\n"
        "## NombreTabla\n\n"
        "Descripcion breve del proposito de la tabla.\n\n"
        "**Columnas:**\n"
        "- `NombreColumna` — descripcion exacta del campo segun el schema. "
        "Si el schema incluye una descripcion para ese campo, usala tal cual. "
        "Si no hay descripcion, infiere el proposito a partir del nombre.\n\n"
        "**IMPORTANTE:** Lista TODAS las columnas del schema, una por linea, sin omitir ninguna.\n\n"
        "**Relaciones:**\n"
        "- Con OtraTabla por CampoX\n\n"
        "---\n\n"
        "REGLAS: SOLO markdown. SIN JSON. SIN ejemplos de formulas ni medidas. "
        "Lista cada columna del schema con su descripcion. En espanol."
    )
    system_msg = msg + "\nContexto del modelo completo: " + contexto
    raw = call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": "TABLAS: " + json.dumps(batch)},
        ],
        temperature=0.1, max_tokens=6000,
    )
    return re.sub(r"```json.*?```", "", raw, flags=re.DOTALL).strip()


def generate_doc(schema, progress_callback=None):
    """Genera documentacion completa en markdown."""
    all_tables = schema.get("tables", [])
    all_names  = [t["name"] for t in all_tables]
    batch_size = 3 if len(all_tables) > 15 else 5
    batches    = [all_tables[i:i+batch_size] for i in range(0, len(all_tables), batch_size)]
    md_parts   = []
    for step, batch in enumerate(batches, start=1):
        names = [t["name"] for t in batch]
        if progress_callback:
            progress_callback(step, len(batches)+1, names, "Generando")
        chunk = _analyze_batch_md(batch, all_names)
        if chunk:
            md_parts.append(chunk)
        time.sleep(1)
    separator = "\n\n"
    return {
        "resumen":  "",
        "markdown": separator.join(md_parts),
        "n_tablas": len(all_tables),
        "tablas":   [],
    }
