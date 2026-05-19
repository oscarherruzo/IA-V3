# GENERACIÓN DE CAMPOS CALCULADOS LOOKER STUDIO: DESDE DESCRIPCIÓN EN LENGUAJE NATURAL
# INCLUYE CAMPOS RECOMENDADOS AUTOMÁTICOS BASADOS EN EL SCHEMA

import json
from core.llm import call_llm


def generate_looker_expression(schema: dict, query: str) -> str:
    """GENERA UN CAMPO CALCULADO PARA LOOKER STUDIO BASADO EN EL MODELO SEMÁNTICO DE ORIGEN"""
    
    system_msg = (
        "Actúas como un Arquitecto de Datos y Consultor Senior de BI especializado en Looker Studio.\n"
        f"Analiza con rigor el MODELO SEMÁNTICO DE ORIGEN suministrado en este SCHEMA: {json.dumps(schema)}.\n\n"
        
        "REGLAS DE DISEÑO DE EXPRESIONES:\n"
        "1. Identifica el rol de los campos involucrados (Dimensiones descriptivas vs. Métricas agregables).\n"
        "2. ¡PROHIBICIÓN ESTRICTA!: Nunca inventes nombres de campos que no existan en el esquema. Usa exactamente los nombres provistos.\n"
        "3. Utiliza obligatoriamente la sintaxis nativa de Looker Studio (Ej: CASE WHEN ... THEN ... ELSE ... END, REGEXP_EXTRACT, COUNT_DISTINCT).\n"
        "4. Si vas a calcular ratios o tasas (ej. CTR, Conversion Rate), asegúrate de agregar los campos correctamente (ej. SUM(x)/SUM(y)) y de sugerir el manejo de divisiones por cero si es necesario.\n"
        "5. PROHIBICIÓN ESTRICTA: No utilices ningún tipo de emoji, icono o carácter gráfico especial en toda la respuesta.\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO (Cumplir estrictamente sin excepciones):\n"
        "1. Una breve línea introductoria explicando la lógica analítica de la expresión.\n"
        "2. El bloque de código envuelto única y exclusivamente en:\n"
        "```looker\n"
        "-- Nombre\n"
        "EXPRESION\n"
        "```\n"
        "3. Una línea posterior explicando qué hace la fórmula y su impacto en visualizaciones de Looker Studio.\n"
        "4. Responde siempre en español."
    )
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": query},
        ],
        temperature=0.1, max_tokens=2000,
    )


def generate_campos_recomendados(schema: dict) -> str:
    """ANALIZA EL MODELO SEMÁNTICO Y RECOMIENDA CAMPOS CALCULADOS DE ALTO VALOR"""
    
    system_msg = (
        "Actúas como un Director de Analytics e Ingeniero de Datos Senior especializado en Looker Studio.\n"
        f"Tienes este SCHEMA que representa las fuentes de datos empresariales: {json.dumps(schema)}.\n\n"
        
        "CRITERIOS DE RECOMENDACIÓN SEMÁNTICA:\n"
        "- Examina los tipos de datos y nombres de columnas para deducir el contexto del negocio (E-commerce, Analítica Web, CRM, etc.).\n"
        "- Localiza métricas base (ingresos, sesiones, cantidades) y sugiere KPIs derivados avanzados que requieran agregación (Ratios, Ticket Promedio, ARPU).\n"
        "- Localiza dimensiones de texto complejas (URLs, UTMs, descripciones) y propón extracciones (REGEXP_EXTRACT) o agrupaciones estratégicas (CASE WHEN).\n"
        "- Localiza fechas y sugiere segmentaciones temporales útiles para controles de filtros en Dashboards.\n"
        "- Omite cálculos triviales; cada recomendación debe aportar valor analítico real para la toma de decisiones.\n\n"
        
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "1. Un párrafo ejecutivo inicial que diagnostique el tipo de fuente de datos detectada y su potencial analítico en Looker Studio.\n"
        "2. Cada campo recomendado mapeado en su propio bloque limpio:\n"
        "```looker\n"
        "-- Nombre\n"
        "EXPRESION\n"
        "```\n"
        "3. Tras cada bloque, un breve desglose indicando: Por qué es útil para este negocio y en qué tipo de gráfico se usaría.\n"
        "4. Responde siempre en español."
    )
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": "Analiza el schema y recomienda los campos calculados más útiles."},
        ],
        temperature=0.2, max_tokens=3000,
    )
