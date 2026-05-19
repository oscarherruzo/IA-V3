import re
import time
# FUNCIONES CORE PARA EXCEL
# GENERADOR, VALIDADOR, EXPLICADOR, EVALUADOR, CHAT Y DOCUMENTADOR

import json
from core.llm import call_llm

# ── GENERAR FÓRMULA EXCEL ───────────────────────────────────────────────────


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
    return re.sub(r"\n{2,}", " ", texto).strip()[:600]

def generate_excel_formula(schema: dict, query: str) -> str:
    """GENERA UNA FÓRMULA EXCEL DESDE UNA DESCRIPCIÓN"""
    
    schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
    
    system_msg = (
        f"ERES UN EXPERTO EN EXCEL Y FÓRMULAS AVANZADAS.\n\n"
        f"SCHEMA DISPONIBLE:\n{schema_str}\n\n"
        f"INSTRUCCIONES:\n"
        f"1. ANALIZA LA SOLICITUD DEL USUARIO\n"
        f"2. GENERA UNA FÓRMULA EXCEL ÓPTIMA\n"
        f"3. USA FUNCIONES: SUMIF, COUNTIF, VLOOKUP, INDEX/MATCH, IF, "
        f"XLOOKUP, FILTER, UNIQUE, SORT, AGGREGATE, etc.\n"
        f"4. SOPORTA TANTO EXCEL CLÁSICO COMO EXCEL 365 (con dinámicas)\n\n"
        f"FORMATO DE RESPUESTA:\n"
        f"1. Breve explicación (1 línea)\n"
        f"2. Bloque de fórmula:\n"
        f"```excel\n"
        f"=FORMULA_AQUI\n"
        f"```\n"
        f"3. Qué hace (breve)\n\n"
        f"NO INCLUYAS explicaciones extras, solo lo solicitado."
    )
    
    try:
        result = call_llm(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": query},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        return result if result else "Error: respuesta vacía"
    except Exception as e:
        return f"Error de API: {str(e)}"


# ── VALIDAR FÓRMULA EXCEL ───────────────────────────────────────────────────

def validate_excel_formula(formula: str, schema: dict) -> dict:
    """VALIDA UNA FÓRMULA EXCEL CONTRA EL SCHEMA"""
    
    schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
    columnas = []
    for tabla in schema.get("tables", []):
        for col in tabla.get("columns", []):
            columnas.append(f"{tabla['name']}.{col['name']}")
    
    system_msg = (
        f"ERES UN VALIDADOR DE FÓRMULAS EXCEL.\n\n"
        f"SCHEMA:\n{schema_str}\n\n"
        f"COLUMNAS DISPONIBLES: {', '.join(columnas)}\n\n"
        f"VALIDAR LA FÓRMULA EXCEL Y DEVOLVER SOLO JSON:\n"
        f"{{\n"
        f'  "estado": "VALIDA" | "INVALIDA" | "VALIDA CON ADVERTENCIAS",\n'
        f'  "codigo": "FÓRMULA_ORIGINAL",\n'
        f'  "errores": ["error1", "error2"],\n'
        f'  "advertencias": ["adv1", "adv2"],\n'
        f'  "score_validez": 95,\n'
        f'  "sugerencias": ["sugerencia1"]\n'
        f"}}"
    )
    
    try:
        result = call_llm(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"FÓRMULA:\n{formula}"},
            ],
            temperature=0.1,
            max_tokens=1500,
        )
        
        # INTENTAR PARSEAR JSON
        try:
            import json as json_module
            validation = json_module.loads(result)
        except:
            validation = {
                "estado": "VALIDA CON ADVERTENCIAS",
                "codigo": formula,
                "errores": [],
                "advertencias": ["No se pudo parsear completamente"],
                "score_validez": 70,
                "sugerencias": []
            }
        
        return validation
    except Exception as e:
        return {
            "estado": "ERROR",
            "codigo": formula,
            "errores": [str(e)],
            "advertencias": [],
            "score_validez": 0,
            "sugerencias": []
        }


# ── EXPLICAR FÓRMULA EXCEL ──────────────────────────────────────────────────

