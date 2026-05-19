# ═══════════════════════════════════════════════════════════════════════════════
# CORE/PDF.PY — GENERADOR DE PDF DESDE MARKDOWN
# AnalytiQ AI Suite
#
# Recibe el doc_data con:
#   - "resumen": string de texto plano
#   - "markdown": string markdown completo generado por el LLM
#   - "tablas": lista de dicts (estructura legacy, ignorada si hay markdown)
#
# Convierte el markdown a elementos ReportLab para generar un PDF profesional.
# ═══════════════════════════════════════════════════════════════════════════════

import io
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether, Preformatted,
)

from config.settings import (
    W, H,
    PDF_DARK, PDF_GRAY, PDF_LIGHT, PDF_BORDER, PDF_GREEN, PDF_TEAL, PDF_ACCENT,
)

# ── ESTILOS ───────────────────────────────────────────────────────────────────

def _s(name, **kw):
    return ParagraphStyle(name, **kw)

PDF_ST = {
    "section": _s("section", fontName="Helvetica-Bold", fontSize=7,  textColor=PDF_GRAY,
                  leading=10, spaceBefore=18, spaceAfter=6, letterSpacing=1.5),
    "h2":      _s("h2",      fontName="Helvetica-Bold", fontSize=14, textColor=PDF_DARK,
                  leading=18, spaceBefore=14, spaceAfter=4),
    "h3":      _s("h3",      fontName="Helvetica-Bold", fontSize=11, textColor=PDF_DARK,
                  leading=14, spaceBefore=10, spaceAfter=3),
    "h4":      _s("h4",      fontName="Helvetica-Bold", fontSize=9.5, textColor=PDF_ACCENT,
                  leading=13, spaceBefore=8, spaceAfter=2),
    "body":    _s("body",    fontName="Helvetica",      fontSize=9.5, textColor=PDF_ACCENT,
                  leading=15, spaceAfter=5, alignment=TA_JUSTIFY),
    "bullet":  _s("bullet",  fontName="Helvetica",      fontSize=9,  textColor=PDF_ACCENT,
                  leading=13, leftIndent=12, spaceAfter=2),
    "code":    _s("code",    fontName="Courier",        fontSize=8,
                  textColor=colors.HexColor("#A3E635"), leading=12, spaceAfter=1),
    "code_cm": _s("code_cm", fontName="Courier",        fontSize=8,
                  textColor=colors.HexColor("#6B7280"), leading=12, spaceAfter=1),
}

# ── HELPERS ───────────────────────────────────────────────────────────────────

def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=PDF_BORDER, spaceAfter=8, spaceBefore=4)

def _sp(h=6):
    return Spacer(1, h)

def _body(t):
    # Escapar caracteres especiales de ReportLab
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(t, PDF_ST["body"])

def _h2(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(t.upper(), PDF_ST["section"])

def _h3(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(t, PDF_ST["h3"])

def _h4(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(t, PDF_ST["h4"])

def _bullet(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(f"&bull;&nbsp;&nbsp;{t}", PDF_ST["bullet"])

def _code_block(lines: list):
    content = []
    for line in lines:
        safe = (line.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace('"', "&quot;")
                    .replace(" ", "&nbsp;"))
        if line.strip().startswith("--") or line.strip().startswith("#"):
            content.append(Paragraph(safe, PDF_ST["code_cm"]))
        elif line == "":
            content.append(Paragraph("&nbsp;", PDF_ST["code"]))
        else:
            content.append(Paragraph(safe, PDF_ST["code"]))
    tbl = Table([[content]], colWidths=[W - 50 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), PDF_DARK),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#374151")),
    ]))
    return tbl

def _info_card(text: str, border_color=None):
    if border_color is None:
        border_color = PDF_DARK
    tbl = Table([[Paragraph(text, PDF_ST["body"])]], colWidths=[W - 50 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), PDF_LIGHT),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBEFORE",    (0, 0), (0, -1),  3, border_color),
        ("BOX",           (0, 0), (-1, -1), 0.5, PDF_BORDER),
    ]))
    return tbl


# ── CONVERTIDOR MARKDOWN → FLOWABLES ─────────────────────────────────────────

def markdown_to_flowables(md_text: str) -> list:
    """
    CONVIERTE MARKDOWN A LISTA DE FLOWABLES DE REPORTLAB.
    Soporta: # H1-H4, **negrita**, - listas, ```codigo```, texto plano.
    """
    flowables = []
    lines = md_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Encabezados
        if line.startswith("#### "):
            flowables.append(_h4(line[5:].strip()))
        elif line.startswith("### "):
            flowables.append(_h3(line[4:].strip()))
        elif line.startswith("## "):
            flowables.append(_h2(line[3:].strip()))
        elif line.startswith("# "):
            flowables.append(_h2(line[2:].strip()))

        # Bloque de código
        elif line.strip().startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if code_lines:
                flowables.append(_sp(4))
                flowables.append(_code_block(code_lines))
                flowables.append(_sp(4))

        # Separador horizontal
        elif line.strip() in ("---", "***", "___"):
            flowables.append(_hr())

        # Listas con - o *
        elif re.match(r"^[\-\*]\s+", line):
            text = re.sub(r"^[\-\*]\s+", "", line)
            text = _inline_format(text)
            flowables.append(_bullet(text))

        # Listas numeradas
        elif re.match(r"^\d+\.\s+", line):
            text = re.sub(r"^\d+\.\s+", "", line)
            text = _inline_format(text)
            flowables.append(_bullet(text))

        # Línea en blanco
        elif line.strip() == "":
            flowables.append(_sp(4))

        # Texto normal
        else:
            text = _inline_format(line)
            if text.strip():
                flowables.append(Paragraph(text, PDF_ST["body"]))

        i += 1

    return flowables


