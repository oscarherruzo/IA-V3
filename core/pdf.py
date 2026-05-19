# GENERACIÓN COMPLETA DE PDF: PORTADA, HELPERS, ESTILOS Y CONSTRUCTOR
# COMPATIBLE CON DOCUMENTACIÓN DE POWER BI (MARKDOWN) Y LOOKER/SHEETS/EXCEL (TABLAS JSON)

import io
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)

from config.settings import (
    W, H,
    PDF_DARK, PDF_GRAY, PDF_LIGHT, PDF_BORDER, PDF_GREEN, PDF_TEAL, PDF_ACCENT,
)


# ── FÁBRICA DE ESTILOS DE PÁRRAFO ─────────────────────────────────────────────

def _s(name, **kw):
    return ParagraphStyle(name, **kw)

PDF_ST = {
    "section": _s("section", fontName="Helvetica-Bold", fontSize=7,  textColor=PDF_GRAY,
                  leading=10, spaceBefore=18, spaceAfter=6, letterSpacing=1.5),
    "h3":      _s("h3",      fontName="Helvetica-Bold", fontSize=12, textColor=PDF_DARK,
                  leading=15, spaceBefore=10, spaceAfter=3),
    "body":    _s("body",    fontName="Helvetica",      fontSize=9.5, textColor=PDF_ACCENT,
                  leading=15, spaceAfter=5, alignment=TA_JUSTIFY),
    "bullet":  _s("bullet",  fontName="Helvetica",      fontSize=9,  textColor=PDF_ACCENT,
                  leading=13, leftIndent=12, spaceAfter=2),
    "code":    _s("code",    fontName="Courier",        fontSize=8,
                  textColor=colors.HexColor("#A3E635"), leading=12, spaceAfter=1),
    "code_cm": _s("code_cm", fontName="Courier",        fontSize=8,
                  textColor=colors.HexColor("#6B7280"), leading=12, spaceAfter=1),
}


# ── HELPERS DE FLUJO ──────────────────────────────────────────────────────────

def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=PDF_BORDER, spaceAfter=8, spaceBefore=4)

def _sp(h=6):
    return Spacer(1, h)

def _body(t):
    return Paragraph(t, PDF_ST["body"])

def _h2(t):
    return Paragraph(t.upper(), PDF_ST["section"])

def _h3(t):
    return Paragraph(t, PDF_ST["h3"])

def _bullet(t):
    return Paragraph(f"&bull;&nbsp;&nbsp;{t}", PDF_ST["bullet"])

def _esc(t):
    return (
        t.replace("&", "&amp;").replace("<", "&lt;")
         .replace(">", "&gt;").replace('"', "&quot;")
         .replace(" ", "&nbsp;")
    )


# ── BLOQUE DE CÓDIGO DAX / LOOKER ─────────────────────────────────────────────

def _code_block(lines: list):
    content = []
    for line in lines:
        safe = _esc(line)
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


def _make_cover_callback(platform_label: str, model_label: str, n_tablas: int):
    def _on_cover(canvas, doc):
        canvas.saveState()
        # Fondo completo oscuro
        canvas.setFillColor(PDF_DARK)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)
        # Banda superior
        canvas.setFillColor(colors.HexColor("#111827"))
        canvas.rect(0, H - 75 * mm, W, 75 * mm, fill=1, stroke=0)
        # Icono
        canvas.setFillColor(colors.white)
        canvas.roundRect(20 * mm, H - 50 * mm, 20 * mm, 20 * mm, 4, fill=1, stroke=0)
        canvas.setFillColor(PDF_DARK)
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawCentredString(30 * mm, H - 36 * mm, "◈")
        # Título
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
        # Info card con n_tablas — en la portada, encima del bloque de metadatos
        canvas.setFillColor(colors.HexColor("#1F2937"))
        canvas.roundRect(20 * mm, 68 * mm, W - 40 * mm, 14 * mm, 4, fill=1, stroke=0)
        canvas.setStrokeColor(PDF_GREEN)
        canvas.setLineWidth(2)
        canvas.line(20 * mm, 68 * mm, 20 * mm, 82 * mm)
        canvas.setFont("Helvetica", 8.5)
        canvas.setFillColor(colors.white)
        canvas.drawString(25 * mm, 77 * mm, f"Tablas documentadas: {n_tablas}")
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.drawString(25 * mm, 71 * mm,
                          "Análisis: Descripción · Columnas · Relaciones  ·  GDPR-Safe · Solo metadatos")
        # Bloque de metadatos inferior
        canvas.setFillColor(colors.HexColor("#111827"))
        canvas.roundRect(20 * mm, 30 * mm, W - 40 * mm, 34 * mm, 6, fill=1, stroke=0)
        fields = [
            ("GENERADO POR", "AnalytiQ AI Suite · 9Router + Fallback"),
            ("MODELO IA",    model_label),
            ("PRIVACIDAD",   "GDPR-Safe · Solo metadatos"),
        ]
        xi, yi = 26 * mm, 59 * mm
        for label, val in fields:
            canvas.setFont("Helvetica-Bold", 7)
            canvas.setFillColor(PDF_GRAY)
            canvas.drawString(xi, yi, label.upper())
            canvas.setFont("Helvetica", 8.5)
            canvas.setFillColor(colors.white)
            canvas.drawString(xi + 28 * mm, yi, val)
            yi -= 9 * mm
        canvas.restoreState()
    return _on_cover


# ══════════════════════════════════════════════════════════════════════════════
# CONVERSOR MARKDOWN → REPORTLAB (PARA POWER BI)
# ══════════════════════════════════════════════════════════════════════════════

