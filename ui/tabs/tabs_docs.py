# ═══════════════════════════════════════════════════════════════════════════════
# UI/TABS/TABS_DOCS.PY — TAB INDEPENDIENTE DE DOCUMENTACIÓN
# AnalytiQ AI Suite
#
# Orden de renderizado (UX optimizado — sin scroll):
#   1. Cabecera
#   2. Botón de generar  ← siempre visible arriba
#   3. Resultado         ← aparece justo debajo del botón
#   4. Configuración     ← selector de plataforma y carga de schema
#   5. Detalle del schema cargado
# ═══════════════════════════════════════════════════════════════════════════════

import json
import streamlit as st

from modules.power_bi.core_functions import generate_doc as generate_doc_powerbi
from modules.looker.core_functions   import generate_doc_looker
from modules.sheets.core_functions   import generate_doc_sheets
from modules.excel.core_functions    import generate_doc_excel
from core.pdf                        import build_doc_pdf

PLATFORM_LABELS = {
    "power_bi": "Power BI (DAX)",
    "looker":   "Looker Studio",
    "sheets":   "Google Sheets",
    "excel":    "Microsoft Excel",
}

GENERATOR_MAP = {
    "power_bi": generate_doc_powerbi,
    "looker":   generate_doc_looker,
    "sheets":   generate_doc_sheets,
    "excel":    generate_doc_excel,
}


