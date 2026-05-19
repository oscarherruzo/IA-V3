# TABS DE GOOGLE SHEETS: GENERAR, VALIDAR, EXPLICAR, EVALUAR Y CHAT

import streamlit as st

from modules.sheets.core_functions import (
    generate_sheets_formula, generate_campos_recomendados,
    validate_sheets_formula, explain_sheets_formula,
    evaluate_sheets_formula, chat_con_sheets,
    generate_formulas_base, generate_doc_sheets,
)
from core.pdf          import build_doc_pdf
from ui.components.render_helpers import render_resultado, render_validation


# ── INICIALIZACIÓN DE SESSION STATE ──────────────────────────────────────────

def init_sheets_state():
    defaults = {
        "gs_historial":           [],
        "gs_chat_history":        [],
        "gs_explain_result":      None,
        "gs_validation_result":   None,
        "gs_eval_result":         None,
        "gs_doc_result":          None,
        "gs_campos_result":       None,
        "gs_recomendados_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── RENDER PRINCIPAL ──────────────────────────────────────────────────────────

def render_tabs_sheets(current_schema: dict):
    """RENDERIZA LAS 5 TABS DE GOOGLE SHEETS EN LA COLUMNA CENTRAL"""

    tab_gen, tab_val, tab_exp, tab_eval, tab_chat = st.tabs([
        "◈  Generar Fórmula",
        "◈  Validar Fórmula",
        "◈  Explicar Fórmula",
        "◈  Evaluar Fórmula",
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


# ── TAB 1: GENERAR FÓRMULA ───────────────────────────────────────────────────

def _tab_generar(schema: dict):
    ss = st.session_state
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Solicitud</p>', unsafe_allow_html=True)

    user_query = st.text_area(
        "Describe la lógica que necesitas",
        placeholder="Ej: Suma de ventas por categoría usando SUMIF...",
        height=130, label_visibility="collapsed", key="gs_query_input",
    )

    col_btn1, col_btn2, col_hint = st.columns([1, 1, 1])
    with col_btn1:
        run = st.button("Generar fórmula", type="primary", key="gs_btn_generar")
    with col_btn2:
        run_rec = st.button(
            "◈ Campos recomendados", type="secondary", key="gs_btn_recomendados",
            help="Analiza tu schema y sugiere automáticamente las fórmulas más útiles",
        )
    with col_hint:
        st.markdown('<p class="hint-note">9Router · Groq · SambaNova · Gemini fallback</p>',
                    unsafe_allow_html=True)

    if run:
        if user_query and schema:
            with st.status("Generando fórmula Google Sheets...", expanded=True) as status:
                st.write("Analizando schema de campos disponibles...")
                st.write("Construyendo fórmula Google Sheets...")
                try:
                    result = generate_sheets_formula(schema, user_query)
                    status.update(label="Fórmula generada", state="complete")
                    ss.gs_historial.insert(0, {"query": user_query, "result": result})
                    st.toast("Fórmula lista")
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
                st.write("Identificando fórmulas más útiles...")
                try:
                    recomendados = generate_campos_recomendados(schema)
                    ss.gs_recomendados_result = recomendados
                    status.update(label="Campos recomendados listos", state="complete")
                    st.toast("Recomendaciones generadas")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")

    if ss.gs_recomendados_result:
        st.markdown('<hr class="hr-dark">', unsafe_allow_html=True)
        st.markdown('<p class="card-title">Fórmulas recomendadas para tu modelo</p>', unsafe_allow_html=True)
        render_resultado(ss.gs_recomendados_result, code_lang="sql")
        if st.button("Limpiar recomendados", type="secondary", key="gs_clear_rec"):
            ss.gs_recomendados_result = None
            st.rerun()

    # CAMPOS BASE POR FUENTE
    st.markdown('<hr class="hr-dark">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Fórmulas según el schema</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Selecciona las fuentes que te interesan y el nivel. '
        'La IA genera fórmulas Sheets listas para usar.</p>',
        unsafe_allow_html=True,
    )

    todas_fuentes = [t["name"] for t in schema.get("tables", [])] if schema else []
    fuentes_elegidas = st.multiselect(
        "Selecciona las fuentes", options=todas_fuentes,
        placeholder="Elige una o varias fuentes...", key="gs_campos_fuentes",
    )

    col_nivel, col_gen = st.columns([1, 1])
    with col_nivel:
        nivel = st.selectbox("Nivel", options=["Basicos", "Avanzados", "Ambos"], key="gs_nivel")
    with col_gen:
        st.markdown("<div style='padding-top:28px;'></div>", unsafe_allow_html=True)
        run_campos = st.button("Generar fórmulas", type="primary", key="gs_btn_campos")

    if run_campos:
        if not fuentes_elegidas:
            st.warning("Selecciona al menos una fuente.")
        else:
            with st.status(f"Generando fórmulas para {len(fuentes_elegidas)} fuentes...", expanded=True) as status:
                progress = st.progress(0, text="Iniciando...")
                log_area = st.empty()

                def on_prog(idx, total, nombres, msg=""):
                    pct = min(int((idx / total) * 95), 95)
                    txt = f"Lote {idx}/{total}: {', '.join(nombres[:3])}..."
                    progress.progress(pct, text=txt)
                    log_area.caption(txt)

                try:
                    campos = generate_formulas_base(fuentes_elegidas, nivel, schema, progress_callback=on_prog)
                    progress.progress(100, text="Completado")
                    ss.gs_campos_result = {"campos": campos, "fuentes": fuentes_elegidas, "nivel": nivel}
                    status.update(label=f"{len(campos)} fórmulas generadas", state="complete")
                    st.toast("Fórmulas listas")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")

    if ss.gs_campos_result:
        campos_list = ss.gs_campos_result.get("campos", [])
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

            if st.button("Limpiar fórmulas", type="secondary", key="gs_clear_campos"):
                ss.gs_campos_result = None
                st.rerun()
        else:
            st.warning("La IA no devolvió fórmulas. Intenta con menos fuentes o diferente nivel.")

    st.markdown('</div>', unsafe_allow_html=True)

    if ss.gs_historial:
        st.markdown('<p class="card-title" style="margin:16px 0 12px 0;">Historial</p>',
                    unsafe_allow_html=True)
        for i, item in enumerate(ss.gs_historial):
            num    = len(ss.gs_historial) - i
            titulo = item["query"][:70] + ("..." if len(item["query"]) > 70 else "")
            with st.expander(f"#{num} — {titulo}"):
                render_resultado(item["result"], code_lang="sql")
        if st.button("Limpiar historial", type="secondary", key="gs_clear_historial"):
            ss.gs_historial = []
            st.rerun()


# ── TAB 2: VALIDAR FÓRMULA ───────────────────────────────────────────────────

def _tab_validar(schema: dict):
    ss = st.session_state

    if ss.gs_validation_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title" style="margin-bottom:6px;">Código analizado</p>',
                    unsafe_allow_html=True)
        st.code(ss.gs_validation_result["codigo"], language="sql")
        st.markdown('<p class="card-title" style="margin:16px 0 4px 0;">Resultado de la validación</p>',
                    unsafe_allow_html=True)
        render_validation(ss.gs_validation_result)
        if st.button("Limpiar validación", type="secondary", key="gs_clear_validate"):
            ss.gs_validation_result = None
            st.rerun()


    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Validador de Fórmulas Google Sheets</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Pega una fórmula y la IA la validará '
        'contra tu schema: detecta referencias inexistentes, errores de sintaxis y problemas de lógica.</p>',
        unsafe_allow_html=True,
    )

    expr_to_validate = st.text_area(
        "Pega aquí la fórmula Sheets a validar",
        placeholder='Ej:\n=SUMIF(Ventas!C:C,"Laptop",Ventas!A:A)',
        height=200, label_visibility="collapsed", key="gs_validate_input",
    )

    col_val_btn, col_val_hint = st.columns([1, 2])
    with col_val_btn:
        run_validate = st.button("Validar fórmula", type="primary", key="gs_btn_validate")
    with col_val_hint:
        if schema and len(schema.get("tables", [])) > 1:
            st.markdown('<p class="hint-ok">Schema cargado — validación completa activa</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<p class="hint-warn">Sin schema — solo validación lógica por IA</p>',
                        unsafe_allow_html=True)

    if run_validate:
        if not expr_to_validate.strip():
            st.warning("Pega una fórmula para validar.")
        else:
            with st.status("Validando fórmula Sheets...", expanded=True) as status:
                st.write("Comprobando campos contra el schema...")
                st.write("Analizando sintaxis y lógica con IA...")
                try:
                    validation = validate_sheets_formula(expr_to_validate, schema)
                    ss.gs_validation_result = validation
                    estado = validation.get("estado", "INVALIDA")
                    if estado == "VALIDA":
                        status.update(label="Fórmula válida", state="complete")
                    elif estado == "VALIDA CON ADVERTENCIAS":
                        status.update(label="Válida con advertencias", state="complete")
                    else:
                        status.update(label="Se encontraron errores", state="error")
                    st.toast("Validación completada")
                except Exception as e:
                    status.update(label="Error en la validación", state="error")
                    st.error(f"Error de API: {e}")


    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 3: EXPLICAR FÓRMULA ──────────────────────────────────────────────────

def _tab_explicar(schema: dict):
    ss = st.session_state

    if ss.gs_explain_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title" style="margin-bottom:6px;">Código analizado</p>',
                    unsafe_allow_html=True)
        st.code(ss.gs_explain_result["code"], language="sql")
        st.markdown('<p class="card-title" style="margin:16px 0 8px 0;">Explicación</p>',
                    unsafe_allow_html=True)
        st.markdown(ss.gs_explain_result["explanation"])
        if st.button("Limpiar análisis", type="secondary", key="gs_clear_explain"):
            ss.gs_explain_result = None
            st.rerun()


    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Explícame esta fórmula Sheets</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Pega cualquier fórmula de Google Sheets y la IA te la explicará '
        'parte a parte: qué hace, qué funciones usa, casos de uso y alternativas.</p>',
        unsafe_allow_html=True,
    )

    expr_input = st.text_area(
        "Pega aquí tu fórmula Sheets",
        placeholder="Ej:\n=ARRAYFORMULA(SUMIF(A:A,D:D,B:B))",
        height=200, label_visibility="collapsed", key="gs_explain_input",
    )

    col_exp_btn, col_exp_hint = st.columns([1, 2])
    with col_exp_btn:
        run_explain = st.button("Explicar fórmula", type="primary", key="gs_btn_explain")
    with col_exp_hint:
        st.markdown('<p class="hint-note">Funciona con cualquier fórmula Sheets, aunque no sea de tu modelo actual</p>',
                    unsafe_allow_html=True)

    if run_explain:
        if not expr_input.strip():
            st.warning("Pega una fórmula para explicar.")
        else:
            with st.status("Analizando la fórmula Sheets...", expanded=True) as status:
                st.write("Identificando funciones y estructura...")
                st.write("Generando explicación parte a parte...")
                try:
                    explanation = explain_sheets_formula(expr_input, schema)
                    ss.gs_explain_result = {"code": expr_input.strip(), "explanation": explanation}
                    status.update(label="Explicación lista", state="complete")
                    st.toast("Explicación generada")
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")


    st.markdown('</div>', unsafe_allow_html=True)


