# HELPERS DE RENDERIZADO COMPARTIDOS ENTRE TABS DE POWER BI Y LOOKER STUDIO
# FUNCIONES REUTILIZABLES PARA MOSTRAR CÓDIGO, VALIDACIONES Y RESULTADOS

import streamlit as st


def render_resultado(text: str, code_lang: str = "sql"):
    """
    RENDERIZA UN TEXTO CON BLOQUES DE CÓDIGO FORMATEADOS.
    SEPARA BLOQUES ```dax / ```looker DEL TEXTO EXPLICATIVO.
    """
    pattern = r"```(?:dax|DAX|looker|LOOKER|sql|SQL)?\n?(.*?)```"
    import re
    partes    = re.split(pattern, text, flags=re.DOTALL)
    dax_count = 0
    for idx, parte in enumerate(partes):
        parte = parte.strip()
        if not parte:
            continue
        if idx % 2 == 0:
            st.markdown(parte)
        else:
            dax_count += 1
            st.markdown(f'<p class="dax-label">Bloque {dax_count}</p>', unsafe_allow_html=True)
            st.code(parte, language=code_lang)


def render_validation(result: dict):
    """RENDERIZA EL RESULTADO DE UNA VALIDACIÓN CON ESTADO, PUNTUACIÓN Y LISTAS"""
    estado       = result.get("estado", "INVALIDA")
    puntuacion   = result.get("puntuacion", 0)
    resumen      = result.get("resumen", "")
    errores      = result.get("errores_criticos", [])
    advertencias = result.get("advertencias", [])
    sugerencias  = result.get("sugerencias", [])

    color_estado = {
        "VALIDA": "#15803D",
        "VALIDA CON ADVERTENCIAS": "#B45309",
        "INVALIDA": "#DC2626",
    }.get(estado, "#6B7280")

    st.markdown(f"""
    <div class="verdict-card" style="border-left: 4px solid {color_estado};">
        <div class="verdict-header">
            <span style="font-size:1rem;font-weight:700;color:{color_estado};">{estado}</span>
            <span style="font-size:1.8rem;font-weight:700;color:{color_estado};">
                {puntuacion}<span style="font-size:0.9rem;color:#6B7280;">/10</span>
            </span>
        </div>
        <p class="verdict-resumen">{resumen}</p>
    </div>
    """, unsafe_allow_html=True)

    if errores:
        st.markdown('<p class="validation-section-title errors">Errores criticos</p>',
                    unsafe_allow_html=True)
        for e in errores:
            st.markdown(f'<div class="validation-item error">{e}</div>', unsafe_allow_html=True)

    if advertencias:
        st.markdown('<p class="validation-section-title warnings">Advertencias de logica</p>',
                    unsafe_allow_html=True)
        for a in advertencias:
            st.markdown(f'<div class="validation-item warning">{a}</div>', unsafe_allow_html=True)

    if sugerencias:
        st.markdown('<p class="validation-section-title tips">Sugerencias de mejora</p>',
                    unsafe_allow_html=True)
        for s in sugerencias:
            st.markdown(f'<div class="validation-item tip">{s}</div>', unsafe_allow_html=True)

    if not errores and not advertencias:
        st.markdown(
            '<div class="validation-ok">No se detectaron errores ni advertencias. '
            'La medida/expresión parece correcta.</div>',
            unsafe_allow_html=True,
        )