def init_docs_state():
    defaults = {
        "docs_doc_result":   None,
        "docs_schema":       None,
        "docs_schema_name":  None,
        "docs_platform":     "power_bi",
        "docs_doc_platform": "power_bi",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_tabs_docs():
    ss = st.session_state

    # CABECERA
    st.markdown("""
        <div class="card module-docs">
            <div class="module-docs-header">
                <h3>Generador de Documentación · AnalytiQ AI</h3>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ── 1. BOTÓN — siempre arriba ─────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col_btn, col_hint = st.columns([1, 2])
    with col_btn:
        run_doc = st.button(
            "Generar documentación completa",
            type="primary",
            key="docs_btn_generate",
            disabled=(ss.docs_schema is None),
        )
    with col_hint:
        if ss.docs_schema is None:
            st.markdown(
                '<p class="hint-warn">Sube un JSON de schema (abajo) para activar la generación.</p>',
                unsafe_allow_html=True,
            )
        else:
            n       = len(ss.docs_schema.get("tables", []))
            n_lotes = max(1, (n + 2) // 3)
            plat    = PLATFORM_LABELS.get(ss.docs_platform, ss.docs_platform)
            st.markdown(
                f'<p class="hint-note">{n} tablas · {n_lotes} lote(s) · {plat} · ~{n_lotes * 20}s</p>',
                unsafe_allow_html=True,
            )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── 2. PROCESO ────────────────────────────────────────────────────────────
    if run_doc:
        schema   = ss.docs_schema
        n        = len(schema.get("tables", []))
        n_lotes  = max(1, (n + 2) // 3)
        plat     = PLATFORM_LABELS.get(ss.docs_platform, ss.docs_platform)
        gen_func = GENERATOR_MAP.get(ss.docs_platform, generate_doc_powerbi)

        with st.status(
            f"Documentando {n} tablas en {n_lotes} lote(s) · {plat}...",
            expanded=True,
        ) as status:
            progress = st.progress(0, text="Iniciando...")

            def on_prog(step, total, names, msg):
                pct = min(int((step / total) * 95), 95)
                progress.progress(pct, text=f"Lote {step}/{total}: {', '.join(names[:3])} · {msg}")

            try:
                doc_data = gen_func(schema, progress_callback=on_prog)
                progress.progress(100, text="Completado")
                ss.docs_doc_result   = doc_data
                ss.docs_doc_platform = ss.docs_platform
                status.update(
                    label=f"Documentación lista · {len(doc_data.get('tablas', []))} tablas documentadas",
                    state="complete",
                )
                st.toast("Documentación generada correctamente")
            except Exception as e:
                status.update(label="Error al generar", state="error")
                st.error(f"Error de API: {e}")

    # ── 3. RESULTADO — justo debajo del botón ────────────────────────────────
    if ss.docs_doc_result:
        _render_doc_result(ss.docs_doc_result, ss.get("docs_doc_platform", "power_bi"))

    # ── 4. CONFIGURACIÓN ─────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Configuración</p>', unsafe_allow_html=True)

    col_plat, col_upload = st.columns([1, 2])
    with col_plat:
        selected_platform = st.selectbox(
            "Plataforma a documentar",
            options=list(PLATFORM_LABELS.keys()),
            format_func=lambda x: PLATFORM_LABELS[x],
            key="docs_platform_select",
            index=list(PLATFORM_LABELS.keys()).index(ss.docs_platform),
        )
        ss.docs_platform = selected_platform

    with col_upload:
        uploaded = st.file_uploader(
            "Sube el JSON del modelo de datos",
            type=["json"],
            key="docs_file_uploader",
            help="Solo se procesan metadatos: nombres de tablas y columnas. Nunca datos reales.",
        )
        if uploaded is not None:
            if uploaded.name != ss.docs_schema_name:
                try:
                    raw_data = json.load(uploaded)
                    ss.docs_schema = {
                        "tables": [
                            {
                                "name":          t["name"],
                                "columns":       [{"name": c["name"]} for c in t.get("columns", [])],
                                "relationships": t.get("relationships", []),
                            }
                            for t in raw_data.get("tables", [])
                        ]
                    }
                    ss.docs_schema_name = uploaded.name
                    st.success(f"Schema cargado: {len(ss.docs_schema['tables'])} tablas.")
                except Exception:
                    st.error("El archivo JSON no tiene un formato válido.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 5. DETALLE DEL SCHEMA ─────────────────────────────────────────────────
    if ss.docs_schema:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="card-title">Schema cargado</p>', unsafe_allow_html=True)
        n_tables = len(ss.docs_schema["tables"])
        st.markdown(
            f'<div class="status-ok"><span class="status-dot"></span>'
            f'{n_tables} tabla(s) listas · {PLATFORM_LABELS.get(ss.docs_platform)}</div>',
            unsafe_allow_html=True,
        )
        for t in ss.docs_schema["tables"]:
            rels = len(t.get("relationships", []))
            with st.expander(f"{t['name']} ({len(t['columns'])} cols · {rels} rels)"):
                for col in t["columns"]:
                    st.caption(f"↳ {col['name']}")
        st.markdown('</div>', unsafe_allow_html=True)


def _render_doc_result(doc_data: dict, platform: str):
    ss = st.session_state

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Resultado de la documentación</p>', unsafe_allow_html=True)

    resumen = doc_data.get("resumen", "")
    if resumen:
        st.markdown(resumen)

    n_tablas = len(doc_data.get("tablas", []))
    st.markdown(
        f'<p class="hint-ok">{n_tablas} tablas documentadas correctamente.</p>',
        unsafe_allow_html=True,
    )

    # Descarga y limpieza — arriba del detalle para no tener que bajar
    col_pdf, col_clear = st.columns([1, 1])
    with col_pdf:
        try:
            pdf_bytes = build_doc_pdf(doc_data, platform=platform)
            st.download_button(
                label="Descargar PDF",
                data=pdf_bytes,
                file_name=f"documentacion_{platform}.pdf",
                mime="application/pdf",
                key="docs_download_pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Error al generar PDF: {e}")
    with col_clear:
        if st.button("Limpiar resultado", type="secondary", key="docs_clear_result"):
            ss.docs_doc_result = None
            st.rerun()

    # Detalle por tabla
    if doc_data.get("tablas"):
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title">Detalle por tabla</p>', unsafe_allow_html=True)
        for tabla in doc_data["tablas"]:
            nombre = tabla.get("nombre", "Sin nombre")
            with st.expander(f"{nombre}"):
                st.markdown(tabla.get("descripcion", ""))

    st.markdown('</div>', unsafe_allow_html=True)