def explain_excel_formula(schema: dict, formula_code: str) -> str:
    """
    ANALIZA Y EXPLICA UNA FÓRMULA DE EXCEL COMPARÁNDOLA CON EL SCHEMA REAL
    PARA DETECTAR INCONSISTENCIAS SEMÁNTICAS.
    """
    system_msg = (
        "Actúas como un Auditor de Modelos Semánticos y Consultor de BI Senior experto en Excel.\n"
        f"Tu tarea es explicar fórmulas de Excel basándote ESTRICTAMENTE en este SCHEMA de origen: {json.dumps(schema)}.\n\n"
        
        "REGLAS CRÍTICAS DE AUDITORÍA:\n"
        "1. Validación de Campos: Compara los nombres de las tablas y columnas de la fórmula con el SCHEMA de tu entorno. "
        "Si detectas que la fórmula intenta usar campos incoherentes (Ej: intentar mapear 'Vendedor' contra 'ClienteID' sin que exista una relación real en el esquema), debes abrir una sección obligatoria llamada '⚠️ ALERTA DE INTEGRIDAD SEMÁNTICA' al inicio de tu respuesta explicando detalladamente el error de diseño.\n"
        "2. Estructura del Desglose: Explica la fórmula parte a parte (LET, XLOOKUP, FILTER, etc.), adaptando el lenguaje al contexto real del negocio.\n"
        "3. Propón la Corrección: Si la fórmula analizada tiene redundancias o errores de combinación en base a tu esquema, muestra la versión optimizada en un bloque limpio de código.\n"
        "4. PROHIBICIÓN ESTRICTA: No utilices ningún tipo de emoji, icono o carácter gráfico especial en toda la respuesta.\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "1. ⚠️ ALERTA DE INTEGRIDAD SEMÁNTICA (Solo si aplica un desajuste con el esquema).\n"
        "2. ¿Qué hace globalmente la fórmula?\n"
        "3. Desglose técnico paso a paso.\n"
        "4. Alternativas de optimización basadas en las columnas reales del modelo.\n"
        "5. Responde siempre en español."
    )
    
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": f"FÓRMULA A EXPLICAR:\n{formula_code}"},
        ],
        temperature=0.1, max_tokens=3000,
    )
# ── EVALUAR FÓRMULA EXCEL ───────────────────────────────────────────────────

def evaluate_excel_formula(formula: str, schema: dict) -> str:
    """EVALÚA SI LA LÓGICA DE NEGOCIO DE UNA FÓRMULA EXCEL TIENE SENTIDO"""
    
    schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
    
    system_msg = (
        f"ERES UN EVALUADOR DE FÓRMULAS EXCEL.\n\n"
        f"SCHEMA:\n{schema_str}\n\n"
        f"EVALUAR LA FÓRMULA Y DEVOLVER:\n"
        f"1. ¿Tiene sentido lógico dado el schema?\n"
        f"2. Riesgos (divisiones por 0, referencias circulares, etc)\n"
        f"3. Performance y eficiencia\n"
        f"4. Alternativas más óptimas\n"
        f"5. Score de lógica (0-100)\n"
        f"6. Compatibilidad (Excel 365 vs clásico)\n\n"
        f"USA MARKDOWN."
    )
    
    try:
        result = call_llm(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"FÓRMULA:\n{formula}"},
            ],
            temperature=0.2,
            max_tokens=2000,
        )
        return result if result else "No se pudo generar evaluación"
    except Exception as e:
        return f"Error de API: {str(e)}"


# ── CHAT CON EL MODELO EXCEL ────────────────────────────────────────────────

def chat_con_excel(pregunta: str, schema: dict, historial: list = None) -> str:
    """CHAT LIBRE SOBRE EXCEL Y EL SCHEMA"""
    
    if historial is None:
        historial = []
    
    schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
    
    system_msg = (
        f"ERES UN ASISTENTE EXPERTO EN EXCEL Y ANÁLISIS DE DATOS.\n\n"
        f"SCHEMA:\n{schema_str}\n\n"
        f"EL USUARIO PREGUNTA SOBRE:\n"
        f"- Cómo crear fórmulas para ciertas tareas\n"
        f"- Qué funciones usar\n"
        f"- Si una fórmula tiene sentido\n"
        f"- Cómo optimizar spreadsheets\n"
        f"- Diferencias entre Excel clásico y 365\n"
        f"- Alternativas y mejores prácticas\n\n"
        f"RESPONDE DE FORMA ÚTIL Y CONCISA.\n"
        f"SI NECESITAS MOSTRAR CÓDIGO, USA ```excel\\n=FORMULA\\n```"
    )
    
    messages = [{"role": "system", "content": system_msg}]
    
    # AGREGAR HISTORIAL
    for turno in historial[-5:]:  # ÚLTIMOS 5 TURNOS
        messages.append({"role": "user", "content": turno["pregunta"]})
        messages.append({"role": "assistant", "content": turno["respuesta"]})
    
    # NUEVA PREGUNTA
    messages.append({"role": "user", "content": pregunta})
    
    try:
        result = call_llm(messages=messages, temperature=0.4, max_tokens=2000)
        return result if result else "No se pudo generar respuesta"
    except Exception as e:
        return f"Error de API: {str(e)}"


# ── GENERAR FÓRMULAS RECOMENDADAS ──────────────────────────────────────────