def _inline_format(text: str) -> str:
    """Convierte markdown inline (**negrita**, `codigo`) a markup ReportLab."""
    # Escapar primero
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # **negrita**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # *cursiva*
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # `codigo inline`
    text = re.sub(r"`(.+?)`", r'<font name="Courier" size="8">\1</font>', text)
    return text


# ── CALLBACKS DE PÁGINA ───────────────────────────────────────────────────────

def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PDF_DARK)
    canvas.rect(0, H - 13 * mm, W, 13 * mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(colors.white)
    canvas.drawString(20 * mm, H - 8.5 * mm, "ANALYTIQ AI SUITE · DOCUMENTACIÓN DEL MODELO")
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(PDF_GRAY)
    canvas.drawRightString(W - 20 * mm, H - 8.5 * mm, "Generado con IA · GDPR-Safe")
    canvas.setFillColor(PDF_LIGHT)
    canvas.rect(0, 0, W, 9 * mm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(PDF_GRAY)
    canvas.drawCentredString(W / 2, 3 * mm, f"Página {doc.page}")
    canvas.restoreState()


def _make_cover_callback(platform_label: str, model_label: str):
    def _on_cover(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(PDF_DARK)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#111827"))
        canvas.rect(0, H - 75 * mm, W, 75 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.roundRect(20 * mm, H - 50 * mm, 20 * mm, 20 * mm, 4, fill=1, stroke=0)
        canvas.setFillColor(PDF_DARK)
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawCentredString(30 * mm, H - 36 * mm, "◈")
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 32)
        canvas.drawString(20 * mm, H - 85 * mm, "Documentación del Modelo")
        canvas.setFont("Helvetica", 13)
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawString(20 * mm, H - 96 * mm,
                          f"AnalytiQ AI Suite · {platform_label}")
        canvas.setStrokeColor(colors.HexColor("#374151"))
        canvas.setLineWidth(1)
        canvas.line(20 * mm, H - 104 * mm, W - 20 * mm, H - 104 * mm)
        canvas.setFont("Helvetica", 9.5)
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawString(20 * mm, H - 115 * mm,
                          "Este documento describe el propósito de cada tabla y campo del modelo,")
        canvas.drawString(20 * mm, H - 125 * mm,
                          "las relaciones entre tablas y ejemplos generados por IA.")
        canvas.setFillColor(colors.HexColor("#111827"))
        canvas.roundRect(20 * mm, 30 * mm, W - 40 * mm, 28 * mm, 6, fill=1, stroke=0)
        fields = [
            ("Generado por", "AnalytiQ AI Suite · 9Router + Fallback"),
            ("Modelo IA",    model_label),
            ("Privacidad",   "GDPR-Safe · Solo metadatos"),
        ]
        xi, yi = 26 * mm, 53 * mm
        for label, val in fields:
            canvas.setFont("Helvetica-Bold", 7)
            canvas.setFillColor(PDF_GRAY)
            canvas.drawString(xi, yi, label.upper())
            canvas.setFont("Helvetica", 8.5)
            canvas.setFillColor(colors.white)
            canvas.drawString(xi + 28 * mm, yi, val)
            yi -= 7 * mm
        canvas.restoreState()
    return _on_cover


# ── CONSTRUCTOR PRINCIPAL DE PDF ──────────────────────────────────────────────

def build_doc_pdf(doc_data: dict, platform: str = "power_bi") -> bytes:
    """
    CONSTRUYE EL PDF DE DOCUMENTACIÓN COMPLETO.

    Acepta dos formatos de doc_data:
        A) Nuevo (markdown): {"resumen": str, "markdown": str, "n_tablas": int}
        B) Legacy (JSON):    {"resumen": str, "tablas": [{"nombre":..., "descripcion":...}]}

    Args:
        doc_data: Diccionario con los datos de documentación
        platform: Identificador de plataforma para etiquetas del PDF

    Returns:
        bytes: PDF listo para descargar
    """
    # Etiquetas por plataforma
    PLAT_LABELS = {
        "power_bi": ("Power BI",        "Llama 3.3 70B · 9Router · Groq / SambaNova / Gemini", PDF_GREEN),
        "looker":   ("Looker Studio",   "Llama 3.3 70B · 9Router · Gemini 2.0 Flash",          PDF_TEAL),
        "sheets":   ("Google Sheets",   "Llama 3.3 70B · 9Router · Groq / SambaNova / Gemini", PDF_TEAL),
        "excel":    ("Microsoft Excel", "Llama 3.3 70B · 9Router · Groq / SambaNova / Gemini", PDF_GREEN),
    }
    plat_label, model_label, accent_col = PLAT_LABELS.get(
        platform, ("Power BI", "Llama 3.3 70B", PDF_GREEN)
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=25 * mm, rightMargin=25 * mm,
        topMargin=20 * mm,  bottomMargin=16 * mm,
    )
    story = [PageBreak()]

    # ── RESUMEN ───────────────────────────────────────────────────────────────
    resumen = doc_data.get("resumen", "")
    n_tablas = doc_data.get("n_tablas", len(doc_data.get("tablas", [])))

    story += [
        _h2("Resumen del modelo"), _hr(), _sp(4),
        _body(resumen) if resumen else _sp(2),
        _sp(6),
        _info_card(
            f"<b>Tablas documentadas:</b> {n_tablas}  ·  "
            f"<b>Plataforma:</b> {plat_label}  ·  "
            f"<b>Privacidad:</b> GDPR-Safe · Solo metadatos",
            border_color=accent_col,
        ),
        _sp(8), PageBreak(),
    ]

    # ── CONTENIDO PRINCIPAL ───────────────────────────────────────────────────
    # Formato A: markdown directo del LLM
    if doc_data.get("markdown"):
        md_flowables = markdown_to_flowables(doc_data["markdown"])
        story += md_flowables

    # Formato B: legacy JSON con lista de tablas (retrocompatibilidad)
    elif doc_data.get("tablas"):
        for tabla in doc_data["tablas"]:
            # Soporte para tablas que sean strings (resumen en bruto) o dicts
            if isinstance(tabla, str):
                story += [_body(tabla), _sp(6)]
                continue

            nombre = tabla.get("nombre", "")
            desc   = tabla.get("descripcion", "")
            cols   = tabla.get("columnas", [])
            rels   = tabla.get("relaciones", [])
            daxs   = tabla.get("dax_sugeridos", tabla.get("formulas", []))

            section = [_h2(nombre), _hr(), _sp(4)]

            if desc:
                section += [_h3("Descripción"), _body(desc), _sp(6)]

            if cols:
                section += [_h3("Columnas / Campos"), _sp(3)]
                # Columnas pueden ser lista de dicts o lista de strings
                if cols and isinstance(cols[0], dict):
                    col_data = [["Campo", "Propósito"]]
                    for c in cols:
                        col_data.append([
                            Paragraph(str(c.get("nombre", c.get("name", ""))),
                                      _s("cn", fontName="Courier", fontSize=8,
                                         textColor=PDF_DARK, leading=11)),
                            Paragraph(str(c.get("proposito", c.get("purpose", ""))),
                                      PDF_ST["body"]),
                        ])
                else:
                    col_data = [["Campo"]]
                    for c in cols:
                        col_data.append([Paragraph(str(c),
                            _s("cn", fontName="Courier", fontSize=8,
                               textColor=PDF_DARK, leading=11))])

                t = Table(col_data, colWidths=[55 * mm, 105 * mm] if len(col_data[0]) > 1 else [160 * mm])
                t.setStyle(TableStyle([
                    ("BACKGROUND",     (0, 0), (-1,  0), PDF_DARK),
                    ("TEXTCOLOR",      (0, 0), (-1,  0), colors.white),
                    ("FONTNAME",       (0, 0), (-1,  0), "Helvetica-Bold"),
                    ("FONTSIZE",       (0, 0), (-1, -1), 8.5),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PDF_LIGHT]),
                    ("GRID",           (0, 0), (-1, -1), 0.4, PDF_BORDER),
                    ("TOPPADDING",     (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
                    ("LEFTPADDING",    (0, 0), (-1, -1), 8),
                    ("VALIGN",         (0, 0), (-1, -1), "TOP"),
                ]))
                section += [t, _sp(10)]

            if rels:
                section += [_h3("Relaciones"), _sp(3)]
                for r in rels:
                    section.append(_bullet(str(r)))
                section.append(_sp(8))

            if daxs:
                label = "Ejemplos sugeridos"
                section += [_h3(label), _sp(3)]
                for d in daxs:
                    if isinstance(d, dict):
                        nombre_d = d.get("nombre", d.get("name", ""))
                        desc_d   = d.get("descripcion", d.get("description", ""))
                        codigo   = d.get("codigo", d.get("code", ""))
                        section += [
                            Paragraph(f"<b>{nombre_d}</b> — {desc_d}", PDF_ST["bullet"]),
                            _sp(3),
                            _code_block(codigo.split("\n")),
                            _sp(8),
                        ]

            section.append(PageBreak())
            story.append(KeepTogether(section[:4]))
            story += section[4:]

    cover_fn = _make_cover_callback(plat_label, model_label)
    doc.build(story, onFirstPage=cover_fn, onLaterPages=_on_page)
    return buffer.getvalue()
