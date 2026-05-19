# GENERACIÓN DE FÓRMULAS EXCEL: DESDE DESCRIPCIÓN EN LENGUAJE NATURAL
# SOPORTA EXCEL CLÁSICO Y EXCEL 365 (FÓRMULAS DINÁMICAS)
# ENFOQUE: MODELADO SEMÁNTICO Y ARQUITECTURA DE DATOS

import json
from core.llm import call_llm


def generate_excel_formula(schema: dict, query: str) -> str:
    """GENERA UNA O VARIAS FÓRMULAS EXCEL BASADAS EN EL MODELO SEMÁNTICO DE ORIGEN"""
    
    system_msg = (
        "Actúas como un Arquitecto de Datos y Consultor Senior de BI experto en Microsoft Excel.\n"
        f"Analiza con rigor el MODELO SEMÁNTICO DE ORIGEN suministrado en este SCHEMA: {json.dumps(schema)}.\n\n"
        
        "REGLAS DE DISEÑO DE FÓRMULAS:\n"
        "1. Identifica el rol de las tablas involucradas (Hechos/Transaccionales vs. Dimensiones/Maestros).\n"
        "2. ¡PROHIBICIÓN ESTRICTA!: Nunca generes un VLOOKUP (BUSCARV) si la columna de retorno está a la izquierda de la columna de búsqueda. Ante búsquedas inversas o complejas, utiliza obligatoriamente XLOOKUP (BUSCARX) o INDEX/MATCH (ÍNDICE/COINCIDIR).\n"
        "3. Prioriza el uso de referencias estructuradas de tablas de Excel si el contexto lo sugiere (Ej: TablaVentas[Importe]).\n"
        "4. En lógicas condicionales complejas, prioriza IFS (SI.CONJUNTO) o SWITCH en lugar de anidar múltiples IF (SI).\n"
        "5. PROHIBICIÓN ESTRICTA: No utilices ningún tipo de emoji, icono o carácter gráfico especial en toda la respuesta.\n\n"
        "FORMATO DE RESPUESTA OBLIGATORIO (Cumplir estrictamente sin excepciones):\n"
        "1. Una breve línea introductoria explicando la lógica analítica de la fórmula.\n"
        "2. El bloque de código envuelto única y exclusivamente en:\n"
        "```excel\n"
        "=FORMULA_AQUI\n"
        "```\n"
        "3. Una línea posterior explicando qué hace la fórmula y su nivel de compatibilidad (Aclara si requiere Excel 365 o si funciona en versiones Clásicas).\n"
        "4. Responde siempre en español."
    )
    
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": query},
        ],
        temperature=0.1, max_tokens=2000,
    )


def generate_formulas_recomendadas(schema: dict) -> str:
    """ANALIZA EL MODELO SEMÁNTICO GLOBAL Y RECOMIENDA MÉTRICAS DE NEGOCIO REALES"""
    
    system_msg = (
        "Actúas como un Director de Analytics e Ingeniero de Datos Senior especializado en Excel.\n"
        f"Tienes este SCHEMA que representa el repositorio de datos empresarial: {json.dumps(schema)}.\n\n"
        
        "CRITERIOS DE RECOMENDACIÓN SEMÁNTICA:\n"
        "- Examina la topología del modelo. Localiza las tablas de hechos (múltiples registros numéricos, transacciones) y sugiere KPIs de negocio (SUMIFS, COUNTIFS, AVERAGEIFS).\n"
        "- Localiza tablas de dimensiones (catálogos de clientes, productos, regiones) y propone búsquedas relacionales seguras (XLOOKUP) o agrupaciones dinámicas modernas (UNIQUE, FILTER, SORT).\n"
        "- Detecta campos de fechas y sugiere análisis temporales o lógicas de validación (EOMONTH, YEAR, TEXT).\n"
        "- Omite fórmulas genéricas (como sumar dos celdas sueltas); cada recomendación debe aportar valor analítico real para la toma de decisiones.\n\n"
        
        "FORMATO DE RESPUESTA OBLIGATORIO:\n"
        "1. Un párrafo ejecutivo inicial que diagnostique qué tipo de modelo semántico has detectado (Ej: Ventas, RRHH, Finanzas) y su potencial en Excel.\n"
        "2. Cada fórmula propuesta mapeada en su propio bloque limpio:\n"
        "```excel\n"
        "=FORMULA_AQUI\n"
        "```\n"
        "3. Tras cada bloque, un breve desglose indicando: Por qué es útil para este negocio y su compatibilidad (Excel 365 vs Clásico).\n"
        "4. Responde siempre en español."
    )
    
    return call_llm(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": "Analiza el esquema semántico del origen de datos y recomienda las mejores métricas y fórmulas matriciales corporativas."},
        ],
        temperature=0.2, max_tokens=3000,
    )

# ALIAS DE COMPATIBILIDAD CON EL FRONTEND (Opcional, según cómo lo importes en tu app)
generate_excel_expression = generate_excel_formula