def _markdown_to_story(md_text: str) -> list:
    """
    Convierte markdown puro generado por _analyze_batch_md en elementos ReportLab.
    Soporta: ## H2, **negrita**, - bullet, `código inline`, texto normal, --- separador.
    """
    story = []
    lines = md_text.split("\n")

    for line in lines:
        stripped = line.strip()

        # Separador ---
        if re.match(r"^-{3,}$", stripped):
            story.append(_hr())
            story.append(_sp(6))
            continue

        # H2 → título de sección (nombre de tabla)
        if stripped.startswith("## "):
            titulo = stripped[3:].strip()
            story.append(PageBreak())
            story.append(_h2(titulo))
            story.append(_hr())
            story.append(_sp(4))
            continue

        # H3 → subtítulo
        if stripped.startswith("### "):
            story.append(_h3(stripped[4:].strip()))
            story.append(_sp(2))
            continue

        # Bullet: - `Campo` — descripción
        if stripped.startswith("- "):
            content = stripped[2:].strip()
            # Convertir `código` a negrita monoespaciada en XML ReportLab
            content = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", content)
            # Convertir **negrita**
            content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content)
            story.append(_bullet(content))
            continue

        # Líneas **negrita** solas (ej: **Columnas:**)
        if stripped.startswith("**") and stripped.endswith("**"):
            texto = stripped[2:-2]
            story.append(Paragraph(f"<b>{texto}</b>", PDF_ST["h3"]))
            story.append(_sp(2))
            continue

        # Línea vacía → pequeño espacio
        if not stripped:
            story.append(_sp(4))
            continue

        # Texto normal — convertir inline markdown
        content = stripped
        content = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", content)
        content = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", content)
        story.append(_body(content))

    return story


# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUCTOR DE PDF — POWER BI (MARKDOWN) Y OTRAS PLATAFORMAS (JSON)
# ══════════════════════════════════════════════════════════════════════════════

def build_doc_pdf(doc_data: dict, platform: str = "power_bi") -> bytes:
    """
    CONSTRUYE EL PDF DE DOCUMENTACIÓN COMPLETO.

    Para Power BI lee doc_data["markdown"] (string markdown puro).
    Para Looker/Sheets/Excel lee doc_data["tablas"] (lista de dicts JSON).

    Args:
        doc_data: Dict con "markdown" o "tablas" según plataforma
        platform: "power_bi" | "looker" | "sheets" | "excel"

    Returns:
        bytes: PDF listo para descargar
    """
    # ETIQUETAS POR PLATAFORMA
    if platform == "looker":
        plat_label  = "Looker Studio"
        model_label = "Llama 3.3 70B · 9Router · Gemini 2.0 Flash"
        accent_col  = PDF_TEAL
        code_label  = "Expresión"
    elif platform == "sheets":
        plat_label  = "Google Sheets"
        model_label = "Llama 3.3 70B · 9Router · Groq / SambaNova / Gemini"
        accent_col  = PDF_GREEN
        code_label  = "Fórmula"
    elif platform == "excel":
        plat_label  = "Excel"
        model_label = "Llama 3.3 70B · 9Router · Groq / SambaNova / Gemini"
        accent_col  = PDF_GREEN
        code_label  = "Fórmula"
    else:  # power_bi
        plat_label  = "Power BI"
        model_label = "Llama 3.3 70B · 9Router · Groq / SambaNova / Gemini"
        accent_col  = PDF_GREEN
        code_label  = "DAX"

    n_tablas = doc_data.get("n_tablas") or len(doc_data.get("tablas", []))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=25 * mm, rightMargin=25 * mm,
        topMargin=20 * mm,  bottomMargin=16 * mm,
    )
    # El story empieza vacío — la portada es 100% canvas, sin PageBreak inicial
    story = []

    # ── POWER BI: renderizar desde markdown ───────────────────────────────────
    if platform == "power_bi":
        md = doc_data.get("markdown", "")
        if md:
            story += _markdown_to_story(md)

    # ── OTRAS PLATAFORMAS: renderizar desde tablas JSON ───────────────────────
    else:
        for tabla in doc_data.get("tablas", []):
            nombre = tabla.get("nombre", "")
            desc   = tabla.get("descripcion", "")
            cols   = tabla.get("columnas", [])
            rels   = tabla.get("relaciones", [])
            daxs   = tabla.get("dax_sugeridos", [])

            section = [_h2(nombre), _hr(), _sp(4)]

            if desc:
                section += [_h3("Descripción"), _body(desc), _sp(6)]

            if cols:
                section += [_h3("Columnas / Campos"), _sp(3)]
                col_data = [["Campo", "Propósito"]]
                for c in cols:
                    col_data.append([
                        Paragraph(
                            c.get("nombre", ""),
                            _s("cn", fontName="Courier", fontSize=8,
                               textColor=PDF_DARK, leading=11)
                        ),
                        Paragraph(c.get("proposito", ""), PDF_ST["body"]),
                    ])
                t = Table(col_data, colWidths=[55 * mm, 105 * mm])
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
                section += [_h3("Relaciones con otras tablas/fuentes"), _sp(3)]
                for r in rels:
                    section.append(_bullet(r))
                section.append(_sp(8))

            if daxs:
                section += [_h3(f"Ejemplos {code_label} sugeridos"), _sp(3)]
                for d in daxs:
                    section += [
                        Paragraph(
                            f"<b>{d.get('nombre', '')}</b> — {d.get('descripcion', '')}",
                            PDF_ST["bullet"]
                        ),
                        _sp(3),
                        _code_block(d.get("codigo", "").split("\n")),
                        _sp(8),
                    ]

            section.append(PageBreak())
            story.append(KeepTogether(section[:4]))
            story += section[4:]

    cover_fn = _make_cover_callback(plat_label, model_label, n_tablas)
    doc.build(story, onFirstPage=cover_fn, onLaterPages=_on_page)
    return buffer.getvalue()