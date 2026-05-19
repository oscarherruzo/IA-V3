# GENERACIÓN DE MEDIDAS DAX: DESDE DESCRIPCIÓN EN LENGUAJE NATURAL
# INCLUYE DAX RECOMENDADOS AUTOMÁTICOS BASADOS EN EL MODELO SEMÁNTICO
# ENFOQUE: MODELADO DIMENSIONAL Y ARQUITECTURA DE BI

import json
from core.llm import call_llm


def generate_dax(schema: dict, query: str) -> str:
    """GENERA UNA O VARIAS MEDIDAS DAX BASADAS EN EL MODELO SEMÁNTICO DE ORIGEN"""
    
    system_msg = (
        "Actúas como un Arquitecto de Datos y Consultor Senior de Power BI.\n"
        f"Analiza con rigor el MODELO SEMÁNTICO DE ORIGEN suministrado en este SCHEMA: {json.dumps(schema)}.\n\n"
        
        "REGLAS DE DISEÑO DAX (MEJORES PRÁCTICAS OBLIGATORIAS):\n"
        "1. Identifica el rol de las tablas (Hechos vs. Dimensiones) y respeta la propagación de filtros.\n"
        "2. ¡PROHIBICIÓN ESTRICTA!: Nunca utilices el operador de división tradicional (/). Usa OBLIGATORIAMENTE la función DIVIDE() para manejar divisiones por cero de forma segura.\n"
        "3. Sintaxis de Referencias: Las columnas deben llevar siempre el nombre de la tabla ('Tabla'[Columna]). Las medidas JAMÁS deben llevar el nombre de la tabla, solo corchetes ([Medida]).\n"
        "4. En cálculos complejos o con múltiples pasos, utiliza OBLIGATORIAMENTE variables (VAR ... RETURN) para optimizar el rendimiento y la legibilidad.\n"
        "5. Si usas funciones de Time Intelligence (SAMEPERIODLASTYEAR, YTD), asume la existencia de una tabla de fechas si el esquema muestra campos temporales.\n"
        "6. PROHIBICIÓN ESTRICTA: No utilices ningún tipo de emoji, icono o carácter gráfico especial en toda la respuesta.\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO (Cumplir estrictamente sin excepciones):\n"
        "1. Una breve línea introductoria explicando la lógica analítica de la medida.\n"
        "2. El bloque de código envuelto única y exclusivamente en:\n"
        "```dax\n"
        "-- Nombre de la medida\n"
        "Medida = \n"
        "VAR ...\n"
        "RETURN ...\n"
        "```\n"
        "3. Una línea posterior explicando qué hace la fórmula y cómo interactúa con el modelo semántico.\n"
        "4. Responde siempre en español."
    )
    
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": query},
        ],
        temperature=0.1, max_tokens=2000,
    )


def generate_dax_recomendados(schema: dict) -> str:
    """ANALIZA EL MODELO SEMÁNTICO Y RECOMIENDA MÉTRICAS DE NEGOCIO REALES (KPIs)"""
    
    system_msg = (
        "Actúas como un Director de Analytics e Ingeniero de Datos Senior especializado en Power BI.\n"
        f"Tienes este SCHEMA que representa el repositorio de datos empresarial: {json.dumps(schema)}.\n\n"
        
        "CRITERIOS DE RECOMENDACIÓN SEMÁNTICA:\n"
        "- Examina la topología del modelo. Localiza las tablas de hechos (múltiples registros numéricos, llaves foráneas) y sugiere métricas base obligatorias (SUM, COUNTROWS) e inmediatamente KPIs derivados (Márgenes, Ratios).\n"
        "- Si detectas dimensiones de fechas, propón obligatoriamente KPIs de Time Intelligence (Crecimiento MoM, YoY, YTD) usando CALCULATE.\n"
        "- Si detectas entidades de clientes o productos, sugiere medidas analíticas avanzadas como Rankings (RANKX) o categorizaciones dinámicas.\n"
        "- Omite medidas genéricas que no aporten valor; cada recomendación debe ser un KPI real que un directivo querría ver en un Dashboard.\n\n"
        
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "1. Un párrafo ejecutivo inicial que diagnostique qué tipo de modelo en Estrella/Copo de Nieve has detectado y su potencial analítico.\n"
        "2. Cada medida DAX propuesta mapeada en su propio bloque limpio (usa DIVIDE y VAR...RETURN siempre que sea pertinente):\n"
        "```dax\n"
        "-- Nombre\n"
        "Medida = CALCULATE(...)\n"
        "```\n"
        "3. Tras cada bloque, un breve desglose indicando: Por qué es útil para este negocio y en qué visualización de Power BI destacaría.\n"
        "4. Responde siempre en español."
    )
    
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": "Analiza el esquema semántico del origen de datos y recomienda los mejores KPIs y medidas DAX corporativas."},
        ],
        temperature=0.2, max_tokens=3000,
    )