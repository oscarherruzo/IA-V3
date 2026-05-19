# TABS DE LOOKER STUDIO: GENERAR, VALIDAR, EXPLICAR, EVALUAR Y CHAT
# EQUIVALENTE AL MÓDULO POWER BI PERO ADAPTADO A LOOKER STUDIO

import streamlit as st

from modules.looker.core_functions import (
    generate_looker_expression, generate_campos_recomendados,
    validate_looker_expression, explain_looker_expression,
    evaluate_looker_expression, chat_con_looker,
    generate_campos_base, generate_doc_looker,
)
from core.pdf          import build_doc_pdf
from ui.components.render_helpers import render_resultado, render_validation


# ── INICIALIZACIÓN DE SESSION STATE LOOKER ────────────────────────────────────

def init_looker_state():
    defaults = {
        "lk_historial":           [],
        "lk_chat_history":        [],
        "lk_explain_result":      None,
        "lk_validation_result":   None,
        "lk_eval_result":         None,
        "lk_doc_result":          None,
        "lk_campos_result":       None,
        "lk_recomendados_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── RENDER PRINCIPAL ──────────────────────────────────────────────────────────

def render_tabs_looker(current_schema: dict):
    """RENDERIZA LAS 5 TABS DE LOOKER STUDIO EN LA COLUMNA CENTRAL"""

    tab_gen, tab_val, tab_exp, tab_eval, tab_chat = st.tabs([
        "◈  Generar Expresión",
        "◈  Validar Expresión",
        "◈  Explicar Expresión",
        "◈  Evaluar Expresión",
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


# ── TAB 1: GENERAR EXPRESIÓN ──────────────────────────────────────────────────

def _tab_generar(schema: dict):
    ss = st.session_state
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Solicitud</p>', unsafe_allow_html=True)

    user_query = st.text_area(
        "Describe la lógica que necesitas",
        placeholder="Ej: Categorizar ventas en Alto/Medio/Bajo según importe...",
        height=130, label_visibility="collapsed", key="lk_query_input",
    )

    col_btn1, col_btn2, col_hint = st.columns([1, 1, 1])
    with col_btn1:
        run = st.button("Generar expresión", type="primary", key="lk_btn_generar")
    with col_btn2:
        run_rec = st.button(
            "◈ Campos recomendados", type="secondary", key="lk_btn_recomendados",
            help="Analiza tu schema y sugiere automáticamente los campos calculados más útiles",
        )
    with col_hint:
        st.markdown('<p class="hint-note">9Router · Groq · SambaNova · Gemini fallback</p>',
                    unsafe_allow_html=True)

    if run:
        if user_query and schema:
            with st.status("Generando expresión Looker...", expanded=True) as status:
                st.write("Analizando schema de campos disponibles...")
                st.write("Construyendo expresión Looker Studio...")
                try:
                    result = generate_looker_expression(schema, user_query)
                    status.update(label="Expresión generada", state="complete")
                    ss.lk_historial.insert(0, {"query": user_query, "result": result})
                    st.toast("Expresión lista")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")
        else:
            st.warning("Introduce una solicitud y asegúrate de tener un schema cargado.")

    if run_rec:
        if schema is None or len(schema.get("tables", [])) <= 1:
            st.warning("Carga primero un schema real para obtener recomendaciones.")
        else:
            with st.status("Analizando tu schema...", expanded=True) as status:
                st.write("Detectando métricas y dimensiones...")
                st.write("Identificando campos calculados más útiles...")
                try:
                    recomendados = generate_campos_recomendados(schema)
                    ss.lk_recomendados_result = recomendados
                    status.update(label="Campos recomendados listos", state="complete")
                    st.toast("Recomendaciones generadas")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")

    if ss.lk_recomendados_result:
        st.markdown('<hr class="hr-dark">', unsafe_allow_html=True)
        st.markdown('<p class="card-title">Campos recomendados para tu modelo</p>', unsafe_allow_html=True)
        render_resultado(ss.lk_recomendados_result, code_lang="sql")
        if st.button("Limpiar recomendados", type="secondary", key="lk_clear_rec"):
            ss.lk_recomendados_result = None
            st.rerun()

    # CAMPOS BASE POR FUENTE
    st.markdown('<hr class="hr-dark">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Campos calculados segun el schema</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Selecciona las fuentes que te interesan y el nivel. '
        'La IA genera campos calculados listos para usar en Looker Studio.</p>',
        unsafe_allow_html=True,
    )

    todas_fuentes = [t["name"] for t in schema.get("tables", [])] if schema else []
    fuentes_elegidas = st.multiselect(
        "Selecciona las fuentes", options=todas_fuentes,
        placeholder="Elige una o varias fuentes...", key="lk_campos_fuentes",
    )

    col_nivel, col_gen = st.columns([1, 1])
    with col_nivel:
        nivel = st.selectbox("Nivel", options=["Basicos", "Avanzados", "Ambos"], key="lk_nivel")
    with col_gen:
        st.markdown("<div style='padding-top:28px;'></div>", unsafe_allow_html=True)
        run_campos = st.button("Generar campos", type="primary", key="lk_btn_campos")

    if run_campos:
        if not fuentes_elegidas:
            st.warning("Selecciona al menos una fuente.")
        else:
            n_lotes = max(1, (len(fuentes_elegidas) + 4) // 5)
            with st.status(f"Generando campos para {len(fuentes_elegidas)} fuentes...", expanded=True) as status:
                progress = st.progress(0, text="Iniciando...")
                log_area = st.empty()

                def on_prog(idx, total, nombres):
                    pct = min(int((idx / total) * 95), 95)
                    txt = f"Lote {idx}/{total}: {', '.join(nombres[:3])}..."
                    progress.progress(pct, text=txt)
                    log_area.caption(txt)

                try:
                    campos = generate_campos_base(fuentes_elegidas, nivel, schema, progress_callback=on_prog)
                    progress.progress(100, text="Completado")
                    ss.lk_campos_result = {"campos": campos, "fuentes": fuentes_elegidas, "nivel": nivel}
                    status.update(label=f"{len(campos)} campos generados", state="complete")
                    st.toast("Campos listos")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")

    if ss.lk_campos_result:
        campos_list = ss.lk_campos_result.get("campos", [])
        if campos_list:
            fuentes_con_campos = {}
            for c in campos_list:
                fuente = c.get("tabla", "Sin fuente")
                if fuente not in fuentes_con_campos:
                    fuentes_con_campos[fuente] = []
                fuentes_con_campos[fuente].append(c)

            for fuente, campos_fuente in fuentes_con_campos.items():
                st.markdown(f'<p class="section-label">{fuente}</p>', unsafe_allow_html=True)
                for c in campos_fuente:
                    nivel_val = c.get("nivel", "").lower()
                    badge_cls = "basica" if "basico" in nivel_val else "avanzada"
                    with st.expander(f"{c.get('nombre', '')}"):
                        st.markdown(f'<span class="nivel-badge {badge_cls}">{c.get("nivel","")}</span>',
                                    unsafe_allow_html=True)
                        st.caption(c.get("descripcion", ""))
                        st.code(c.get("codigo", ""), language="sql")

            if st.button("Limpiar campos", type="secondary", key="lk_clear_campos"):
                ss.lk_campos_result = None
                st.rerun()
        else:
            st.warning("La IA no devolvió campos. Intenta con menos fuentes o diferente nivel.")

    st.markdown('</div>', unsafe_allow_html=True)

    if ss.lk_historial:
        st.markdown('<p class="card-title" style="margin:16px 0 12px 0;">Historial</p>',
                    unsafe_allow_html=True)
        for i, item in enumerate(ss.lk_historial):
            num    = len(ss.lk_historial) - i
            titulo = item["query"][:70] + ("..." if len(item["query"]) > 70 else "")
            with st.expander(f"#{num} — {titulo}"):
                render_resultado(item["result"], code_lang="sql")
        if st.button("Limpiar historial", type="secondary", key="lk_clear_historial"):
            ss.lk_historial = []
            st.rerun()


# ── TAB 2: VALIDAR EXPRESIÓN ──────────────────────────────────────────────────

def _tab_validar(schema: dict):
    ss = st.session_state

    if ss.lk_validation_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title" style="margin-bottom:6px;">Código analizado</p>',
                    unsafe_allow_html=True)
        st.code(ss.lk_validation_result["codigo"], language="sql")
        st.markdown('<p class="card-title" style="margin:16px 0 4px 0;">Resultado de la validación</p>',
                    unsafe_allow_html=True)
        render_validation(ss.lk_validation_result)
        if st.button("Limpiar validación", type="secondary", key="lk_clear_validate"):
            ss.lk_validation_result = None
            st.rerun()


    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Validador de Expresiones Looker</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Pega una expresión de campo calculado y la IA la validará '
        'contra tu schema: detecta campos inexistentes, errores de sintaxis y problemas de lógica.</p>',
        unsafe_allow_html=True,
    )

    expr_to_validate = st.text_area(
        "Pega aquí la expresión Looker a validar",
        placeholder="Ej:\nCASE\n  WHEN Ventas > 10000 THEN 'Alto'\n  WHEN Ventas > 5000 THEN 'Medio'\n  ELSE 'Bajo'\nEND",
        height=200, label_visibility="collapsed", key="lk_validate_input",
    )

    col_val_btn, col_val_hint = st.columns([1, 2])
    with col_val_btn:
        run_validate = st.button("Validar expresión", type="primary", key="lk_btn_validate")
    with col_val_hint:
        if schema and len(schema.get("tables", [])) > 1:
            st.markdown('<p class="hint-ok">Schema cargado — validación completa activa</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<p class="hint-warn">Sin schema — solo validación lógica por IA</p>',
                        unsafe_allow_html=True)

    if run_validate:
        if not expr_to_validate.strip():
            st.warning("Pega una expresión para validar.")
        else:
            with st.status("Validando expresión Looker...", expanded=True) as status:
                st.write("Comprobando campos contra el schema...")
                st.write("Analizando sintaxis y lógica con IA...")
                try:
                    validation = validate_looker_expression(expr_to_validate, schema)
                    ss.lk_validation_result = validation
                    estado = validation.get("estado", "INVALIDA")
                    if estado == "VALIDA":
                        status.update(label="Expresión válida", state="complete")
                    elif estado == "VALIDA CON ADVERTENCIAS":
                        status.update(label="Válida con advertencias", state="complete")
                    else:
                        status.update(label="Se encontraron errores", state="error")
                    st.toast("Validación completada")
                except Exception as e:
                    status.update(label="Error en la validación", state="error")
                    st.error(f"Error de API: {e}")


    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 3: EXPLICAR EXPRESIÓN ─────────────────────────────────────────────────

def _tab_explicar(schema: dict):
    ss = st.session_state

    if ss.lk_explain_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title" style="margin-bottom:6px;">Código analizado</p>',
                    unsafe_allow_html=True)
        st.code(ss.lk_explain_result["code"], language="sql")
        st.markdown('<p class="card-title" style="margin:16px 0 8px 0;">Explicación</p>',
                    unsafe_allow_html=True)
        st.markdown(ss.lk_explain_result["explanation"])
        if st.button("Limpiar análisis", type="secondary", key="lk_clear_explain"):
            ss.lk_explain_result = None
            st.rerun()


    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Explicame esta expresión Looker</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Pega cualquier campo calculado de Looker Studio y la IA te lo explicará '
        'parte a parte: qué hace, qué funciones usa, casos de uso y alternativas.</p>',
        unsafe_allow_html=True,
    )

    expr_input = st.text_area(
        "Pega aquí tu expresión Looker",
        placeholder="Ej:\nIF(REGEXP_MATCH(Canal, 'organic'), 'Orgánico', 'Pago')",
        height=200, label_visibility="collapsed", key="lk_explain_input",
    )

    col_exp_btn, col_exp_hint = st.columns([1, 2])
    with col_exp_btn:
        run_explain = st.button("Explicar expresión", type="primary", key="lk_btn_explain")
    with col_exp_hint:
        st.markdown('<p class="hint-note">Funciona con cualquier expresión Looker, aunque no sea de tu modelo actual</p>',
                    unsafe_allow_html=True)

    if run_explain:
        if not expr_input.strip():
            st.warning("Pega una expresión para explicar.")
        else:
            with st.status("Analizando la expresión Looker...", expanded=True) as status:
                st.write("Identificando funciones y estructura...")
                st.write("Generando explicación parte a parte...")
                try:
                    explanation = explain_looker_expression(expr_input, schema)
                    ss.lk_explain_result = {"code": expr_input.strip(), "explanation": explanation}
                    status.update(label="Explicación lista", state="complete")
                    st.toast("Explicación generada")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")


    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 4: EVALUAR + DOCUMENTAR ───────────────────────────────────────────────