# ── TAB 4: EVALUAR + DOCUMENTAR ─────────────────────────────────────────────

def _tab_evaluar(schema: dict):
    ss = st.session_state

    if ss.gs_eval_result:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<p class="card-title" style="margin-bottom:6px;">Fórmula evaluada</p>',
                    unsafe_allow_html=True)
        st.code(ss.gs_eval_result["code"], language="sql")
        st.markdown('<p class="card-title" style="margin:16px 0 8px 0;">Evaluación de negocio</p>',
                    unsafe_allow_html=True)
        render_resultado(ss.gs_eval_result["evaluacion"], code_lang="sql")
        if st.button("Limpiar evaluación", type="secondary", key="gs_clear_eval"):
            ss.gs_eval_result = None
            st.rerun()


    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Evaluador de Fórmulas Google Sheets</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Analiza si la lógica de negocio de tu fórmula tiene sentido '
        'dado el schema: coherencia con los campos, riesgos de nulos, alternativas más eficientes.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="eval-info">Diferente al validador: no busca errores de sintaxis '
        'sino que evalúa si la lógica de negocio es correcta y óptima para tu modelo.</div>',
        unsafe_allow_html=True,
    )

    expr_to_eval = st.text_area(
        "Pega aquí la fórmula Sheets a evaluar",
        placeholder="Ej:\n=IFERROR(SUMIF(A:A,G1,B:B)/COUNTIF(A:A,G1),0)",
        height=200, label_visibility="collapsed", key="gs_eval_input",
    )

    col_eval_btn, col_eval_hint = st.columns([1, 2])
    with col_eval_btn:
        run_eval = st.button("Evaluar fórmula", type="primary", key="gs_btn_eval")
    with col_eval_hint:
        if schema and len(schema.get("tables", [])) > 1:
            st.markdown('<p class="hint-ok">Schema cargado — evaluación completa con contexto del modelo</p>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<p class="hint-warn">Sin schema — evaluación genérica sin contexto</p>',
                        unsafe_allow_html=True)

    if run_eval:
        if not expr_to_eval.strip():
            st.warning("Pega una fórmula para evaluar.")
        else:
            with st.status("Evaluando la lógica de negocio...", expanded=True) as status:
                st.write("Analizando coherencia con el schema...")
                st.write("Evaluando riesgos analíticos...")
                st.write("Buscando alternativas en los campos disponibles...")
                try:
                    evaluacion = evaluate_sheets_formula(expr_to_eval, schema)
                    ss.gs_eval_result = {"code": expr_to_eval.strip(), "evaluacion": evaluacion}
                    status.update(label="Evaluación completada", state="complete")
                    st.toast("Evaluación lista")
                except Exception as e:
                    status.update(label="Error en la evaluación", state="error")
                    st.error(f"Error de API: {e}")


    # DOCUMENTAR MODELO SHEETS + PDF
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



