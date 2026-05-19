# TABS DE POWER BI: GENERAR, VALIDAR, EXPLICAR, EVALUAR Y CHAT
# INCLUYE MEDIDAS BASE, DAX RECOMENDADOS, HISTORIAL Y GENERACIÓN DE PDF

import streamlit as st

from modules.power_bi.generator       import generate_dax, generate_dax_recomendados
from modules.power_bi.core_functions  import (
    explain_dax, evaluate_dax, chat_con_modelo,
    generate_medidas_base, generate_doc,
)
from modules.power_bi.validator       import validate_dax
from core.pdf                         import build_doc_pdf
from ui.components.render_helpers                import render_resultado, render_validation


# ── INICIALIZACIÓN DE SESSION STATE POWER BI ──────────────────────────────────

def init_powerbi_state():
    defaults = {
        "pb_historial":           [],
        "pb_chat_history":        [],
        "pb_explain_result":      None,
        "pb_validation_result":   None,
        "pb_eval_result":         None,
        "pb_doc_result":          None,
        "pb_medidas_result":      None,
        "pb_recomendados_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── RENDER PRINCIPAL ──────────────────────────────────────────────────────────

def render_tabs_power_bi(current_schema: dict):
    """RENDERIZA LAS 5 TABS DE POWER BI EN LA COLUMNA CENTRAL"""

    tab_gen, tab_val, tab_exp, tab_eval, tab_chat = st.tabs([
        "◈  Generar DAX",
        "◈  Validar DAX",
        "◈  Explicar DAX",
        "◈  Evaluar DAX",
        "◈  Chat con el modelo",
    ])

    with tab_gen:
        _tab_generar(current_schema)

    with tab_val:
        _tab_validar(current_schema)

    with tab_exp:
        _tab_explicar(current_schema)

    with tab_eval:
        _tab_evaluar(current_schema)

    with tab_chat:
        _tab_chat(current_schema)


# ── TAB 1: GENERAR DAX ────────────────────────────────────────────────────────

def _tab_generar(schema: dict):
    ss = st.session_state
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Solicitud</p>', unsafe_allow_html=True)

    user_query = st.text_area(
        "Describe la lógica que necesitas",
        placeholder="Ej: Variación porcentual de ventas respecto al año anterior...",
        height=130, label_visibility="collapsed", key="pb_query_input",
    )

    col_btn1, col_btn2, col_hint = st.columns([1, 1, 1])
    with col_btn1:
        run = st.button("Generar DAX", type="primary", key="pb_btn_generar")
    with col_btn2:
        run_rec = st.button(
            "◈ DAX recomendados", type="secondary", key="pb_btn_recomendados",
            help="Analiza tu modelo y sugiere automáticamente las medidas DAX más útiles",
        )
    with col_hint:
        st.markdown('<p class="hint-note">9Router · Groq · SambaNova · Gemini fallback</p>',
                    unsafe_allow_html=True)

    # GENERAR DAX DESDE DESCRIPCIÓN
    if run:
        if user_query and schema:
            with st.status("Generando fórmula DAX...", expanded=True) as status:
                st.write("Analizando esquema de metadatos...")
                st.write("Construyendo lógica DAX...")
                try:
                    result = generate_dax(schema, user_query)
                    status.update(label="Fórmula generada", state="complete")
                    ss.pb_historial.insert(0, {"query": user_query, "result": result})
                    st.toast("Fórmula lista")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")
        else:
            st.warning("Introduce una solicitud y asegúrate de tener un modelo cargado.")

    # DAX RECOMENDADOS
    if run_rec:
        if schema is None or len(schema.get("tables", [])) <= 1:
            st.warning("Carga primero un modelo real (JSON o SQL Server).")
        else:
            with st.status("Analizando tu modelo...", expanded=True) as status:
                st.write("Detectando tablas de hechos y dimensiones...")
                st.write("Identificando KPIs relevantes para tu modelo...")
                st.write("Generando medidas DAX personalizadas...")
                try:
                    recomendados = generate_dax_recomendados(schema)
                    ss.pb_recomendados_result = recomendados
                    status.update(label="DAX recomendados listos", state="complete")
                    st.toast("Recomendaciones generadas")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")

    if ss.pb_recomendados_result:
        st.markdown('<hr class="hr-dark">', unsafe_allow_html=True)
        st.markdown('<p class="card-title">DAX recomendados para tu modelo</p>', unsafe_allow_html=True)
        render_resultado(ss.pb_recomendados_result)
        if st.button("Limpiar recomendados", type="secondary", key="pb_clear_rec"):
            ss.pb_recomendados_result = None
            st.rerun()

    # MEDIDAS BASE POR TABLA
    st.markdown('<hr class="hr-dark">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Medidas DAX segun el modelo</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Selecciona las tablas que te interesan y el nivel. '
        'La IA genera medidas listas para usar basadas en las columnas reales de tu modelo.</p>',
        unsafe_allow_html=True,
    )

    todas_tablas = [t["name"] for t in schema.get("tables", [])] if schema else []
    tablas_elegidas = st.multiselect(
        "Selecciona las tablas", options=todas_tablas,
        placeholder="Elige una o varias tablas...", key="pb_medidas_tablas",
    )

    col_nivel, col_gen = st.columns([1, 1])
    with col_nivel:
        nivel = st.selectbox("Nivel", options=["Basicas", "Avanzadas", "Ambas"], key="pb_nivel")
    with col_gen:
        st.markdown("<div style='padding-top:28px;'></div>", unsafe_allow_html=True)
        run_medidas = st.button("Generar medidas", type="primary", key="pb_btn_medidas")

    if run_medidas:
        if not tablas_elegidas:
            st.warning("Selecciona al menos una tabla.")
        else:
            n_lotes = max(1, (len(tablas_elegidas) + 4) // 5)
            with st.status(f"Generando medidas para {len(tablas_elegidas)} tablas en {n_lotes} lote(s)...", expanded=True) as status:
                progress = st.progress(0, text="Iniciando...")
                log_area = st.empty()

                def on_prog(idx, total, nombres):
                    pct = min(int((idx / total) * 95), 95)
                    txt = f"Lote {idx}/{total}: {', '.join(nombres[:3])}..."
                    progress.progress(pct, text=txt)
                    log_area.caption(txt)

                try:
                    medidas = generate_medidas_base(tablas_elegidas, nivel, schema, progress_callback=on_prog)
                    progress.progress(100, text="Completado")
                    ss.pb_medidas_result = {"medidas": medidas, "tablas": tablas_elegidas, "nivel": nivel}
                    status.update(label=f"{len(medidas)} medidas generadas en {n_lotes} lote(s)", state="complete")
                    st.toast("Medidas listas")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")

    if ss.pb_medidas_result:
        medidas_list = ss.pb_medidas_result.get("medidas", [])
        if medidas_list:
            tablas_con_medidas = {}
            for m in medidas_list:
                tabla = m.get("tabla", "Sin tabla")
                if tabla not in tablas_con_medidas:
                    tablas_con_medidas[tabla] = []
                tablas_con_medidas[tabla].append(m)

            for tabla, medidas_tabla in tablas_con_medidas.items():
                st.markdown(f'<p class="section-label">{tabla}</p>', unsafe_allow_html=True)
                for m in medidas_tabla:
                    nivel_val = m.get("nivel", "").lower()
                    badge_cls = "basica" if nivel_val == "basica" else "avanzada"
                    with st.expander(f"{m.get('nombre', '')}"):
                        st.markdown(f'<span class="nivel-badge {badge_cls}">{m.get("nivel","")}</span>',
                                    unsafe_allow_html=True)
                        st.caption(m.get("descripcion", ""))
                        st.code(m.get("codigo", ""), language="sql")

            if st.button("Limpiar medidas", type="secondary", key="pb_clear_medidas"):
                ss.pb_medidas_result = None
                st.rerun()
        else:
            st.warning("La IA no devolvió medidas. Intenta con menos tablas o diferente nivel.")

    st.markdown('</div>', unsafe_allow_html=True)

    # HISTORIAL
    if ss.pb_historial:
        st.markdown('<p class="card-title" style="margin:16px 0 12px 0;">Historial</p>',
                    unsafe_allow_html=True)
        for i, item in enumerate(ss.pb_historial):
            num    = len(ss.pb_historial) - i
            titulo = item["query"][:70] + ("..." if len(item["query"]) > 70 else "")
            with st.expander(f"#{num} — {titulo}"):
                render_resultado(item["result"])
        if st.button("Limpiar historial", type="secondary", key="pb_clear_historial"):
            ss.pb_historial = []
            st.rerun()


# ── TAB 2: VALIDAR DAX ────────────────────────────────────────────────────────

def _tab_validar(schema: dict):
    ss = st.session_state

    if ss.pb_validation_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title" style="margin-bottom:6px;">Código analizado</p>',
                    unsafe_allow_html=True)
        st.code(ss.pb_validation_result["codigo"], language="sql")
        st.markdown('<p class="card-title" style="margin:16px 0 4px 0;">Resultado de la validación</p>',
                    unsafe_allow_html=True)
        render_validation(ss.pb_validation_result)
        if st.button("Limpiar validación", type="secondary", key="pb_clear_validate"):
            ss.pb_validation_result = None
            st.rerun()


    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Validador de DAX</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Pega una medida DAX y la IA la validará contra tu schema: '
        'detecta tablas y columnas inexistentes, errores de sintaxis, '
        'problemas de lógica y te da una puntuación de calidad.</p>',
        unsafe_allow_html=True,
    )

    dax_to_validate = st.text_area(
        "Pega aquí la medida DAX a validar",
        placeholder="Ej:\nMargen Bruto % =\nVAR Ventas = SUM('FactVentas'[Importe])\nRETURN DIVIDE(Ventas, Ventas + Coste)",
        height=200, label_visibility="collapsed", key="pb_validate_input",
    )

    col_val_btn, col_val_hint = st.columns([1, 2])
    with col_val_btn:
        run_validate = st.button("Validar medida", type="primary", key="pb_btn_validate")
    with col_val_hint:
        if schema and len(schema.get("tables", [])) > 1:
            st.markdown('<p class="hint-ok">Schema cargado — validación completa activa</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<p class="hint-warn">Sin schema — solo validación lógica por IA</p>',
                        unsafe_allow_html=True)

    if run_validate:
        if not dax_to_validate.strip():
            st.warning("Pega una medida DAX para validar.")
        else:
            with st.status("Validando la medida DAX...", expanded=True) as status:
                st.write("Comprobando referencias de tablas y columnas en el schema...")
                st.write("Analizando sintaxis y lógica con IA...")
                try:
                    validation = validate_dax(dax_to_validate, schema)
                    ss.pb_validation_result = validation
                    estado = validation.get("estado", "INVALIDA")
                    if estado == "VALIDA":
                        status.update(label="Medida válida", state="complete")
                    elif estado == "VALIDA CON ADVERTENCIAS":
                        status.update(label="Válida con advertencias", state="complete")
                    else:
                        status.update(label="Se encontraron errores", state="error")
                    st.toast("Validación completada")
                except Exception as e:
                    status.update(label="Error en la validación", state="error")
                    st.error(f"Error de API: {e}")


    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 3: EXPLICAR DAX ───────────────────────────────────────────────────────

