# PANEL DE TOKENS: TRACKING Y RENDER DE USO POR PROVEEDOR
# MUESTRA ESTADÍSTICAS EN LA COLUMNA DERECHA DE LA APLICACIÓN

import streamlit as st
from config.settings import PROVIDERS


# ── INICIALIZACIÓN DE SESSION STATE DE TOKENS ─────────────────────────────────

def init_token_state():
    # INICIALIZA LOS CONTADORES DE TOKENS PARA TODOS LOS PROVEEDORES
    for provider in PROVIDERS:
        for metric in ("prompt", "completion", "calls"):
            key = f"tokens_{provider}_{metric}"
            if key not in st.session_state:
                st.session_state[key] = 0


# ── RENDER DEL PANEL DE TOKENS ────────────────────────────────────────────────

def render_tokens_panel():
    # CALCULA EL TOTAL GLOBAL DE TOKENS USADOS EN LA SESIÓN
    total_global = sum(
        st.session_state.get(f"tokens_{p}_prompt", 0) +
        st.session_state.get(f"tokens_{p}_completion", 0)
        for p in PROVIDERS
    )

    html = '<div class="tokens-card">'
    html += '<p class="card-title">Uso de tokens</p>'

    for provider, cfg in PROVIDERS.items():
        prompt     = st.session_state.get(f"tokens_{provider}_prompt", 0)
        completion = st.session_state.get(f"tokens_{provider}_completion", 0)
        calls      = st.session_state.get(f"tokens_{provider}_calls", 0)
        total      = prompt + completion
        daily      = cfg["daily"]
        color      = cfg["color"]
        label      = cfg["label"]

        html += '<div class="tokens-provider-block">'
        html += '<div class="tokens-provider-header">'
        html += (
            f'<span class="tokens-label" style="font-weight:700;color:{color};'
            f'text-transform:uppercase;letter-spacing:0.08em;font-size:0.7rem;">{label}</span>'
        )
        html += f'<span class="tokens-provider-calls">{calls} llamadas</span>'
        html += '</div>'
        html += f'<div class="tokens-row"><span class="tokens-label">Total</span><span class="tokens-value">{total:,}</span></div>'
        html += f'<div class="tokens-row"><span class="tokens-label">&#8593; Prompt</span><span class="tokens-value">{prompt:,}</span></div>'
        html += f'<div class="tokens-row"><span class="tokens-label">&#8595; Completion</span><span class="tokens-value">{completion:,}</span></div>'

        if daily > 0 and total > 0:
            pct = min((total / daily) * 100, 100)
            bar_color = "#DC2626" if pct >= 90 else "#D97706" if pct >= 70 else color
            html += (
                f'<div class="tokens-bar-wrap">'
                f'<div style="height:100%;border-radius:4px;background:{bar_color};width:{pct:.1f}%;"></div>'
                f'</div>'
            )
            html += f'<p class="tokens-caption">{pct:.1f}% de {daily // 1000}k</p>'
        else:
            caption = "sin uso" if calls == 0 else "sin l&#237;mite"
            html += f'<p class="tokens-caption">{caption}</p>'

        html += '</div>'

    html += (
        '<div class="tokens-total-row">'
        '<span class="tokens-total-label">Total sesi&#243;n</span>'
        f'<span class="tokens-total-value">{total_global:,}</span>'
        '</div>'
    )

    # ENLACES A LAS CONSOLAS DE CADA PROVEEDOR
    html += (
        '<div style="margin-top:12px;padding-top:10px;border-top:1px solid #F3F4F6;">'
        '<p class="tokens-caption" style="margin-bottom:6px;">Ver uso real:</p>'
        '<a href="http://localhost:20128" target="_blank" style="display:block;font-size:0.72rem;color:#0F766E;text-decoration:none;margin-bottom:3px;">&#8599; 9Router Console</a>'
        '<a href="https://console.groq.com/usage" target="_blank" style="display:block;font-size:0.72rem;color:#15803D;text-decoration:none;margin-bottom:3px;">&#8599; Groq Console</a>'
        '<a href="https://cloud.sambanova.ai" target="_blank" style="display:block;font-size:0.72rem;color:#7C3AED;text-decoration:none;margin-bottom:3px;">&#8599; SambaNova Cloud</a>'
        '<a href="https://aistudio.google.com" target="_blank" style="display:block;font-size:0.72rem;color:#1D4ED8;text-decoration:none;">&#8599; Google AI Studio</a>'
        '</div>'
    )

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

    # BOTÓN PARA RESETEAR TODOS LOS CONTADORES
    if total_global > 0:
        if st.button("Resetear contadores", type="secondary", key="reset_tokens"):
            for p in PROVIDERS:
                for m in ("prompt", "completion", "calls"):
                    st.session_state[f"tokens_{p}_{m}"] = 0
            st.rerun()