# ── TAB 5: CHAT CON EL MODELO ────────────────────────────────────────────────

def _tab_chat(schema: dict):
    ss = st.session_state
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<p class="card-title">Chat con el modelo</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hint-text">Pregunta libremente sobre tu schema de Google Sheets: '
        'qué campos usar, cómo calcular una métrica, si una fórmula tiene sentido, '
        'o cómo construir una fórmula desde cero.</p>',
        unsafe_allow_html=True,
    )

    if ss.gs_chat_history:
        for turno in ss.gs_chat_history:
            st.markdown(f"""
            <div class="chat-user-bubble">
                <p class="chat-user-label">Tu pregunta</p>
                <p class="chat-user-text">{turno["pregunta"]}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("""
            <div class="chat-ai-bubble">
                <p class="chat-ai-label">Formula Assistant · Google Sheets</p>
            </div>
            """, unsafe_allow_html=True)
            render_resultado(turno["respuesta"], code_lang="sql")
        st.markdown("<hr>", unsafe_allow_html=True)

    pregunta_chat = st.text_area(
        "Escribe tu pregunta",
        placeholder="Ej: ¿Cómo puedo calcular la tasa de conversión con mis campos?\n"
                    "Ej: ¿Hay algún campo de fecha en el schema?\n"
                    "Ej: ¿Cómo filtraría solo los registros del último mes?",
        height=100, label_visibility="collapsed", key="gs_chat_input",
    )

    col_chat_btn, col_chat_hint = st.columns([1, 2])
    with col_chat_btn:
        run_chat = st.button("Enviar", type="primary", key="gs_btn_chat")
    with col_chat_hint:
        st.markdown(
            f'<p class="hint-note">Conversación activa — {len(ss.gs_chat_history)} turnos</p>',
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
                    respuesta = chat_con_sheets(pregunta_chat, schema, ss.gs_chat_history)
                    ss.gs_chat_history.append({
                        "pregunta": pregunta_chat.strip(),
                        "respuesta": respuesta,
                    })
                    status.update(label="Respuesta lista", state="complete")
                    st.rerun()
                except Exception as e:
                    status.update(label="Error", state="error")
                    st.error(f"Error de API: {e}")

    if ss.gs_chat_history:
        if st.button("Limpiar conversación", type="secondary", key="gs_clear_chat"):
            ss.gs_chat_history = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)