def _tab_explicar(schema: dict):
    ss = st.session_state

    if ss.pb_explain_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title" style="margin-bottom:6px;">Código analizado</p>',
                    unsafe_allow_html=True)
        st.code(ss.pb_explain_result["code"], language="sql")
        st.markdown('<p class="card-title" style="margin:16px 0 8px 0;">Explicación</p>',
                    unsafe_allow_html=True)
        st.markdown(ss.pb_explain_result["explanation"])
        if st.button("Limpiar análisis", type="secondary", key="pb_clear_explain"):
            ss.pb_explain_result = None
            st.rerun()


    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Explicame este DAX</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Pega cualquier medida DAX y la IA te la explicará '
        'línea por línea: qué hace, qué funciones usa, casos de uso y posibles mejoras.</p>',
        unsafe_allow_html=True,
    )

    dax_input = st.text_area(
        "Pega aquí tu medida DAX",
        placeholder="Ej:\nVentas YoY % =\nVAR VentasActual   = [Total Ventas]\nVAR VentasAnterior = CALCULATE([Total Ventas], SAMEPERIODLASTYEAR('Fecha'[Date]))\nRETURN DIVIDE(VentasActual - VentasAnterior, VentasAnterior)",
        height=200, label_visibility="collapsed", key="pb_explain_input",
    )

    col_exp_btn, col_exp_hint = st.columns([1, 2])
    with col_exp_btn:
        run_explain = st.button("Explicar medida", type="primary", key="pb_btn_explain")
    with col_exp_hint:
        st.markdown('<p class="hint-note">Funciona con cualquier medida DAX, aunque no sea de tu modelo actual</p>',
                    unsafe_allow_html=True)

    if run_explain:
        if not dax_input.strip():
            st.warning("Pega una medida DAX para explicar.")
        else:
            with st.status("Analizando la medida DAX...", expanded=True) as status:
                st.write("Identificando funciones y estructura...")
                st.write("Generando explicación línea por línea...")
                try:
                    explanation = explain_dax(dax_input, schema)
                    ss.pb_explain_result = {"code": dax_input.strip(), "explanation": explanation}
                    status.update(label="Explicación lista", state="complete")
                    st.toast("Explicación generada")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")


    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 4: EVALUAR DAX ────────────────────────────────────────────────────────