def _tab_evaluar(schema: dict):
    ss = st.session_state

    if ss.lk_eval_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title" style="margin-bottom:6px;">Expresión evaluada</p>',
                    unsafe_allow_html=True)
        st.code(ss.lk_eval_result["code"], language="sql")
        st.markdown('<p class="card-title" style="margin:16px 0 8px 0;">Evaluación de negocio</p>',
                    unsafe_allow_html=True)
        render_resultado(ss.lk_eval_result["evaluacion"], code_lang="sql")
        if st.button("Limpiar evaluación", type="secondary", key="lk_clear_eval"):
            ss.lk_eval_result = None
            st.rerun()


    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Evaluador de Expresiones Looker</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Analiza si la lógica de negocio de tu expresión tiene sentido '
        'dado el schema: coherencia con los campos, riesgos de nulos, alternativas más eficientes.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="eval-info">Diferente al validador: no busca errores de sintaxis '
        'sino que evalua si la logica de negocio es correcta y optima para tu modelo.</div>',
        unsafe_allow_html=True,
    )

    expr_to_eval = st.text_area(
        "Pega aquí la expresión Looker a evaluar",
        placeholder="Ej:\nCOALESCE(Ingresos, 0) / COALESCE(Visitas, 1)",
        height=200, label_visibility="collapsed", key="lk_eval_input",
    )

    col_eval_btn, col_eval_hint = st.columns([1, 2])
    with col_eval_btn:
        run_eval = st.button("Evaluar expresión", type="primary", key="lk_btn_eval")
    with col_eval_hint:
        if schema and len(schema.get("tables", [])) > 1:
            st.markdown('<p class="hint-ok">Schema cargado — evaluación completa con contexto del modelo</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<p class="hint-warn">Sin schema — evaluación genérica sin contexto</p>',
                        unsafe_allow_html=True)

    if run_eval:
        if not expr_to_eval.strip():
            st.warning("Pega una expresión para evaluar.")
        else:
            with st.status("Evaluando la lógica de negocio...", expanded=True) as status:
                st.write("Analizando coherencia con el schema...")
                st.write("Evaluando riesgos analíticos...")
                st.write("Buscando alternativas en los campos disponibles...")
                try:
                    evaluacion = evaluate_looker_expression(expr_to_eval, schema)
                    ss.lk_eval_result = {"code": expr_to_eval.strip(), "evaluacion": evaluacion}
                    status.update(label="Evaluación completada", state="complete")
                    st.toast("Evaluación lista")
                except Exception as e:
                    status.update(label="Error en la evaluación", state="error")
                    st.error(f"Error de API: {e}")


    # DOCUMENTAR MODELO LOOKER + PDF
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
                Desde ahí puedes documentar cualquier plataforma con un selector unificado.
            </p>
        </div>
    """, unsafe_allow_html=True)



# ── TAB 5: CHAT CON EL MODELO ─────────────────────────────────────────────────

def _tab_chat(schema: dict):
    ss = st.session_state
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Chat con el modelo</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Pregunta libremente sobre tu schema de Looker Studio: '
        'qué campos usar, cómo calcular una métrica, si una expresión tiene sentido, '
        'o cómo construir un campo calculado desde cero.</p>',
        unsafe_allow_html=True,
    )

    if ss.lk_chat_history:
        for turno in ss.lk_chat_history:
            st.markdown(f"""
            <div class="chat-user-bubble">
                <p class="chat-user-label">Tu pregunta</p>
                <p class="chat-user-text">{turno["pregunta"]}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="chat-ai-bubble">
                <p class="chat-ai-label">Formula Assistant · Looker</p>
            </div>
            """, unsafe_allow_html=True)
            render_resultado(turno["respuesta"], code_lang="sql")
        st.markdown("<hr>", unsafe_allow_html=True)

    pregunta_chat = st.text_area(
        "Escribe tu pregunta",
        placeholder="Ej: ¿Cómo puedo calcular la tasa de conversión con mis campos?\n"
                    "Ej: ¿Hay algún campo de fecha en el schema?\n"
                    "Ej: ¿Cómo filtraría solo los registros del último mes?",
        height=100, label_visibility="collapsed", key="lk_chat_input",
    )

    col_chat_btn, col_chat_hint = st.columns([1, 2])
    with col_chat_btn:
        run_chat = st.button("Enviar", type="primary", key="lk_btn_chat")
    with col_chat_hint:
        st.markdown(
            f'<p class="hint-note">Conversación activa — {len(ss.lk_chat_history)} turnos</p>',
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
                    respuesta = chat_con_looker(pregunta_chat, schema, ss.lk_chat_history)
                    ss.lk_chat_history.append({
                        "pregunta": pregunta_chat.strip(),
                        "respuesta": respuesta,
                    })
                    status.update(label="Respuesta lista", state="complete")
                    st.rerun()
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")

    if ss.lk_chat_history:
        if st.button("Limpiar conversación", type="secondary", key="lk_clear_chat"):
            ss.lk_chat_history = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
