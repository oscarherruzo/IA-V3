# CONFIGURACIÓN GLOBAL DE LA APLICACIÓN: MODELOS, COLORES, LÍMITES Y CONSTANTES

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

# ── MODELOS LLM ───────────────────────────────────────────────────────────────

MODEL_9ROUTER     = "kr/claude-sonnet-4.5"                    # 9ROUTER - Claude Sonnet (disponible en 9Router)
MODEL_GROQ        = "llama-3.3-70b-versatile"                 # GROQ fallback
MODEL_SAMBANOVA   = "Meta-Llama-3.3-70B-Instruct"             # SAMBANOVA fallback
MODEL_GEMINI      = "gemini-2.0-flash"                        # GEMINI fallback

# ── PROVEEDORES Y LÍMITES DE TOKENS ──────────────────────────────────────────

PROVIDERS = {
    "9router": {
        "label":  "9Router",
        "daily":  0,           # SIN LÍMITE DIARIO CONOCIDO
        "color":  "#0F766E",
    },
    "groq": {
        "label":  "Groq",
        "daily":  500_000,
        "color":  "#15803D",
    },
    "sambanova": {
        "label":  "SambaNova",
        "daily":  0,
        "color":  "#7C3AED",
    },
    "gemini": {
        "label":  "Gemini",
        "daily":  1_000_000,
        "color":  "#1D4ED8",
    },
}

# ── PALABRAS CLAVE PARA DETECTAR ERRORES DE CUOTA ────────────────────────────

QUOTA_KEYWORDS = (
    "rate_limit", "rate limit", "rate limit exceeded",
    "quota", "tokens", "429",
    "insufficient", "exceeded", "limit exceeded", "too many",
    "resource_exhausted", "resource exhausted",
)

# ── TAMAÑOS DE LOTE PARA GENERACIÓN POR BATCHES ──────────────────────────────

BATCH_SIZE_DOC     = 5    # TABLAS POR LOTE EN DOCUMENTACIÓN
BATCH_SIZE_MEDIDAS = 5    # TABLAS POR LOTE EN MEDIDAS BASE
DOC_CALL_PAUSE     = 1    # SEGUNDOS ENTRE LLAMADAS EN DOCUMENTACIÓN

# ── COLORES PDF ───────────────────────────────────────────────────────────────

W, H = A4
PDF_DARK   = colors.HexColor("#1A1D23")
PDF_GRAY   = colors.HexColor("#6B7280")
PDF_LIGHT  = colors.HexColor("#F7F8FA")
PDF_BORDER = colors.HexColor("#E5E7EB")
PDF_GREEN  = colors.HexColor("#15803D")
PDF_TEAL   = colors.HexColor("#0F766E")
PDF_ACCENT = colors.HexColor("#374151")

# ── FUNCIONES DAX CONOCIDAS (PARA VALIDACIÓN ESTÁTICA) ───────────────────────

DAX_FUNCTIONS = {
    "calculate", "calculatetable", "filter", "all", "allexcept", "allselected",
    "values", "distinct", "summarize", "summarizecolumns", "addcolumns",
    "selectcolumns", "topn", "rankx", "if", "switch", "divide", "blank",
    "isblank", "isinscope", "related", "relatedtable", "userelationship",
    "crossfilter", "treatas", "var", "return", "sum", "sumx", "average",
    "averagex", "count", "countrows", "countx", "countblank", "counta",
    "min", "max", "minx", "maxx", "earlier", "earliest", "hasonevalue",
    "hasonefilter", "selectedvalue", "firstdate", "lastdate", "dateadd",
    "datesytd", "datesmtd", "datesqtd", "sameperiodlastyear", "totalytd",
    "totalmtd", "datesbetween", "datesinperiod", "parallelperiod",
    "generate", "generateseries", "row", "datatable", "naturalinnerjoin",
    "naturalleftouterjoin", "except", "intersect", "union", "groupby",
    "rollup", "rollupaddissubtotal", "isonorafter", "substitutewithindex",
}