# ═══════════════════════════════════════════════════════════════════════════════
# STYLES.PY — SISTEMA DE ESTILOS DINÁMICOS POR PLATAFORMA
# AnalytiQ AI Suite
#
# Arquitectura:
#   1. css_variables  → Variables CSS (:root) que cambian con la plataforma activa
#   2. static_css     → Estilos base reutilizables para toda la aplicación
#
# Uso:
#   from styles import load_css
#   st.markdown(load_css("power_bi"), unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════════════════════════


def load_css(platform: str = "power_bi") -> str:
    """
    GENERA EL CSS COMPLETO DE LA APLICACIÓN.
    Inyecta las variables de color del tema activo y devuelve el CSS estático.

    Args:
        platform: Identificador de la plataforma activa.
                  Valores: "power_bi" | "looker" | "sheets" | "excel" | "docs" | "json"

    Returns:
        str: HTML con bloques <style> listos para inyectar en Streamlit.
    """

    # ── PALETAS DE COLORES POR PLATAFORMA ─────────────────────────────────────
    # Cada plataforma tiene su identidad de color propia que se aplica
    # a botones, bordes, indicadores de estado, barras de progreso y tabs activos.
    themes = {
        "power_bi": {
            "primary": "#002060",   # Azul corporativo Power BI
            "hover":   "#0066CC",   # Azul brillante para hover
            "text":    "#FFFFFF",
            "light":   "#F0F5FF",
            "bg_tint": "#F5F8FF",   # Tinte de fondo sutil al cambiar de módulo
        },
        "looker": {
            "primary": "#EA4D1A",   # Naranja Looker Studio
            "hover":   "#FF6B35",
            "text":    "#FFFFFF",
            "light":   "#FFF5F0",
            "bg_tint": "#FFF8F5",
        },
        "sheets": {
            "primary": "#117A65",   # Verde Google Sheets
            "hover":   "#16A085",
            "text":    "#FFFFFF",
            "light":   "#F0F9F7",
            "bg_tint": "#F4FCF9",
        },
        "excel": {
            "primary": "#0D5C3C",   # Verde oscuro Microsoft Excel
            "hover":   "#107C47",
            "text":    "#FFFFFF",
            "light":   "#E8F5F0",
            "bg_tint": "#F0FAF5",
        },
        "docs": {
            "primary": "#7C3AED",   # Púrpura para módulo de Documentación
            "hover":   "#A855F7",
            "text":    "#FFFFFF",
            "light":   "#F8F5FF",
            "bg_tint": "#FAF7FF",
        },
        "json": {
            "primary": "#B45309",   # Ámbar/JSON para módulo Conversor
            "hover":   "#D97706",
            "text":    "#FFFFFF",
            "light":   "#FFFBEB",
            "bg_tint": "#FFFDF5",
        },
    }

    # Usa power_bi como fallback si el tema no existe
    t = themes.get(platform, themes["power_bi"])

    # ── BLOQUE 1: VARIABLES CSS DINÁMICAS (:root) ─────────────────────────────
    # Estas variables cambian en cada rerun de Streamlit cuando el usuario
    # cambia de plataforma, proporcionando el feedback visual de "cambio de contexto"
    css_variables = f"""
    <style>
    :root {{
        --theme-primary: {t['primary']};
        --theme-hover:   {t['hover']};
        --theme-text:    {t['text']};
        --theme-light:   {t['light']};
        --theme-bg-tint: {t['bg_tint']};
    }}
    </style>
    """

    # ── BLOQUE 2: CSS ESTÁTICO GLOBAL ─────────────────────────────────────────
    static_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    * { box-sizing: border-box; }

    /* ══════════════════════════════════════════════════════════
       BASE — Fondo de aplicación con tinte dinámico por módulo
    ══════════════════════════════════════════════════════════ */

    .stApp {
        background: var(--theme-bg-tint);
        color: #1A1D23;
        font-family: 'DM Sans', sans-serif;
        transition: background 0.4s ease;  /* Transición suave al cambiar de módulo */
    }

    /* ══════════════════════════════════════════════════════════
       HEADER — Barra superior con línea de color dinámica
    ══════════════════════════════════════════════════════════ */

    .app-header {
        background: #FFFFFF;
        border-bottom: 1px solid #E5E7EB;
        border-top: 4px solid var(--theme-primary); /* Línea superior dinámica */
        padding: 18px 36px;
        display: flex;
        align-items: center;
        gap: 14px;
        margin: -1rem -1rem 2rem -1rem;
        transition: border-top-color 0.3s ease;
    }

    .app-logo {
        width: 40px;
        height: 40px;
        background: var(--theme-primary);
        color: var(--theme-text);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        font-weight: 700;
        transition: background 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }

    .app-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1A1D23;
        letter-spacing: -0.02em;
        margin: 0;
    }

    .app-subtitle {
        font-size: 0.73rem;
        color: #6B7280;
        font-weight: 400;
        margin: 2px 0 0 0;
    }

    .badge {
        margin-left: auto;
        background: #F0FDF4;
        color: #15803D;
        border: 1px solid #BBF7D0;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.68rem;
        font-weight: 600;
        font-family: 'DM Mono', monospace;
        letter-spacing: 0.04em;
    }

    /* ══════════════════════════════════════════════════════════
       CARDS — Tarjetas de contenido
    ══════════════════════════════════════════════════════════ */

    .card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .card-privacy {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-left: 3px solid var(--theme-primary);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 16px;
        transition: border-left-color 0.3s ease;
    }

    .card-privacy p {
        font-size: 0.8rem;
        color: #6B7280;
        margin: 0;
        line-height: 1.6;
    }

    .card-title {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: #6B7280;
        margin-bottom: 16px;
    }

    /* ══════════════════════════════════════════════════════════
       MÓDULO POWER BI — Identidad Visual Azul Corporativo
    ══════════════════════════════════════════════════════════ */

    .module-powerbi {
        border-left: 4px solid #002060 !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F5FF 100%) !important;
    }

    .module-powerbi-header {
        background: linear-gradient(90deg, #002060 0%, #0066CC 100%);
        color: white;
        padding: 16px 20px;
        border-radius: 8px 8px 0 0;
        margin: -24px -24px 16px -24px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .module-powerbi-header::before { content: "◆"; font-size: 1.2rem; font-weight: bold; }
    .module-powerbi-header h3 { margin: 0; font-size: 1rem; font-weight: 600; }

    .powerbi-section-title {
        color: #002060;
        border-bottom: 2px solid #0066CC;
        padding-bottom: 8px;
        margin: 16px 0 12px 0;
    }

    .powerbi-badge {
        background: #E8F2FF; color: #002060; border: 1px solid #0066CC;
        border-radius: 4px; padding: 4px 10px; font-size: 0.7rem;
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    }

    .powerbi-code {
        background: #1A1A2E !important;
        border-left: 3px solid #0066CC !important;
        color: #93C5FD !important;
    }

    /* ══════════════════════════════════════════════════════════
       MÓDULO LOOKER — Identidad Visual Naranja
    ══════════════════════════════════════════════════════════ */

    .module-looker {
        border-left: 4px solid #EA4D1A !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #FFF5F0 100%) !important;
    }

    .module-looker-header {
        background: linear-gradient(90deg, #EA4D1A 0%, #FF6B35 100%);
        color: white; padding: 16px 20px;
        border-radius: 8px 8px 0 0;
        margin: -24px -24px 16px -24px;
        display: flex; align-items: center; gap: 12px;
    }

    .module-looker-header::before { content: "⬢"; font-size: 1.2rem; font-weight: bold; }
    .module-looker-header h3 { margin: 0; font-size: 1rem; font-weight: 600; }

    .looker-section-title {
        color: #EA4D1A;
        border-bottom: 2px solid #FF6B35;
        padding-bottom: 8px; margin: 16px 0 12px 0;
    }

    .looker-badge {
        background: #FFF2E6; color: #EA4D1A; border: 1px solid #FF6B35;
        border-radius: 4px; padding: 4px 10px; font-size: 0.7rem;
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    }

    .looker-code {
        background: #1A0F08 !important;
        border-left: 3px solid #FF6B35 !important;
        color: #FFA574 !important;
    }

    /* ══════════════════════════════════════════════════════════
       MÓDULO GOOGLE SHEETS — Identidad Visual Verde
    ══════════════════════════════════════════════════════════ */

    .module-sheets {
        border-left: 4px solid #117A65 !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #F0F9F7 100%) !important;
    }

    .module-sheets-header {
        background: linear-gradient(90deg, #117A65 0%, #16A085 100%);
        color: white; padding: 16px 20px;
        border-radius: 8px 8px 0 0;
        margin: -24px -24px 16px -24px;
        display: flex; align-items: center; gap: 12px;
    }

    .module-sheets-header::before { content: "⊞"; font-size: 1.2rem; font-weight: bold; }
    .module-sheets-header h3 { margin: 0; font-size: 1rem; font-weight: 600; }

    .sheets-section-title {
        color: #117A65; border-bottom: 2px solid #16A085;
        padding-bottom: 8px; margin: 16px 0 12px 0;
    }

    .sheets-badge {
        background: #E8F8F5; color: #117A65; border: 1px solid #16A085;
        border-radius: 4px; padding: 4px 10px; font-size: 0.7rem;
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    }

    .sheets-code {
        background: #0F1916 !important;
        border-left: 3px solid #16A085 !important;
        color: #52D0A3 !important;
    }

    /* ══════════════════════════════════════════════════════════
       MÓDULO EXCEL — Identidad Visual Verde Oscuro
    ══════════════════════════════════════════════════════════ */

    .module-excel {
        border-left: 4px solid #0D5C3C !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #E8F5F0 100%) !important;
    }

    .module-excel-header {
        background: linear-gradient(90deg, #0D5C3C 0%, #107C47 100%);
        color: white; padding: 16px 20px;
        border-radius: 8px 8px 0 0;
        margin: -24px -24px 16px -24px;
        display: flex; align-items: center; gap: 12px;
    }

    .module-excel-header::before { content: "∑"; font-size: 1.4rem; font-weight: bold; }
    .module-excel-header h3 { margin: 0; font-size: 1rem; font-weight: 600; }

    .excel-section-title {
        color: #0D5C3C; border-bottom: 2px solid #107C47;
        padding-bottom: 8px; margin: 16px 0 12px 0;
    }

    .excel-badge {
        background: #DEEAE5; color: #0D5C3C; border: 1px solid #107C47;
        border-radius: 4px; padding: 4px 10px; font-size: 0.7rem;
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    }

    .excel-code {
        background: #0F1612 !important;
        border-left: 3px solid #107C47 !important;
        color: #4FB584 !important;
    }

    /* ══════════════════════════════════════════════════════════
       MÓDULO DOCS — Identidad Visual Púrpura
    ══════════════════════════════════════════════════════════ */

    .module-docs {
        border-left: 4px solid #7C3AED !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #F8F5FF 100%) !important;
    }

    .module-docs-header {
        background: linear-gradient(90deg, #7C3AED 0%, #A855F7 100%);
        color: white; padding: 16px 20px;
        border-radius: 8px 8px 0 0;
        margin: -24px -24px 16px -24px;
        display: flex; align-items: center; gap: 12px;
    }

    .module-docs-header::before { content: "📄"; font-size: 1.1rem; }
    .module-docs-header h3 { margin: 0; font-size: 1rem; font-weight: 600; }

    .docs-section-title {
        color: #7C3AED; border-bottom: 2px solid #A855F7;
        padding-bottom: 8px; margin: 16px 0 12px 0;
    }

    .docs-badge {
        background: #F3E8FF; color: #7C3AED; border: 1px solid #A855F7;
        border-radius: 4px; padding: 4px 10px; font-size: 0.7rem;
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    }

    /* ══════════════════════════════════════════════════════════
       MÓDULO JSON CONVERSOR — Identidad Visual Ámbar
    ══════════════════════════════════════════════════════════ */

    .module-json {
        border-left: 4px solid #B45309 !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #FFFBEB 100%) !important;
    }

    .module-json-header {
        background: linear-gradient(90deg, #B45309 0%, #D97706 100%);
        color: white; padding: 16px 20px;
        border-radius: 8px 8px 0 0;
        margin: -24px -24px 16px -24px;
        display: flex; align-items: center; gap: 12px;
    }

    .module-json-header::before { content: "{ }"; font-size: 1.0rem; font-weight: 800; font-family: 'DM Mono', monospace; }
    .module-json-header h3 { margin: 0; font-size: 1rem; font-weight: 600; }

    .json-section-title {
        color: #B45309; border-bottom: 2px solid #D97706;
        padding-bottom: 8px; margin: 16px 0 12px 0;
    }

    .json-badge {
        background: #FEF3C7; color: #B45309; border: 1px solid #D97706;
        border-radius: 4px; padding: 4px 10px; font-size: 0.7rem;
        font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
    }

    /* ══════════════════════════════════════════════════════════
       DAX — Sub-identidad Visual Púrpura (dentro de Power BI)
    ══════════════════════════════════════════════════════════ */

    .module-dax {
        border-left: 4px solid #7C3AED !important;
        background: linear-gradient(135deg, #FFFFFF 0%, #F8F5FF 100%) !important;
    }

    .module-dax-header {
        background: linear-gradient(90deg, #7C3AED 0%, #A855F7 100%);
        color: white; padding: 16px 20px;
        border-radius: 8px 8px 0 0;
        margin: -24px -24px 16px -24px;
        display: flex; align-items: center; gap: 12px;
    }

    .module-dax-header::before { content: "ƒ"; font-size: 1.4rem; font-weight: bold; }
    .module-dax-header h3 { margin: 0; font-size: 1rem; font-weight: 600; }

    .dax-section-title { color: #7C3AED; border-bottom: 2px solid #A855F7; padding-bottom: 8px; margin: 16px 0 12px 0; }
    .dax-badge { background: #F3E8FF; color: #7C3AED; border: 1px solid #A855F7; border-radius: 4px; padding: 4px 10px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .dax-code { background: #1F0A3C !important; border-left: 3px solid #A855F7 !important; color: #D8B4FE !important; }

    /* ══════════════════════════════════════════════════════════
       STATUS INDICATORS
    ══════════════════════════════════════════════════════════ */

    .status-ok {
        display: inline-flex; align-items: center; gap: 6px;
        background: #F0FDF4; color: #15803D;
        border: 1px solid #BBF7D0; border-radius: 6px;
        padding: 6px 12px; font-size: 0.78rem; font-weight: 500;
        margin-bottom: 12px;
    }

    .status-dot { width: 6px; height: 6px; border-radius: 50%; background: #22C55E; }

    /* ══════════════════════════════════════════════════════════
       TOKENS PANEL — Panel lateral de uso de tokens
    ══════════════════════════════════════════════════════════ */

    .tokens-card {
        background: #FFFFFF; border: 1px solid #E5E7EB;
        border-radius: 14px; padding: 20px 24px; margin-bottom: 16px;
    }

    .tokens-row { display: flex; justify-content: space-between; align-items: center; padding: 4px 0; font-size: 0.8rem; }
    .tokens-label { color: #6B7280; font-family: 'DM Sans', sans-serif; }
    .tokens-value { color: #1A1D23; font-family: 'DM Mono', monospace; font-weight: 500; font-size: 0.8rem; }

    .tokens-bar-wrap { background: #F3F4F6; border-radius: 4px; height: 5px; margin: 8px 0 4px 0; overflow: hidden; }
    .tokens-caption { font-size: 0.7rem; color: #9CA3AF; font-family: 'DM Mono', monospace; text-align: right; margin: 0; }
    .tokens-total-row { display: flex; justify-content: space-between; align-items: center; padding-top: 8px; }
    .tokens-total-label { font-size: 0.8rem; font-weight: 600; color: #1A1D23; }
    .tokens-total-value { font-size: 1rem; font-weight: 700; color: #1A1D23; font-family: 'DM Mono', monospace; }
    .tokens-provider-block { margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid #F3F4F6; }
    .tokens-provider-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
    .tokens-provider-calls { font-size: 0.7rem; color: #6B7280; font-family: 'DM Mono', monospace; }

    /* ══════════════════════════════════════════════════════════
       VALIDATION PANEL
    ══════════════════════════════════════════════════════════ */

    .verdict-card { border: 1px solid #2A2A2A; border-radius: 4px; padding: 20px; margin: 16px 0; background: #1A1A1A; }
    .verdict-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .verdict-resumen { font-size: 0.85rem; color: #9CA3AF; margin: 0; }

    .validation-section-title { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin: 16px 0 8px 0; }
    .validation-section-title.errors   { color: #DC2626; }
    .validation-section-title.warnings { color: #D97706; }
    .validation-section-title.tips     { color: #2563EB; }

    .validation-item { border-radius: 3px; padding: 10px 14px; margin-bottom: 6px; font-size: 0.83rem; }
    .validation-item.error   { background: #1F0A0A; border: 1px solid #5B1A1A; color: #FCA5A5; }
    .validation-item.warning { background: #1F1200; border: 1px solid #5B3A00; color: #FCD34D; }
    .validation-item.tip     { background: #0A0F1F; border: 1px solid #1A2D5B; color: #93C5FD; }
    .validation-ok { background: #0A1F0F; border: 1px solid #1A5B2D; border-radius: 3px; padding: 10px 14px; font-size: 0.83rem; color: #86EFAC; }

    /* ══════════════════════════════════════════════════════════
       EVALUADOR — Info box estilo código oscuro
    ══════════════════════════════════════════════════════════ */

    .eval-info {
        background: #0A0F1F; border: 1px solid #1A2D5B;
        border-radius: 3px; padding: 10px 14px;
        margin-bottom: 16px; font-size: 0.8rem; color: #93C5FD;
    }

    /* ══════════════════════════════════════════════════════════
       CHAT BUBBLES — Historial de conversación
    ══════════════════════════════════════════════════════════ */

    .chat-user-bubble { background: #1A1D23; border: 1px solid #2A2A2A; border-radius: 4px; padding: 12px 16px; margin-bottom: 8px; }
    .chat-user-label { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #6B7280; margin: 0 0 6px 0; }
    .chat-user-text { font-size: 0.9rem; color: #E5E7EB; margin: 0; }

    .chat-ai-bubble { background: #0D1117; border: 1px solid #1A2D5B; border-left: 3px solid #374151; border-radius: 4px; padding: 12px 16px; margin-bottom: 16px; }
    .chat-ai-label { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #6B7280; margin: 0 0 6px 0; }

    /* ══════════════════════════════════════════════════════════
       UTILITIES — Clases de apoyo reutilizables
    ══════════════════════════════════════════════════════════ */

    .nivel-badge { font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.08em; display: inline-block; margin-bottom: 6px; }
    .nivel-badge.basica   { background: #0A1F0F; color: #15803D; }
    .nivel-badge.avanzada { background: #1A0A2E; color: #7C3AED; }

    .section-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: #6B7280; margin: 16px 0 8px 0; }

    .hint-text  { font-size: 0.85rem; color: #6B7280; margin-bottom: 16px; }
    .hint-note  { font-size: 0.75rem; color: #9CA3AF; padding-top: 10px; }
    .hint-ok    { font-size: 0.75rem; color: #15803D; padding-top: 10px; }
    .hint-warn  { font-size: 0.75rem; color: #B45309; padding-top: 10px; }
    .api-note   { font-size: 0.75rem; color: #6B7280; margin-top: 4px; }

    .dax-label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #6B7280; margin: 12px 0 4px 0; }
    .hr-dark { border: none; border-top: 1px solid #2A2A2A; margin: 24px 0; }
    hr { border: none; border-top: 1px solid #E5E7EB; margin: 16px 0; }

    /* ══════════════════════════════════════════════════════════
       STREAMLIT OVERRIDES — Personalización de componentes nativos
    ══════════════════════════════════════════════════════════ */

    /* Botones primarios: toman el color dinámico del tema activo */
    div.stButton > button {{
        background: var(--theme-primary) !important;
        color: var(--theme-text) !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
    }}

    div.stButton > button:hover {{
        background: var(--theme-hover) !important;
        box-shadow: 0 4px 10px -2px rgba(0,0,0,0.18) !important;
        transform: translateY(-1px) !important;
    }}

    /* Botones de descarga: neutral oscuro */
    div.stDownloadButton > button {{
        background: #1A1D23 !important; color: #FFFFFF !important;
        border: none !important; border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important; font-size: 0.85rem !important;
        font-weight: 500 !important; padding: 10px 24px !important;
        width: 100% !important; transition: background 0.2s !important;
    }}

    div.stDownloadButton > button:hover {{
        background: #374151 !important; box-shadow: none !important;
    }}

    /* TextArea y TextInput */
    .stTextArea textarea {{
        background: #F9FAFB !important; border: 1px solid #E5E7EB !important;
        border-radius: 8px !important; font-family: 'DM Mono', monospace !important;
        font-size: 0.85rem !important; color: #1A1D23 !important;
    }}

    .stTextInput input {{
        background: #F9FAFB !important; border: 1px solid #E5E7EB !important;
        border-radius: 8px !important; font-family: 'DM Mono', monospace !important;
        font-size: 0.85rem !important; color: #1A1D23 !important;
        padding: 10px 14px !important;
    }}

    /* Focus: usa el color del tema activo */
    .stTextArea textarea:focus,
    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stSelectbox > div > div:focus-within,
    .stMultiSelect > div > div:focus-within {{
        border-color: var(--theme-primary) !important;
        box-shadow: 0 0 0 1px var(--theme-primary) !important;
    }}

    .stNumberInput input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {{
        background: #F9FAFB !important; border: 1px solid #E5E7EB !important;
        border-radius: 8px !important; font-family: 'DM Sans', sans-serif !important;
        font-size: 0.85rem !important; color: #1A1D23 !important;
    }}

    /* Pestañas internas (st.tabs): color dinámico en pestaña activa */
    button[data-baseweb="tab"] p {{
        color: #6B7280 !important;
        transition: color 0.2s ease !important;
    }}

    button[data-baseweb="tab"]:hover p {{
        color: var(--theme-hover) !important;
    }}

    button[data-baseweb="tab"][aria-selected="true"] p {{
        color: var(--theme-primary) !important;
        font-weight: 600 !important;
    }}

    button[data-baseweb="tab"][aria-selected="true"] + div,
    div[data-baseweb="tab-highlight-id"],
    .stTabs [role="tablist"] [aria-selected="true"] {{
        border-color: var(--theme-primary) !important;
        background-color: var(--theme-primary) !important;
    }}

    /* Expanders */
    .streamlit-expanderHeader {{
        background: #F9FAFB !important; border: 1px solid #E5E7EB !important;
        border-radius: 8px !important; font-family: 'DM Sans', sans-serif !important;
        font-size: 0.82rem !important; font-weight: 500 !important;
        color: #374151 !important; padding: 10px 14px !important;
    }}

    .streamlit-expanderHeader:hover {{ color: var(--theme-primary) !important; }}

    .streamlit-expanderContent {{
        border: 1px solid #E5E7EB !important; border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        background: #FFFFFF !important; padding: 12px 14px !important;
    }}

    /* Radios y Progress */
    .stRadio > div {{ gap: 16px !important; }}
    .stRadio label {{ font-family: 'DM Sans', sans-serif !important; font-size: 0.85rem !important; font-weight: 500 !important; color: #374151 !important; }}

    .stProgress > div > div > div {{ background: var(--theme-primary) !important; border-radius: 4px !important; }}
    .stProgress > div > div {{ background: #F3F4F6 !important; border-radius: 4px !important; }}

    /* ══════════════════════════════════════════════════════════
       FOOTER
    ══════════════════════════════════════════════════════════ */

    .footer {
        text-align: center; font-size: 0.72rem; color: #9CA3AF;
        margin-top: 32px; padding-top: 16px;
        border-top: 1px solid #E5E7EB;
        font-family: 'DM Mono', monospace;
    }
    </style>
    """

    return css_variables + static_css