def _tab_evaluar(schema: dict):
    ss = st.session_state

    if ss.pb_eval_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title" style="margin-bottom:6px;">Código evaluado</p>',
                    unsafe_allow_html=True)
        st.code(ss.pb_eval_result["code"], language="sql")
        st.markdown('<p class="card-title" style="margin:16px 0 8px 0;">Evaluación de negocio</p>',
                    unsafe_allow_html=True)
        render_resultado(ss.pb_eval_result["evaluacion"])
        if st.button("Limpiar evaluación", type="secondary", key="pb_clear_eval"):
            ss.pb_eval_result = None
            st.rerun()


    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Evaluador de DAX</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Analiza si la lógica de negocio de tu medida tiene sentido '
        'dado el modelo: coherencia con las relaciones, riesgos de doble conteo, '
        'alternativas con otras tablas disponibles y puntuación de negocio.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="eval-info">Diferente al validador: no busca errores de sintaxis '
        'sino que evalua si la logica de negocio es correcta y optima para tu modelo.</div>',
        unsafe_allow_html=True,
    )

    dax_to_eval = st.text_area(
        "Pega aquí la medida DAX a evaluar",
        placeholder="Ej:\nMargen Neto % =\nVAR Ventas = SUM('FactVentas'[Importe])\nVAR Costes = SUM('FactCostes'[Total])\nRETURN DIVIDE(Ventas - Costes, Ventas)",
        height=200, label_visibility="collapsed", key="pb_eval_input",
    )

    col_eval_btn, col_eval_hint = st.columns([1, 2])
    with col_eval_btn:
        run_eval = st.button("Evaluar medida", type="primary", key="pb_btn_eval")
    with col_eval_hint:
        if schema and len(schema.get("tables", [])) > 1:
            st.markdown('<p class="hint-ok">Schema cargado — evaluación completa con contexto del modelo</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<p class="hint-warn">Sin schema — evaluación genérica sin contexto del modelo</p>',
                        unsafe_allow_html=True)

    if run_eval:
        if not dax_to_eval.strip():
            st.warning("Pega una medida DAX para evaluar.")
        else:
            with st.status("Evaluando la lógica de negocio...", expanded=True) as status:
                st.write("Analizando coherencia con el modelo de datos...")
                st.write("Evaluando relaciones y posibles riesgos...")
                st.write("Buscando alternativas en el schema...")
                try:
                    evaluacion = evaluate_dax(dax_to_eval, schema)
                    ss.pb_eval_result = {"code": dax_to_eval.strip(), "evaluacion": evaluacion}
                    status.update(label="Evaluación completada", state="complete")
                    st.toast("Evaluación lista")
                except Exception as e:
                    status.update(label="Error en la evaluación", state="error")
                    st.error(f"Error de API: {e}")


    # AVISO: DOCUMENTACIÓN MOVIDA A SU PROPIO MÓDULO INDEPENDIENTE
    # La funcionalidad de "Generar Documentación" ha sido extraída a la pestaña
    # global "📄 Docs" para centralizar la documentación de todas las plataformas.
    st.markdown('<hr class="hr-dark">', unsafe_allow_html=True)
    st.markdown("""
        <div style="background:#F8F5FF;border:1px solid #A855F7;border-left:4px solid #7C3AED;
                    border-radius:8px;padding:16px 20px;margin:8px 0;">
            <p style="margin:0 0 6px 0;font-size:0.7rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.08em;color:#7C3AED;">Módulo de Documentación</p>
            <p style="margin:0;font-size:0.85rem;color:#374151;">
                La generación de documentación completa con exportación a PDF se ha trasladado
                al módulo independiente <strong>📄 Docs</strong> en la barra de navegación superior.
                Desde ahí puedes documentar cualquier plataforma (Power BI, Looker, Sheets, Excel)
                con un selector unificado.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 5: CHAT CON EL MODELO ─────────────────────────────────────────────────

def _tab_chat(schema: dict):
    ss = st.session_state
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Chat con el modelo</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Pregunta libremente sobre tu modelo de datos: qué tablas usar, '
        'cómo calcular un KPI, si una relación tiene sentido o cómo construir una medida desde cero.</p>',
        unsafe_allow_html=True,
    )

    if ss.pb_chat_history:
        for turno in ss.pb_chat_history:
            st.markdown(f"""
            <div class="chat-user-bubble">
                <p class="chat-user-label">Tu pregunta</p>
                <p class="chat-user-text">{turno["pregunta"]}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="chat-ai-bubble">
                <p class="chat-ai-label">DAX Assistant</p>
            </div>
            """, unsafe_allow_html=True)
            render_resultado(turno["respuesta"])
        st.markdown("<hr>", unsafe_allow_html=True)

    pregunta_chat = st.text_area(
        "Escribe tu pregunta",
        placeholder="Ej: ¿Qué tablas debería usar para calcular el margen por cliente?\n"
                    "Ej: ¿Hay alguna tabla de fechas en el modelo?\n"
                    "Ej: ¿Cómo calcularía las ventas del mes anterior?",
        height=100, label_visibility="collapsed", key="pb_chat_input",
    )

    col_chat_btn, col_chat_hint = st.columns([1, 2])
    with col_chat_btn:
        run_chat = st.button("Enviar", type="primary", key="pb_btn_chat")
    with col_chat_hint:
        st.markdown(
            f'<p class="hint-note">Conversación activa — {len(ss.pb_chat_history)} turnos</p>',
            unsafe_allow_html=True,
        )

    if run_chat:
        if not pregunta_chat.strip():
            st.warning("Escribe una pregunta para continuar.")
        else:
            with st.status("Consultando al modelo...", expanded=True) as status:
                st.write("Analizando el schema del modelo...")
                st.write("Generando respuesta...")
                try:
                    respuesta = chat_con_modelo(pregunta_chat, schema, ss.pb_chat_history)
                    ss.pb_chat_history.append({
                        "pregunta": pregunta_chat.strip(),
                        "respuesta": respuesta,
                    })
                    status.update(label="Respuesta lista", state="complete")
                    st.rerun()
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")

    if ss.pb_chat_history:
        if st.button("Limpiar conversación", type="secondary", key="pb_clear_chat"):
            ss.pb_chat_history = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
