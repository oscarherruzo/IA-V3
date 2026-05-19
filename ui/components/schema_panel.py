# PANEL IZQUIERDO: CARGA DE SCHEMA (JSON O SQL SERVER), ESTADO DE API Y PRIVACIDAD
# COMPATIBLE CON SCHEMAS DE POWER BI, LOOKER STUDIO, GOOGLE SHEETS Y EXCEL

import json
import streamlit as st
from sqlalchemy import create_engine, text as sql_text


# ── INICIALIZACIÓN DEL SESSION STATE DE SCHEMA ────────────────────────────────

def init_schema_state():
    defaults = {
        "cached_schema":      None,
        "cached_schema_name": None,
        "sql_server":         "",
        "sql_databases":      [],
        "sql_connected":      False,
        "sql_schema_source":  "json",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── RENDER DEL PANEL ──────────────────────────────────────────────────────────

def render_schema_panel(platform: str) -> dict | None:
    """
    RENDERIZA EL PANEL IZQUIERDO DE CARGA DE SCHEMA.
    DEVUELVE EL SCHEMA ACTIVO O UN SCHEMA DE DEMOSTRACIÓN.

    Args:
        platform: "power_bi", "looker", "sheets" o "excel"

    Returns:
        dict schema o None
    """
    st.markdown('<div class="card">', unsafe_allow_html=True)

    # Adaptar dinámicamente etiquetas semánticas según la plataforma seleccionada
    if platform == "power_bi":
        label, entity_single, entity_plural = "Power BI", "tabla", "tablas"
    elif platform == "looker":
        label, entity_single, entity_plural = "Looker Studio", "fuente", "fuentes"
    elif platform == "sheets":
        label, entity_single, entity_plural = "Google Sheets", "hoja", "hojas"
    else:
        label, entity_single, entity_plural = "Microsoft Excel", "hoja", "hojas"

    st.markdown(f'<p class="card-title">Modelo de datos · {label}</p>', unsafe_allow_html=True)

    # Permitir extraer desde base de datos SQL para cualquier entorno de modelado
    src_option = st.radio(
        "Origen del schema",
        options=["Subir JSON", "SQL Server"],
        horizontal=True,
        label_visibility="collapsed",
        key=f"schema_source_radio_{platform}",
    )
    st.markdown("<hr style='margin:8px 0 14px 0;border-color:#E5E7EB;'>", unsafe_allow_html=True)

    current_schema = None

    # ── OPCIÓN A: JSON ────────────────────────────────────────────────────────
    if src_option == "Subir JSON":
        st.session_state.sql_schema_source = "json"

        uploaded_file = st.file_uploader(
            f"Sube el JSON de metadatos semánticos",
            type=["json"],
            help=f"Solo se procesan nombres de {entity_plural} y columnas. Nunca datos reales.",
            key=f"uploader_{platform}",
        )

        if uploaded_file is not None:
            if uploaded_file.name != st.session_state.cached_schema_name:
                try:
                    data = json.load(uploaded_file)
                    st.session_state.cached_schema = {
                        "tables": [
                            {
                                "name":          t["name"],
                                "columns":       [
                                    {k: v for k, v in c.items() if k in ("name", "description", "type")}
                                    for c in t.get("columns", [])
                                ],
                                "relationships": t.get("relationships", []),
                            }
                            for t in data.get("tables", [])
                        ]
                    }
                    st.session_state.cached_schema_name = uploaded_file.name
                except Exception:
                    st.error("El archivo JSON no tiene un formato válido.")

            current_schema = st.session_state.cached_schema

            if current_schema:
                n = len(current_schema["tables"])
                st.markdown(
                    f'<div class="status-ok"><span class="status-dot"></span>'
                    f'{n} {entity_plural if n != 1 else entity_single} cargadas</div>',
                    unsafe_allow_html=True,
                )
                for t in current_schema["tables"]:
                    rels_count      = len(t.get("relationships", []))
                    titulo_expander = f"{t['name']} ({rels_count} rels)" if rels_count > 0 else t["name"]
                    with st.expander(titulo_expander):
                        st.markdown("**Columnas / Campos:**")
                        for col in t["columns"]:
                            st.caption(f"↳ {col['name']}")
                        if t.get("relationships"):
                            st.markdown("**Relaciones / Claves:**")
                            for rel in t["relationships"]:
                                st.caption(f"{rel['from_column']} → {rel['to_table']}[{rel['to_column']}]")
        else:
            st.info("Sube un archivo JSON para comenzar o extrae desde base de datos.", icon="📂")
            current_schema = {"tables": [{"name": "Ventas", "columns": [{"name": "Importe"}]}]}

    # ── OPCIÓN B: SQL SERVER (EXTRACTOR INTEGRADO MULTI-PLATAFORMA) ───────────
    elif src_option == "SQL Server":
        st.session_state.sql_schema_source = "sqlserver"
        current_schema = _render_sql_server_panel(platform, entity_single, entity_plural)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── ESTADO DE LAS API KEYS ────────────────────────────────────────────────
    _render_api_status()

    # ── NOTA DE PRIVACIDAD ────────────────────────────────────────────────────
    st.markdown("""
        <div class="card-privacy">
            <p class="card-title">Privacidad</p>
            <p>Solo se envían <strong style="color:var(--theme-primary);">metadatos</strong> a la IA:
            nombres de tablas y columnas estructurales. Ningún dato real abandona tu entorno.</p>
        </div>
    """, unsafe_allow_html=True)

    return current_schema


# ── PANEL SQL SERVER ──────────────────────────────────────────────────────────

def _render_sql_server_panel(platform: str, entity_single: str, entity_plural: str):
    current_schema = None

    server_input = st.text_input(
        "Servidor SQL Server",
        value=st.session_state.sql_server,
        placeholder="Ej: localhost\\SQLEXPRESS  o  192.168.1.10",
        key=f"sql_server_input_{platform}",
    )

    col_conn, col_hint_sql = st.columns([1, 1])
    with col_conn:
        btn_connect = st.button("Conectar y listar BBDDs", type="primary", key=f"btn_sql_connect_{platform}")
    with col_hint_sql:
        st.markdown('<p class="hint-note">Windows Auth · ODBC 17</p>', unsafe_allow_html=True)

    if btn_connect:
        if not server_input.strip():
            st.warning("Introduce el nombre o IP del servidor.")
        else:
            st.session_state.sql_server    = server_input.strip()
            st.session_state.sql_databases = []
            st.session_state.sql_connected = False
            try:
                _conn_master = (
                    f"mssql+pyodbc://@{st.session_state.sql_server}/master"
                    f"?driver=ODBC+Driver+17+for+SQL+Server"
                    f"&TrustServerCertificate=yes&timeout=8"
                )
                _eng_master = create_engine(_conn_master)
                with _eng_master.connect() as _c:
                    rows = _c.execute(sql_text(
                        "SELECT name FROM sys.databases "
                        "WHERE database_id > 4 ORDER BY name"
                    ))
                    st.session_state.sql_databases = [r[0] for r in rows]
                st.session_state.sql_connected = True
                st.toast(f"{len(st.session_state.sql_databases)} bases de datos encontradas")
            except Exception as _e:
                st.error(f"No se pudo conectar al servidor: {_e}")

    if st.session_state.sql_connected and st.session_state.sql_databases:
        dbs = st.session_state.sql_databases
        st.markdown(
            f'<div class="status-ok"><span class="status-dot"></span>'
            f'Conectado · {len(dbs)} bases de datos</div>',
            unsafe_allow_html=True,
        )

        with st.expander(f"Bases de datos disponibles ({len(dbs)})", expanded=True):
            for i, db_name in enumerate(dbs, 1):
                st.caption(f"{i}. {db_name}")

        db_index = st.number_input(
            "Selecciona nº de base de datos",
            min_value=1, max_value=len(dbs), value=1, step=1,
            key=f"sql_db_index_{platform}",
        )
        selected_db = dbs[int(db_index) - 1]
        st.markdown(
            f'<p class="hint-ok">Seleccionada: <strong>{selected_db}</strong></p>',
            unsafe_allow_html=True,
        )

        btn_extract = st.button(
            f"Extraer relacional · {selected_db}",
            type="primary", key=f"btn_sql_extract_{platform}",
        )

        if btn_extract:
            with st.status(f"Extrayendo metadatos de {selected_db}...", expanded=True) as _st:
                st.write(f"Consultando {entity_plural} y columnas relacionales...")
                try:
                    _conn_db = (
                        f"mssql+pyodbc://@{st.session_state.sql_server}/{selected_db}"
                        f"?driver=ODBC+Driver+17+for+SQL+Server"
                        f"&TrustServerCertificate=yes"
                    )
                    _eng_db = create_engine(_conn_db)

                    _q_cols = sql_text("""
                        SELECT
                            t.TABLE_SCHEMA + '.' + t.TABLE_NAME AS table_name,
                            c.COLUMN_NAME                        AS column_name
                        FROM   INFORMATION_SCHEMA.TABLES  t
                        JOIN   INFORMATION_SCHEMA.COLUMNS c
                               ON  t.TABLE_NAME   = c.TABLE_NAME
                               AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
                        WHERE  t.TABLE_TYPE = 'BASE TABLE'
                        ORDER  BY t.TABLE_SCHEMA, t.TABLE_NAME, c.ORDINAL_POSITION
                    """)
                    _q_fks = sql_text("""
                        SELECT
                            SCHEMA_NAME(fk_tab.schema_id) + '.' + fk_tab.name AS fk_table,
                            fk_col.name                                        AS fk_column,
                            SCHEMA_NAME(pk_tab.schema_id) + '.' + pk_tab.name AS pk_table,
                            pk_col.name                                        AS pk_column
                        FROM   sys.foreign_keys        fk
                        JOIN   sys.tables              fk_tab ON fk.parent_object_id     = fk_tab.object_id
                        JOIN   sys.tables              pk_tab ON fk.referenced_object_id = pk_tab.object_id
                        JOIN   sys.foreign_key_columns fkc    ON fk.object_id = fkc.constraint_object_id
                        JOIN   sys.columns             fk_col ON fkc.parent_object_id    = fk_col.object_id
                                                              AND fkc.parent_column_id   = fk_col.column_id
                        JOIN   sys.columns             pk_col ON fkc.referenced_object_id = pk_col.object_id
                                                              AND fkc.referenced_column_id = pk_col.column_id
                    """)

                    _tables_map = {}
                    with _eng_db.connect() as _c2:
                        st.write("Mapeando columnas estructurales...")
                        for _tname, _cname in _c2.execute(_q_cols).fetchall():
                            if _tname not in _tables_map:
                                _tables_map[_tname] = {"columns": [], "relationships": []}
                            _tables_map[_tname]["columns"].append({"name": _cname})

                        st.write("Mapeando restricciones de claves e integridad (FK)...")
                        for _fk_t, _fk_c, _pk_t, _pk_c in _c2.execute(_q_fks).fetchall():
                            if _fk_t in _tables_map:
                                _tables_map[_fk_t]["relationships"].append({
                                    "from_column": _fk_c,
                                    "to_table":    _pk_t,
                                    "to_column":   _pk_c,
                                    "direction":   "Many-to-One",
                                })

                    _schema_extracted = {
                        "tables": [
                            {"name": name, "columns": data["columns"], "relationships": data["relationships"]}
                            for name, data in _tables_map.items()
                        ]
                    }
                    st.session_state.cached_schema      = _schema_extracted
                    st.session_state.cached_schema_name = f"sqlserver:{selected_db}"
                    _st.update(
                        label=f"Schema semántico extraído · {len(_schema_extracted['tables'])} {entity_plural}",
                        state="complete",
                    )
                    st.toast("Esquema semántico listo")
                except Exception as _e:
                    _st.update(label="Error crítico al extraer metadatos", state="error")
                    st.error(f"Error: {_e}")

    # MOSTRAR SCHEMA EXTRAÍDO DESDE LA BASE DE DATOS ACTIVA
    if (
        st.session_state.cached_schema
        and str(st.session_state.cached_schema_name).startswith("sqlserver:")
    ):
        current_schema = st.session_state.cached_schema
        db_label = st.session_state.cached_schema_name.replace("sqlserver:", "")
        st.markdown(
            f'<div class="status-ok"><span class="status-dot"></span>'
            f'{len(current_schema["tables"])} {entity_plural} · base: {db_label}</div>',
            unsafe_allow_html=True,
        )
        for t in current_schema["tables"]:
            rels_count      = len(t.get("relationships", []))
            titulo_expander = f"{t['name']} ({rels_count} rels)" if rels_count > 0 else t["name"]
            with st.expander(titulo_expander):
                st.markdown("**Columnas / Atributos:**")
                for col in t["columns"]:
                    st.caption(f"↳ {col['name']}")
                if t.get("relationships"):
                    st.markdown("**Integridad referencial (FK):**")
                    for rel in t["relationships"]:
                        st.caption(f"{rel['from_column']} → {rel['to_table']}[{rel['to_column']}]")

        st.markdown("<div style='margin-top:12px;'>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Descargar schema mapeado como JSON",
            data=json.dumps(current_schema, ensure_ascii=False, indent=2),
            file_name=f"schema_{db_label}.json",
            mime="application/json",
            key=f"btn_download_schema_{platform}",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    elif not st.session_state.sql_connected:
        current_schema = {"tables": [{"name": "Ventas", "columns": [{"name": "Importe"}]}]}

    return current_schema


# ── ESTADO DE LAS API KEYS ────────────────────────────────────────────────────

def _render_api_status():
    """RENDERIZA EL ESTADO DE TODOS LOS PROVEEDORES DE IA CENTRALIZADOS"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Estado de los servicios de IA</p>', unsafe_allow_html=True)

    ss = st.session_state

    # 9ROUTER
    router_url = ss.get("router_base_url", "").strip()
    router_key = ss.get("router_api_key", "").strip()
    
    if router_url and router_key:
        st.markdown(
            '<div class="status-ok"><span class="status-dot"></span>9Router · activo (primario)</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<p class="hint-warn">⚠️ 9Router no configurado</p>', unsafe_allow_html=True)

    # GROQ
    if ss.get("groq_api_key", "").strip():
        st.markdown(
            '<div class="status-ok"><span class="status-dot"></span>Groq · fallback 1 activo</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<p class="api-note">Groq · no disponible</p>', unsafe_allow_html=True)

    # SAMBANOVA
    if ss.get("sambanova_api_key", "").strip():
        st.markdown(
            '<div class="status-ok"><span class="status-dot"></span>SambaNova · fallback 2 activo</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<p class="api-note">SambaNova · no disponible</p>', unsafe_allow_html=True)

    # GEMINI
    if ss.get("gemini_api_key", "").strip():
        st.markdown(
            '<div class="status-ok"><span class="status-dot"></span>Gemini · fallback 3 activo</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<p class="api-note">Gemini · no disponible</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)