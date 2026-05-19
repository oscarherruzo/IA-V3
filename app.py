# ═══════════════════════════════════════════════════════════════════════════════
# ANALYTIQ AI — PUNTO DE ENTRADA PRINCIPAL
# Multi-Language Analytics AI Suite
# Power BI (DAX) · Looker Studio · Google Sheets · Excel
# + Módulo de Documentación independiente
# + Conversor a JSON
# Powered by: 9Router + Groq / SambaNova / Gemini fallback
# ═══════════════════════════════════════════════════════════════════════════════

import os
import streamlit as st

# ── IMPORTACIONES DE CAPAS INTERNAS ──────────────────────────────────────────
# Capa de estilos globales (CSS dinámico por plataforma)
from styles import load_css

# Capa de core: tokens y utilidades transversales
from core.tokens import init_token_state, render_tokens_panel

# Capa de UI/Componentes: panel lateral de schema y helpers
from ui.components.schema_panel import init_schema_state, render_schema_panel

# Capa de UI/Tabs: cada pestaña de herramienta en su propio módulo
from ui.tabs.tabs_power_bi   import init_powerbi_state, render_tabs_power_bi
from ui.tabs.tabs_looker     import init_looker_state, render_tabs_looker
from ui.tabs.tabs_sheets     import init_sheets_state, render_tabs_sheets
from ui.tabs.tabs_excel      import init_excel_state, render_tabs_excel
from ui.tabs.tabs_docs       import init_docs_state, render_tabs_docs
from ui.tabs.tabs_json       import init_json_state, render_tabs_json

os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

# ── CONFIGURACIÓN DE PÁGINA STREAMLIT ────────────────────────────────────────
st.set_page_config(
    page_title="AnalytiQ AI | Multi-Language Analytics Suite",
    page_icon="◈",
    layout="wide",
)

# ── INICIALIZACIÓN DE PLATAFORMA ACTIVA ───────────────────────────────────────
# Se inicializa ANTES de cargar el CSS porque el CSS es dinámico por plataforma
if "platform" not in st.session_state:
    st.session_state.platform = "power_bi"

# ── INYECCIÓN DE CSS DINÁMICO ─────────────────────────────────────────────────
# El CSS cambia según la plataforma activa para reflejar la identidad visual
st.markdown(load_css(st.session_state.platform), unsafe_allow_html=True)

# ── INICIALIZACIÓN DE SESSION STATE GLOBAL ────────────────────────────────────
# Cada módulo gestiona su propio estado de forma aislada
init_token_state()
init_schema_state()
init_powerbi_state()
init_looker_state()
init_sheets_state()
init_excel_state()
init_docs_state()
init_json_state()

# ── CARGA DE API KEYS DESDE SECRETS O VARIABLES DE ENTORNO ────────────────────
# Sistema de fallback en 3 capas: secrets anidados → secrets planos → env vars

# 9ROUTER (proveedor principal)
st.session_state["router_base_url"] = ""
st.session_state["router_api_key"]  = ""
try:
    st.session_state["router_base_url"] = st.secrets["ai_config"]["BASE_URL"]
    st.session_state["router_api_key"]  = st.secrets["ai_config"]["API_KEY"]
except:
    try:
        st.session_state["router_base_url"] = st.secrets.get("BASE_URL", "")
        st.session_state["router_api_key"]  = st.secrets.get("API_KEY", "")
    except:
        st.session_state["router_base_url"] = os.environ.get("ROUTER_BASE_URL", "")
        st.session_state["router_api_key"]  = os.environ.get("ROUTER_API_KEY", "")

# GROQ (fallback 1)
try:
    st.session_state["groq_api_key"] = st.secrets.get("GROQ_API_KEY", "")
except:
    st.session_state["groq_api_key"] = os.environ.get("GROQ_API_KEY", "")

# SAMBANOVA (fallback 2)
try:
    st.session_state["sambanova_api_key"] = st.secrets.get("SAMBANOVA_API_KEY", "")
except:
    st.session_state["sambanova_api_key"] = os.environ.get("SAMBANOVA_API_KEY", "")