def generate_formulas_recomendadas(schema: dict) -> str:
    """ANALIZA EL SCHEMA Y SUGIERE FÓRMULAS EXCEL ÚTILES"""
    
    schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
    
    system_msg = (
        f"ERES UN EXPERTO EN EXCEL QUE RECOMIENDA FÓRMULAS ÚTILES.\n\n"
        f"SCHEMA:\n{schema_str}\n\n"
        f"ANALIZA EL SCHEMA Y GENERA 5-7 FÓRMULAS EXCEL ÚTILES QUE ALGUIEN QUERRÍA.\n"
        f"INCLUYE TANTO EXCEL CLÁSICO COMO 365 (con dinámicas si aplica).\n\n"
        f"FORMATO:\n"
        f"## Recomendación 1: [Nombre]\n"
        f"```excel\n"
        f"=FORMULA\n"
        f"```\n"
        f"Descripción breve.\n\n"
        f"(repetir para cada recomendación)"
    )
    
    try:
        result = call_llm(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": "Genera fórmulas recomendadas basadas en el schema"},
            ],
            temperature=0.3,
            max_tokens=3000,
        )
        return result if result else "No se pudieron generar recomendaciones"
    except Exception as e:
        return f"Error de API: {str(e)}"


# ── GENERAR FÓRMULAS BASE POR LOTES ────────────────────────────────────────

def generate_formulas_base(
    fuentes: list, nivel: str, schema: dict, progress_callback=None
) -> list:
    """GENERA FÓRMULAS EXCEL BASE PARA FUENTES ESPECÍFICAS"""
    
    schema_str = json.dumps(schema, ensure_ascii=False, indent=2)
    formulas = []
    
    for idx, fuente in enumerate(fuentes):
        if progress_callback:
            progress_callback(idx + 1, len(fuentes), [fuente], "Generando fórmulas")
        
        tabla_data = next((t for t in schema.get("tables", []) if t["name"] == fuente), None)
        if not tabla_data:
            continue
        
        columnas = [c["name"] for c in tabla_data.get("columns", [])]
        
        system_msg = (
            f"GENERA FÓRMULAS EXCEL PARA LA TABLA: {fuente}\n\n"
            f"COLUMNAS: {', '.join(columnas)}\n"
            f"SCHEMA COMPLETO:\n{schema_str}\n\n"
            f"GENERA {3 if nivel == 'Basicos' else 5} FÓRMULAS ÚTILES.\n"
            f"SOPORTA TANTO EXCEL 365 COMO CLÁSICO.\n\n"
            f"FORMATO JSON:\n"
            f"{{\n"
            f'  "nombre": "Nombre Fórmula",\n'
            f'  "tabla": "{fuente}",\n'
            f'  "nivel": "{nivel}",\n'
            f'  "descripcion": "Qué hace",\n'
            f'  "codigo": "=FORMULA"\n'
            f"}}"
        )
        
        try:
            result = call_llm(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Genera {nivel} fórmulas para {fuente}"},
                ],
                temperature=0.2,
                max_tokens=2000,
            )
            
            # PARSEAR JSON
            try:
                import json as json_module
                import re
                match = re.search(r'\[.*?\]', result, re.DOTALL)
                if match:
                    items = json_module.loads(match.group())
                    for item in items:
                        formulas.append(item)
            except:
                pass
        
        except Exception as e:
            pass
    
    return formulas


# ── GENERAR DOCUMENTACIÓN EXCEL ────────────────────────────────────────────

def _analyze_batch_xl_md(batch, all_names):
    """Analiza tablas y devuelve markdown puro. Sin JSON."""
    contexto = ", ".join(all_names)
    msg = (
        "Eres un experto en Microsoft Excel. "
        "Documenta cada tabla en markdown limpio:\n\n"
        "## NombreTabla\n\n"
        "Descripcion breve.\n\n"
        "**Columnas:**\n"
        "- `NombreColumna` - que almacena\n\n"
        "**Relaciones:**\n"
        "- Con OtraTabla por CampoX\n\n"
        "**Ejemplos formulas Excel:**\n"
        "```\n"
        "=SUMIFS(B:B,A:A,criterio)\n"
        "```\n\n"
        "---\n\n"
        "REGLAS: SOLO markdown. SIN JSON. "
        "2 formulas Excel por tabla. En espanol."
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


def generate_doc_excel(schema, progress_callback=None):
    """Genera documentacion completa de Excel en markdown."""
    all_tables = schema.get("tables", [])
    all_names  = [t["name"] for t in all_tables]
    raw_res = call_llm(
        messages=[
            {"role": "system", "content": (
                "Eres experto en Microsoft Excel. "
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
        chunk = _analyze_batch_xl_md(batch, all_names)
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
