# ═══════════════════════════════════════════════════════════════════════════════
# UI/TABS/TABS_JSON.PY — MÓDULO CONVERSOR DE ARCHIVOS A SCHEMA JSON
# AnalytiQ AI Suite
#
# El usuario sube un archivo real (Excel, CSV, TSV) y la app extrae
# automáticamente la ESTRUCTURA (tablas + columnas) en formato JSON,
# listo para usar en el panel izquierdo de la app o descargar.
#
# Flujo:
#   1. Usuario sube archivo (.xlsx / .xls / .csv / .tsv)
#   2. La app lee SOLO las cabeceras (nunca los datos)
#   3. Genera el schema JSON compatible con el panel izquierdo
#   4. Previsualiza la estructura y descarga el .json
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st

from services.json_converter import extract_schema, get_sheet_names


# ── INICIALIZACIÓN DE SESSION STATE ──────────────────────────────────────────

def init_json_state():
    """INICIALIZA EL SESSION STATE DEL MÓDULO CONVERSOR JSON."""
    defaults = {
        "json_result":     None,   # Schema JSON generado como string
        "json_stats":      None,   # Estadísticas del schema extraído
        "json_file_bytes": None,   # Bytes del archivo subido
        "json_filename":   None,   # Nombre del archivo subido
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── RENDER PRINCIPAL ──────────────────────────────────────────────────────────

def render_tabs_json():
    """RENDERIZA EL MÓDULO CONVERSOR DE ARCHIVOS A SCHEMA JSON."""
    ss = st.session_state

    # ── CABECERA ──────────────────────────────────────────────────────────────
    st.markdown("""
        <div class="card module-json">
            <div class="module-json-header">
                <h3>Conversor a Schema JSON · AnalytiQ AI</h3>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="card">
            <p class="card-title">Qué hace este módulo</p>
            <p class="hint-text">
                Sube tu archivo Excel, CSV o TSV y la app extrae automáticamente
                la estructura del modelo (nombres de hojas y columnas) en formato JSON.
                El archivo generado es compatible directamente con el panel izquierdo
                de cualquier plataforma de la app — súbelo ahí para empezar a generar
                fórmulas, validar o documentar con IA.
            </p>
            <span class="json-badge">Solo extrae estructura · Nunca lee tus datos · 100% Local</span>
        </div>
    """, unsafe_allow_html=True)

    # ── ZONA DE CARGA ─────────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Subir archivo</p>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Arrastra aquí tu archivo o haz clic para buscar",
        type=["xlsx", "xls", "csv", "tsv"],
        key="json_file_uploader",
        help="Soporta Excel (.xlsx, .xls), CSV y TSV. Solo se leen las cabeceras, nunca los datos.",
        label_visibility="collapsed",
    )

    if uploaded is not None:
        file_bytes = uploaded.read()
        ss.json_file_bytes = file_bytes
        ss.json_filename   = uploaded.name
        # Limpiar resultado anterior si cambia el archivo
        ss.json_result = None
        ss.json_stats  = None

        ext     = uploaded.name.rsplit(".", 1)[-1].upper()
        size_kb = round(len(file_bytes) / 1024, 1)
        sheets  = get_sheet_names(file_bytes, uploaded.name)

        st.markdown(
            f'<div class="status-ok"><span class="status-dot"></span>'
            f'{uploaded.name} · {ext} · {size_kb} KB'
            + (f' · {len(sheets)} hojas detectadas' if sheets else '')
            + '</div>',
            unsafe_allow_html=True,
        )

        if sheets:
            st.markdown(
                '<p class="hint-note">Hojas: ' + ' · '.join(f'<b>{s}</b>' for s in sheets) + '</p>',
                unsafe_allow_html=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── SELECTOR DE HOJAS Y BOTÓN DE EXTRACCIÓN ──────────────────────────────
    if ss.json_file_bytes:
        sheets = get_sheet_names(ss.json_file_bytes, ss.json_filename)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<p class="card-title">Opciones de extracción</p>', unsafe_allow_html=True)

        # Mostrar selector de hojas solo si es Excel con más de una hoja
        sheet_selection = None
        if sheets and len(sheets) > 1:
            col_mode, col_sheet = st.columns([1, 2])

            with col_mode:
                modo = st.radio(
                    "Qué hojas exportar",
                    options=["Todas las hojas", "Una hoja específica"],
                    key="json_modo_hojas",
                )

            with col_sheet:
                if modo == "Una hoja específica":
                    sheet_selection = st.selectbox(
                        "Selecciona la hoja",
                        options=sheets,
                        key="json_sheet_selector",
                    )
                    st.markdown(
                        f'<p class="hint-note">Se exportará solo la hoja: <b>{sheet_selection}</b></p>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<p class="hint-note">Se exportarán las {len(sheets)} hojas como tablas independientes.</p>',
                        unsafe_allow_html=True,
                    )
        elif sheets and len(sheets) == 1:
            sheet_selection = sheets[0]
            st.markdown(
                f'<p class="hint-note">El archivo tiene una sola hoja: <b>{sheets[0]}</b></p>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        col_btn, col_hint = st.columns([1, 2])
        with col_btn:
            run = st.button(
                "Extraer schema JSON",
                type="primary",
                key="json_btn_convert",
            )
        with col_hint:
            st.markdown(
                '<p class="hint-note" style="padding-top:10px;">'
                'Se leen solo las cabeceras, nunca los datos. '
                'El proceso es instantáneo independientemente del tamaño del archivo.'
                '</p>',
                unsafe_allow_html=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # ── PROCESO ───────────────────────────────────────────────────────────
        if run:
            # Determinar si exportar una hoja o todas
            exportar_hoja = None
            if sheets and len(sheets) > 1:
                modo_actual = st.session_state.get("json_modo_hojas", "Todas las hojas")
                if modo_actual == "Una hoja específica":
                    exportar_hoja = st.session_state.get("json_sheet_selector", sheets[0])
            elif sheets:
                exportar_hoja = sheets[0]

            label_status = (
                f"Extrayendo hoja '{exportar_hoja}'..."
                if exportar_hoja
                else f"Extrayendo todas las hojas..."
            )

            with st.status(label_status, expanded=True) as status:
                st.write(f"Leyendo cabeceras de {ss.json_filename}...")
                try:
                    json_str, stats = extract_schema(
                        ss.json_file_bytes,
                        ss.json_filename,
                        only_sheet=exportar_hoja,
                    )
                    ss.json_result = json_str
                    ss.json_stats  = stats
                    status.update(
                        label=f"Schema listo · {stats['tables']} tabla(s) · {stats['total_cols']} columnas",
                        state="complete",
                    )
                    st.toast("Schema JSON generado")
                except Exception as e:
                    status.update(label="Error al extraer schema", state="error")
                    st.error(f"Error: {e}")

    # ── RESULTADO ─────────────────────────────────────────────────────────────
    if ss.json_result and ss.json_stats:
        _render_result(ss.json_result, ss.json_stats, ss.json_filename)


# ── HELPER: RENDERIZAR RESULTADO ──────────────────────────────────────────────

def _render_result(json_str: str, stats: dict, filename: str):
    """RENDERIZA EL SCHEMA GENERADO CON PREVISUALIZACIÓN Y DESCARGA."""
    ss = st.session_state

    # ── ESTADÍSTICAS ──────────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Schema extraído</p>', unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Tablas / Hojas", stats["tables"])
    with col_b:
        st.metric("Total columnas", stats["total_cols"])
    with col_c:
        st.metric("Tamaño schema", f"{stats['size_kb']} KB")

    # Resumen por tabla
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p class="card-title">Estructura detectada</p>', unsafe_allow_html=True)

    import json
    schema = json.loads(json_str)
    for table in schema["tables"]:
        col_count = len(table["columns"])
        with st.expander(f"📋 {table['name']} — {col_count} columnas"):
            cols = [c["name"] for c in table["columns"]]
            # Mostrar en 3 columnas para ahorrar espacio
            col1, col2, col3 = st.columns(3)
            for i, col_name in enumerate(cols):
                [col1, col2, col3][i % 3].caption(f"↳ {col_name}")

    st.markdown('</div>', unsafe_allow_html=True)

    # ── DESCARGA Y USO ────────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Descargar y usar</p>', unsafe_allow_html=True)

    output_name = filename.rsplit(".", 1)[0] + "_schema.json"

    col_dl, col_clear = st.columns([1, 1])
    with col_dl:
        st.download_button(
            label=f"⬇ Descargar {output_name}",
            data=json_str.encode("utf-8"),
            file_name=output_name,
            mime="application/json",
            key="json_download_btn",
            use_container_width=True,
        )
    with col_clear:
        if st.button("Limpiar", type="secondary", key="json_clear_result"):
            ss.json_result = None
            ss.json_stats  = None
            st.rerun()

    st.markdown("""
        <div style="background:#FFFBEB;border:1px solid #D97706;border-left:4px solid #B45309;
                    border-radius:8px;padding:14px 18px;margin-top:12px;">
            <p style="margin:0 0 6px 0;font-size:0.7rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.08em;color:#B45309;">Cómo usar este schema</p>
            <p style="margin:0;font-size:0.83rem;color:#374151;line-height:1.6;">
                1. Descarga el archivo <b>_schema.json</b><br>
                2. Ve a cualquier plataforma (Power BI, Looker, Sheets, Excel)<br>
                3. En el panel izquierdo selecciona <b>Subir JSON</b><br>
                4. Sube el schema descargado<br>
                5. La IA ya conoce tu modelo — genera fórmulas, valida y documenta
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── PREVISUALIZACIÓN DEL JSON ─────────────────────────────────────────────
    with st.expander("Ver JSON completo"):
        st.code(json_str, language="json")