# GEMINI (fallback 3)
try:
    st.session_state["gemini_api_key"] = st.secrets.get("GEMINI_API_KEY", "")
except:
    st.session_state["gemini_api_key"] = os.environ.get("GEMINI_API_KEY", "")

# ── HEADER PRINCIPAL ──────────────────────────────────────────────────────────
# Muestra el nuevo título corporativo global de la suite
st.markdown("""
    <div class="app-header">
        <div class="app-logo">◈</div>
        <div>
            <p class="app-title">AnalytiQ AI Suite</p>
            <p class="app-subtitle">Power BI · Looker Studio · Google Sheets · Excel · Documentación · JSON</p>
        </div>
        <span class="badge">9ROUTER · GDPR-SAFE · METADATA ONLY</span>
    </div>
""", unsafe_allow_html=True)

# ── SELECTOR DE PLATAFORMA (NAVEGACIÓN PRINCIPAL) ─────────────────────────────
# Cada botón cambia la plataforma activa y relanza el CSS con los colores del tema
# Se usa un diseño de 6 columnas para incluir los dos nuevos módulos

col_pb, col_lk, col_gs, col_xl, col_doc, col_json = st.columns(6)

# ── Definición de plataformas y sus iconos de navegación
NAV_PLATFORMS = [
    ("power_bi",  col_pb,   "⬡  Power BI"),
    ("looker",    col_lk,   "⬢  Looker"),
    ("sheets",    col_gs,   "⊞  Sheets"),
    ("excel",     col_xl,   "∑  Excel"),
    ("docs",      col_doc,  "📄  Docs"),
    ("json",      col_json, "{ }  JSON"),
]

for platform_key, col, label in NAV_PLATFORMS:
    with col:
        if st.button(
            label,
            use_container_width=True,
            type="primary" if st.session_state.platform == platform_key else "secondary",
            key=f"btn_platform_{platform_key}",
        ):
            st.session_state.platform = platform_key
            st.rerun()

st.markdown("<hr style='margin:16px 0 24px 0;border-color:#E5E7EB;'>", unsafe_allow_html=True)

# ── LAYOUT PRINCIPAL: IZQUIERDA | CENTRO | TOKENS ────────────────────────────
# Los módulos Docs y JSON no necesitan schema panel (usan layout de 2 columnas)

PLATFORMS_WITH_SCHEMA = {"power_bi", "looker", "sheets", "excel"}
current_platform = st.session_state.platform

if current_platform in PLATFORMS_WITH_SCHEMA:
    # LAYOUT ESTÁNDAR: Panel de Schema | Contenido Central | Panel de Tokens
    col_left, col_center, col_tokens = st.columns([1, 2.2, 0.7], gap="large")

    with col_left:
        # COLUMNA IZQUIERDA: Carga de schema y estado de API
        current_schema = render_schema_panel(current_platform)

    with col_center:
        # COLUMNA CENTRAL: Tabs de funcionalidades según plataforma activa
        if current_platform == "power_bi":
            render_tabs_power_bi(current_schema)
        elif current_platform == "looker":
            render_tabs_looker(current_schema)
        elif current_platform == "sheets":
            render_tabs_sheets(current_schema)
        elif current_platform == "excel":
            render_tabs_excel(current_schema)

    with col_tokens:
        # COLUMNA DERECHA: Panel de tracking de tokens por proveedor
        render_tokens_panel()

else:
    # LAYOUT EXTENDIDO: Contenido Central | Panel de Tokens (sin schema)
    col_center, col_tokens = st.columns([3, 0.7], gap="large")

    with col_center:
        if current_platform == "docs":
            # Módulo de Documentación independiente
            render_tabs_docs()
        elif current_platform == "json":
            # Módulo Conversor a JSON
            render_tabs_json()

    with col_tokens:
        render_tokens_panel()

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(
    '<p class="footer">AnalytiQ AI Suite · Power BI · Looker Studio · Google Sheets · Excel · '
    'Documentación · Conversor JSON · 9Router + Groq / SambaNova / Gemini · GDPR-Safe Metadata Processing</p>',
    unsafe_allow_html=True,
)
