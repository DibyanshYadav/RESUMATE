"""
Export a structured resume dict to PDF and DOCX, in one of three templates:
    modern   - single column, blue accent, sans-serif, skill "pill" tags
    classic  - centered header, serif, black & white, traditional/ATS-safe
    compact  - two-column layout with a teal sidebar for skills + education

Data schema (same shape used by preview.py):
{
    "name": str,
    "contact": str,
    "summary": str,
    "skills": [str, ...],
    "experience": [{"title": str, "company": str, "dates": str, "bullets": [str, ...]}, ...],
    "projects": [{"name": str, "description": str, "bullets": [str, ...]}, ...],
    "education": [{"degree": str, "institution": str, "dates": str}, ...],
}

Public API:
    build_pdf(data: dict, template: str = "modern") -> bytes
    build_docx(data: dict, template: str = "modern") -> bytes
"""

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, ListFlowable, ListItem
)

from docx import Document
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ---------------------------------------------------------------------------
# Shared palette (mirrors preview.py's CSS variables)
# ---------------------------------------------------------------------------

MODERN = {
    "accent": colors.HexColor("#2F5EFF"),
    "accent_bg": colors.HexColor("#EEF2FF"),
    "text": colors.HexColor("#111827"),
    "sub": colors.HexColor("#6B7280"),
    "muted": colors.HexColor("#9CA3AF"),
    "body": colors.HexColor("#374151"),
    "border": colors.HexColor("#E5E7EB"),
}
CLASSIC = {
    "text": colors.HexColor("#141414"),
    "sub": colors.HexColor("#555555"),
    "line": colors.HexColor("#999999"),
    "body": colors.HexColor("#222222"),
}
COMPACT = {
    "accent": colors.HexColor("#0D9488"),
    "sidebar_bg": colors.HexColor("#F0F9F8"),
    "text": colors.HexColor("#111827"),
    "sub": colors.HexColor("#6B7280"),
    "muted": colors.HexColor("#9CA3AF"),
    "body": colors.HexColor("#374151"),
    "border": colors.HexColor("#E5E7EB"),
}

PAGE_MARGIN = 0.65 * inch


def _get(d, *keys, default=""):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
    return cur if cur is not None else default


# ===========================================================================
# PDF (reportlab)
# ===========================================================================

def build_pdf(data: dict, template: str = "modern") -> bytes:
    template = (template or "modern").lower()
    if template in ("classic", "minimal"):
        return _pdf_classic(data)
    if template == "compact":
        return _pdf_compact(data)
    return _pdf_modern(data)


def _pdf_doc(buf):
    return SimpleDocTemplate(
        buf, pagesize=LETTER,
        leftMargin=PAGE_MARGIN, rightMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN, bottomMargin=PAGE_MARGIN,
    )


def _pill_rows(skills, pal, content_width, font="Helvetica", size=9, pad_x=8, pad_y=5, gap=5):
    """Pack skill pills into rows of single-row Tables so they visually wrap like CSS chips."""
    rows, current, current_w = [], [], 0.0
    for s in skills:
        w = stringWidth(s, font, size) + pad_x * 2
        if current and current_w + gap + w > content_width:
            rows.append(current)
            current, current_w = [], 0.0
        current.append((s, w))
        current_w += w + gap
    if current:
        rows.append(current)

    flow = []
    for row in rows:
        widths = [w for _, w in row]
        cells = [s for s, _ in row]
        t = Table([cells], colWidths=widths, hAlign="LEFT")
        style = [
            ("BACKGROUND", (0, 0), (-1, -1), pal["accent_bg"]),
            ("TEXTCOLOR", (0, 0), (-1, -1), pal["accent"]),
            ("FONTNAME", (0, 0), (-1, -1), font),
            ("FONTSIZE", (0, 0), (-1, -1), size),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), pad_y),
            ("BOTTOMPADDING", (0, 0), (-1, -1), pad_y),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), gap),
            ("LINEBELOW", (0, 0), (-1, -1), 0, colors.white),
        ]
        try:
            style.append(("ROUNDEDCORNERS", [8, 8, 8, 8]))
        except Exception:
            pass
        t.setStyle(TableStyle(style))
        flow.append(t)
        flow.append(Spacer(1, 4))
    return flow


def _pdf_modern(data: dict) -> bytes:
    pal = MODERN
    buf = io.BytesIO()
    doc = _pdf_doc(buf)
    content_width = doc.width

    styles = {
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=22, textColor=pal["text"], leading=26),
        "contact": ParagraphStyle("contact", fontName="Helvetica", fontSize=9.5, textColor=pal["sub"], leading=13, spaceBefore=2),
        "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=10, textColor=pal["accent"], leading=14, spaceBefore=12, spaceAfter=6, letterSpacing=0.6) ,
        "summary": ParagraphStyle("summary", fontName="Helvetica", fontSize=10, textColor=pal["body"], leading=14.5),
        "entry_title": ParagraphStyle("entry_title", fontName="Helvetica-Bold", fontSize=10.5, textColor=pal["text"], leading=14),
        "entry_dates": ParagraphStyle("entry_dates", fontName="Helvetica", fontSize=9, textColor=pal["muted"], leading=13, alignment=2),
        "entry_sub": ParagraphStyle("entry_sub", fontName="Helvetica-Oblique", fontSize=9.5, textColor=pal["sub"], leading=13, spaceAfter=2),
        "bullet": ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5, textColor=pal["body"], leading=13.5, leftIndent=12),
    }

    story = []
    story.append(Paragraph(_get(data, "name", default="Your Name"), styles["name"]))
    contact = _get(data, "contact")
    if contact:
        story.append(Paragraph(contact, styles["contact"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.6, color=pal["accent"], spaceAfter=2))

    summary = _get(data, "summary")
    if summary:
        story.append(Paragraph("SUMMARY", styles["section"]))
        story.append(Paragraph(summary, styles["summary"]))

    skills = data.get("skills") or []
    if skills:
        story.append(Paragraph("SKILLS", styles["section"]))
        story.extend(_pill_rows(skills, pal, content_width))

    experience = data.get("experience") or []
    if experience:
        story.append(Paragraph("EXPERIENCE", styles["section"]))
        for job in experience:
            title = f'{_get(job, "title")} — {_get(job, "company")}'.strip(" —")
            row = Table([[Paragraph(title, styles["entry_title"]), Paragraph(_get(job, "dates"), styles["entry_dates"])]],
                        colWidths=[content_width * 0.72, content_width * 0.28])
            row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                      ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                      ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
            story.append(row)
            bullets = job.get("bullets") or []
            if bullets:
                story.append(ListFlowable(
                    [ListItem(Paragraph(b, styles["bullet"]), leftIndent=12) for b in bullets],
                    bulletType="bullet", start="•", leftIndent=14, bulletFontSize=9,
                ))
            story.append(Spacer(1, 8))

    projects = data.get("projects") or []
    if projects:
        story.append(Paragraph("PROJECTS", styles["section"]))
        for proj in projects:
            story.append(Paragraph(_get(proj, "name"), styles["entry_title"]))
            desc = _get(proj, "description")
            if desc:
                story.append(Paragraph(desc, styles["entry_sub"]))
            bullets = proj.get("bullets") or []
            if bullets:
                story.append(ListFlowable(
                    [ListItem(Paragraph(b, styles["bullet"]), leftIndent=12) for b in bullets],
                    bulletType="bullet", start="•", leftIndent=14, bulletFontSize=9,
                ))
            story.append(Spacer(1, 8))

    education = data.get("education") or []
    if education:
        story.append(Paragraph("EDUCATION", styles["section"]))
        for edu in education:
            row = Table([[Paragraph(_get(edu, "degree"), styles["entry_title"]), Paragraph(_get(edu, "dates"), styles["entry_dates"])]],
                        colWidths=[content_width * 0.72, content_width * 0.28])
            row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                      ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                      ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
            story.append(row)
            story.append(Paragraph(_get(edu, "institution"), styles["entry_sub"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    return buf.getvalue()


def _pdf_classic(data: dict) -> bytes:
    pal = CLASSIC
    buf = io.BytesIO()
    doc = _pdf_doc(buf)
    content_width = doc.width
    serif, serif_b, serif_i = "Times-Roman", "Times-Bold", "Times-Italic"

    styles = {
        "name": ParagraphStyle("name", fontName=serif_b, fontSize=20, textColor=pal["text"], leading=24, alignment=TA_CENTER),
        "contact": ParagraphStyle("contact", fontName=serif, fontSize=9.5, textColor=pal["sub"], leading=13, alignment=TA_CENTER, spaceBefore=3),
        "section": ParagraphStyle("section", fontName=serif_b, fontSize=10, textColor=pal["text"], leading=14, spaceBefore=12, spaceAfter=5),
        "summary": ParagraphStyle("summary", fontName=serif, fontSize=10, textColor=pal["body"], leading=14.5),
        "entry_title": ParagraphStyle("entry_title", fontName=serif_b, fontSize=10.5, textColor=pal["text"], leading=14),
        "entry_dates": ParagraphStyle("entry_dates", fontName=serif_i, fontSize=9, textColor=pal["sub"], leading=13, alignment=2),
        "entry_sub": ParagraphStyle("entry_sub", fontName=serif, fontSize=9.5, textColor=pal["sub"], leading=13, spaceAfter=2),
        "bullet": ParagraphStyle("bullet", fontName=serif, fontSize=9.5, textColor=pal["body"], leading=13.5, leftIndent=12),
    }

    story = [Paragraph(_get(data, "name", default="Your Name"), styles["name"])]
    contact = _get(data, "contact")
    if contact:
        story.append(Paragraph(contact, styles["contact"]))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.2, color=pal["text"], spaceAfter=2))

    def section_title(text):
        story.append(Paragraph(text.upper(), styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.6, color=pal["line"], spaceAfter=5))

    summary = _get(data, "summary")
    if summary:
        section_title("Summary")
        story.append(Paragraph(summary, styles["summary"]))

    skills = data.get("skills") or []
    if skills:
        section_title("Skills")
        story.append(Paragraph(", ".join(skills), styles["summary"]))

    experience = data.get("experience") or []
    if experience:
        section_title("Experience")
        for job in experience:
            title = f'{_get(job, "title")}, {_get(job, "company")}'.strip(", ")
            row = Table([[Paragraph(title, styles["entry_title"]), Paragraph(_get(job, "dates"), styles["entry_dates"])]],
                        colWidths=[content_width * 0.72, content_width * 0.28])
            row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                      ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                      ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
            story.append(row)
            bullets = job.get("bullets") or []
            if bullets:
                story.append(ListFlowable(
                    [ListItem(Paragraph(b, styles["bullet"]), leftIndent=12) for b in bullets],
                    bulletType="bullet", start="•", leftIndent=14, bulletFontSize=9,
                ))
            story.append(Spacer(1, 8))

    projects = data.get("projects") or []
    if projects:
        section_title("Projects")
        for proj in projects:
            story.append(Paragraph(_get(proj, "name"), styles["entry_title"]))
            desc = _get(proj, "description")
            if desc:
                story.append(Paragraph(desc, styles["entry_sub"]))
            bullets = proj.get("bullets") or []
            if bullets:
                story.append(ListFlowable(
                    [ListItem(Paragraph(b, styles["bullet"]), leftIndent=12) for b in bullets],
                    bulletType="bullet", start="•", leftIndent=14, bulletFontSize=9,
                ))
            story.append(Spacer(1, 8))

    education = data.get("education") or []
    if education:
        section_title("Education")
        for edu in education:
            row = Table([[Paragraph(_get(edu, "degree"), styles["entry_title"]), Paragraph(_get(edu, "dates"), styles["entry_dates"])]],
                        colWidths=[content_width * 0.72, content_width * 0.28])
            row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                      ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                      ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
            story.append(row)
            story.append(Paragraph(_get(edu, "institution"), styles["entry_sub"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    return buf.getvalue()


def _pdf_compact(data: dict) -> bytes:
    pal = COMPACT
    buf = io.BytesIO()
    doc = _pdf_doc(buf)
    sidebar_w = doc.width * 0.34
    main_w = doc.width * 0.66 - 14

    s_name = ParagraphStyle("s_name", fontName="Helvetica-Bold", fontSize=15, textColor=pal["accent"], leading=18)
    s_contact = ParagraphStyle("s_contact", fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#4B5563"), leading=12, spaceBefore=4, spaceAfter=10)
    s_side_title = ParagraphStyle("s_side_title", fontName="Helvetica-Bold", fontSize=9, textColor=pal["accent"], leading=12, spaceBefore=10, spaceAfter=4)
    s_side_item = ParagraphStyle("s_side_item", fontName="Helvetica", fontSize=9, textColor=pal["body"], leading=13, leftIndent=10)
    s_side_edu_title = ParagraphStyle("s_side_edu_title", fontName="Helvetica-Bold", fontSize=9, textColor=pal["text"], leading=12)
    s_side_edu_sub = ParagraphStyle("s_side_edu_sub", fontName="Helvetica", fontSize=8, textColor=pal["sub"], leading=11)
    s_main_title = ParagraphStyle("s_main_title", fontName="Helvetica-Bold", fontSize=10, textColor=pal["accent"], leading=13, spaceBefore=10, spaceAfter=6)
    s_summary = ParagraphStyle("s_summary", fontName="Helvetica", fontSize=9.5, textColor=pal["body"], leading=13.5)
    s_entry_title = ParagraphStyle("s_entry_title", fontName="Helvetica-Bold", fontSize=10, textColor=pal["text"], leading=13)
    s_entry_dates = ParagraphStyle("s_entry_dates", fontName="Helvetica", fontSize=8.5, textColor=pal["muted"], leading=12, alignment=2)
    s_entry_sub = ParagraphStyle("s_entry_sub", fontName="Helvetica-Oblique", fontSize=9, textColor=pal["sub"], leading=12, spaceAfter=2)
    s_bullet = ParagraphStyle("s_bullet", fontName="Helvetica", fontSize=9, textColor=pal["body"], leading=13, leftIndent=10)

    # --- sidebar flow ---
    side = [Paragraph(_get(data, "name", default="Your Name"), s_name)]
    contact = _get(data, "contact")
    if contact:
        side.append(Paragraph(contact, s_contact))
    skills = data.get("skills") or []
    if skills:
        side.append(Paragraph("SKILLS", s_side_title))
        side.append(ListFlowable(
            [ListItem(Paragraph(s, s_side_item), leftIndent=10) for s in skills],
            bulletType="bullet", start="•", leftIndent=10, bulletFontSize=8,
        ))
    education = data.get("education") or []
    if education:
        side.append(Paragraph("EDUCATION", s_side_title))
        for edu in education:
            side.append(Paragraph(_get(edu, "degree"), s_side_edu_title))
            side.append(Paragraph(_get(edu, "institution"), s_side_edu_sub))
            side.append(Paragraph(_get(edu, "dates"), s_side_edu_sub))
            side.append(Spacer(1, 6))

    # --- main flow ---
    main = []
    summary = _get(data, "summary")
    if summary:
        main.append(Paragraph("SUMMARY", s_main_title))
        main.append(Paragraph(summary, s_summary))

    experience = data.get("experience") or []
    if experience:
        main.append(Paragraph("EXPERIENCE", s_main_title))
        for job in experience:
            title = f'{_get(job, "title")} — {_get(job, "company")}'.strip(" —")
            row = Table([[Paragraph(title, s_entry_title), Paragraph(_get(job, "dates"), s_entry_dates)]],
                        colWidths=[main_w * 0.68, main_w * 0.32])
            row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                      ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                                      ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
            main.append(row)
            bullets = job.get("bullets") or []
            if bullets:
                main.append(ListFlowable(
                    [ListItem(Paragraph(b, s_bullet), leftIndent=10) for b in bullets],
                    bulletType="bullet", start="•", leftIndent=12, bulletFontSize=8,
                ))
            main.append(Spacer(1, 8))

    projects = data.get("projects") or []
    if projects:
        main.append(Paragraph("PROJECTS", s_main_title))
        for proj in projects:
            main.append(Paragraph(_get(proj, "name"), s_entry_title))
            desc = _get(proj, "description")
            if desc:
                main.append(Paragraph(desc, s_entry_sub))
            bullets = proj.get("bullets") or []
            if bullets:
                main.append(ListFlowable(
                    [ListItem(Paragraph(b, s_bullet), leftIndent=10) for b in bullets],
                    bulletType="bullet", start="•", leftIndent=12, bulletFontSize=8,
                ))
            main.append(Spacer(1, 8))

    outer = Table([[side, main]], colWidths=[sidebar_w, main_w + 14])
    outer.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), pal["sidebar_bg"]),
        ("LEFTPADDING", (0, 0), (0, 0), 10), ("RIGHTPADDING", (0, 0), (0, 0), 10),
        ("TOPPADDING", (0, 0), (0, 0), 14), ("BOTTOMPADDING", (0, 0), (0, 0), 14),
        ("LEFTPADDING", (1, 0), (1, 0), 14), ("RIGHTPADDING", (1, 0), (1, 0), 0),
        ("TOPPADDING", (1, 0), (1, 0), 14), ("BOTTOMPADDING", (1, 0), (1, 0), 14),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.75, pal["border"]),
    ]))

    doc.build([outer])
    return buf.getvalue()


# ===========================================================================
# DOCX (python-docx)
# ===========================================================================

def build_docx(data: dict, template: str = "modern") -> bytes:
    template = (template or "modern").lower()
    if template in ("classic", "minimal"):
        return _docx_classic(data)
    if template == "compact":
        return _docx_compact(data)
    return _docx_modern(data)


def _set_cell_shading(cell, hex_color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color.lstrip("#"))
    cell._tc.get_or_add_tcPr().append(shd)


def _set_cell_borders_none(cell):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        borders.append(el)
    tcPr.append(borders)


def _add_bottom_border(paragraph, color="2F5EFF", size=18):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def _docx_margins(doc, inches=0.65):
    for section in doc.sections:
        section.top_margin = Inches(inches)
        section.bottom_margin = Inches(inches)
        section.left_margin = Inches(inches)
        section.right_margin = Inches(inches)


def _run(p, text, bold=False, italic=False, size=10, color=None, font=None, allcaps=False):
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor.from_string(color.lstrip("#"))
    if font:
        r.font.name = font
    if allcaps:
        r.font.all_caps = True
    return r


def _add_bullets(doc, items, size=9.5, color="374151", font=None, indent=0.25):
    for b in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Inches(indent)
        p.paragraph_format.space_after = Pt(2)
        _run(p, b, size=size, color=color, font=font)


def _title_dates_row(container, title, dates, total_width_in, title_color="111827",
                      dates_color="9CA3AF", font=None, size=10.5, dates_size=9, italic_dates=False):
    """Borderless 2-col table for a 'Title ........ Dates' row that never wraps unexpectedly."""
    t = container.add_table(rows=1, cols=2)
    t.autofit = False
    left_w, right_w = total_width_in * 0.7, total_width_in * 0.3
    for col, w in zip(t.columns, (left_w, right_w)):
        col.width = Inches(w)
    cells = t.rows[0].cells
    cells[0].width = Inches(left_w)
    cells[1].width = Inches(right_w)
    for c in cells:
        _set_cell_borders_none(c)
        c.vertical_alignment = WD_ALIGN_VERTICAL.BOTTOM
        tcPr = c._tc.get_or_add_tcPr()
        mar = OxmlElement("w:tcMar")
        for edge, val in (("top", "0"), ("bottom", "0"), ("left", "0"), ("right", "0")):
            el = OxmlElement(f"w:{edge}")
            el.set(qn("w:w"), val)
            el.set(qn("w:type"), "dxa")
            mar.append(el)
        tcPr.append(mar)
    p0 = cells[0].paragraphs[0]
    p0.paragraph_format.space_after = Pt(0)
    _run(p0, title, bold=True, size=size, color=title_color, font=font)
    p1 = cells[1].paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p1.paragraph_format.space_after = Pt(0)
    if dates:
        _run(p1, dates, italic=italic_dates, size=dates_size, color=dates_color, font=font)
    return t


def _docx_modern(data: dict) -> bytes:
    doc = Document()
    _docx_margins(doc)
    FONT = "Calibri"
    ACCENT, TEXT, SUB, MUTED, BODY = "2F5EFF", "111827", "6B7280", "9CA3AF", "374151"

    p = doc.add_paragraph()
    _run(p, _get(data, "name", default="Your Name"), bold=True, size=22, color=TEXT, font=FONT)
    p.paragraph_format.space_after = Pt(2)

    contact = _get(data, "contact")
    if contact:
        p = doc.add_paragraph()
        _run(p, contact, size=9.5, color=SUB, font=FONT)
        p.paragraph_format.space_after = Pt(4)

    hr = doc.add_paragraph()
    hr.paragraph_format.space_after = Pt(8)
    _add_bottom_border(hr, color=ACCENT, size=18)

    def section(title):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        _run(h, title.upper(), bold=True, size=10, color=ACCENT, font=FONT)

    summary = _get(data, "summary")
    if summary:
        section("Summary")
        p = doc.add_paragraph()
        _run(p, summary, size=10, color=BODY, font=FONT)

    skills = data.get("skills") or []
    if skills:
        section("Skills")
        chunk = 4
        for i in range(0, len(skills), chunk):
            row_skills = skills[i:i + chunk]
            t = doc.add_table(rows=1, cols=len(row_skills))
            t.autofit = True
            for cell, s in zip(t.rows[0].cells, row_skills):
                _set_cell_shading(cell, "EEF2FF")
                _set_cell_borders_none(cell)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                cp = cell.paragraphs[0]
                cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                _run(cp, s, size=9, color=ACCENT, bold=True, font=FONT)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

    experience = data.get("experience") or []
    if experience:
        section("Experience")
        for job in experience:
            title = f'{_get(job, "title")} — {_get(job, "company")}'.strip(" —")
            _title_dates_row(doc, title, _get(job, "dates"), 7.2, title_color=TEXT, dates_color=MUTED, font=FONT)
            _add_bullets(doc, job.get("bullets") or [], color=BODY, font=FONT)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

    projects = data.get("projects") or []
    if projects:
        section("Projects")
        for proj in projects:
            p = doc.add_paragraph()
            _run(p, _get(proj, "name"), bold=True, size=10.5, color=TEXT, font=FONT)
            desc = _get(proj, "description")
            if desc:
                p = doc.add_paragraph()
                _run(p, desc, italic=True, size=9.5, color=SUB, font=FONT)
            _add_bullets(doc, proj.get("bullets") or [], color=BODY, font=FONT)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

    education = data.get("education") or []
    if education:
        section("Education")
        for edu in education:
            _title_dates_row(doc, _get(edu, "degree"), _get(edu, "dates"), 7.2, title_color=TEXT, dates_color=MUTED, font=FONT)
            p = doc.add_paragraph()
            _run(p, _get(edu, "institution"), italic=True, size=9.5, color=SUB, font=FONT)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _docx_classic(data: dict) -> bytes:
    doc = Document()
    _docx_margins(doc)
    FONT = "Georgia"
    TEXT, SUB, LINE, BODY = "141414", "555555", "999999", "222222"

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p, _get(data, "name", default="Your Name"), bold=True, size=20, color=TEXT, font=FONT)
    p.paragraph_format.space_after = Pt(2)

    contact = _get(data, "contact")
    if contact:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _run(p, contact, size=9.5, color=SUB, font=FONT)

    hr = doc.add_paragraph()
    hr.paragraph_format.space_before = Pt(6)
    hr.paragraph_format.space_after = Pt(8)
    _add_bottom_border(hr, color=TEXT, size=14)

    def section(title):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)
        _run(h, title.upper(), bold=True, size=10, color=TEXT, font=FONT)
        _add_bottom_border(h, color=LINE, size=6)

    summary = _get(data, "summary")
    if summary:
        section("Summary")
        p = doc.add_paragraph()
        _run(p, summary, size=10, color=BODY, font=FONT)

    skills = data.get("skills") or []
    if skills:
        section("Skills")
        p = doc.add_paragraph()
        _run(p, ", ".join(skills), size=10, color=BODY, font=FONT)

    experience = data.get("experience") or []
    if experience:
        section("Experience")
        for job in experience:
            title = f'{_get(job, "title")}, {_get(job, "company")}'.strip(", ")
            _title_dates_row(doc, title, _get(job, "dates"), 7.2, title_color=TEXT, dates_color=SUB, font=FONT, italic_dates=True)
            _add_bullets(doc, job.get("bullets") or [], color=BODY, font=FONT)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

    projects = data.get("projects") or []
    if projects:
        section("Projects")
        for proj in projects:
            p = doc.add_paragraph()
            _run(p, _get(proj, "name"), bold=True, size=10.5, color=TEXT, font=FONT)
            desc = _get(proj, "description")
            if desc:
                p = doc.add_paragraph()
                _run(p, desc, size=9.5, color=SUB, font=FONT)
            _add_bullets(doc, proj.get("bullets") or [], color=BODY, font=FONT)
            doc.add_paragraph().paragraph_format.space_after = Pt(2)

    education = data.get("education") or []
    if education:
        section("Education")
        for edu in education:
            _title_dates_row(doc, _get(edu, "degree"), _get(edu, "dates"), 7.2, title_color=TEXT, dates_color=SUB, font=FONT, italic_dates=True)
            p = doc.add_paragraph()
            _run(p, _get(edu, "institution"), size=9.5, color=SUB, font=FONT)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _zero_cell_margins(cell, left=100, right=100, top=100, bottom=100):
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for edge, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcPr.append(mar)


def _docx_compact(data: dict) -> bytes:
    doc = Document()
    _docx_margins(doc, inches=0.55)
    FONT = "Calibri"
    ACCENT, SIDEBAR_BG, TEXT, SUB, MUTED, BODY = "0D9488", "F0F9F8", "111827", "6B7280", "9CA3AF", "374151"
    # usable width = 8.5in page - 2*0.55in margins = 7.4in
    SIDE_W, MAIN_W = 2.3, 4.9

    # Kill the default table style so Word doesn't add its own borders/spacing/indent.
    outer = doc.add_table(rows=1, cols=2)
    outer.style = None
    outer.autofit = False
    outer.allow_autofit = False
    tbl = outer._tbl
    tblPr = tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    side_cell, main_cell = outer.rows[0].cells
    side_cell.width = Inches(SIDE_W)
    main_cell.width = Inches(MAIN_W)
    _set_cell_shading(side_cell, SIDEBAR_BG)
    _set_cell_borders_none(side_cell)
    _set_cell_borders_none(main_cell)
    _zero_cell_margins(side_cell, left=180, right=180, top=200, bottom=200)
    _zero_cell_margins(main_cell, left=200, right=0, top=200, bottom=200)
    side_cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    main_cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

    # clear default empty paragraphs' spacing
    def clear(cell):
        cell.paragraphs[0].text = ""
        return cell.paragraphs[0]

    # --- sidebar ---
    p = clear(side_cell)
    _run(p, _get(data, "name", default="Your Name"), bold=True, size=15, color=ACCENT, font=FONT)
    contact = _get(data, "contact")
    if contact:
        p = side_cell.add_paragraph()
        _run(p, contact, size=8.5, color="4B5563", font=FONT)
        p.paragraph_format.space_after = Pt(8)

    skills = data.get("skills") or []
    if skills:
        h = side_cell.add_paragraph()
        h.paragraph_format.space_before = Pt(8)
        _run(h, "SKILLS", bold=True, size=9, color=ACCENT, font=FONT)
        for s in skills:
            sp = side_cell.add_paragraph(style="List Bullet")
            sp.paragraph_format.space_after = Pt(1)
            _run(sp, s, size=9, color=BODY, font=FONT)

    education = data.get("education") or []
    if education:
        h = side_cell.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        _run(h, "EDUCATION", bold=True, size=9, color=ACCENT, font=FONT)
        for edu in education:
            p = side_cell.add_paragraph()
            p.paragraph_format.space_before = Pt(4)
            _run(p, _get(edu, "degree"), bold=True, size=9, color=TEXT, font=FONT)
            p2 = side_cell.add_paragraph()
            _run(p2, _get(edu, "institution"), size=8, color=SUB, font=FONT)
            p3 = side_cell.add_paragraph()
            _run(p3, _get(edu, "dates"), size=8, color=SUB, font=FONT)

    # --- main ---
    main_first = clear(main_cell)

    def main_section(title, first=False):
        target = main_first if first else main_cell.add_paragraph()
        target.paragraph_format.space_before = Pt(0 if first else 10)
        target.paragraph_format.space_after = Pt(4)
        _run(target, title.upper(), bold=True, size=10, color=ACCENT, font=FONT)

    first_used = False
    summary = _get(data, "summary")
    if summary:
        main_section("Summary", first=True)
        first_used = True
        p = main_cell.add_paragraph()
        _run(p, summary, size=9.5, color=BODY, font=FONT)

    experience = data.get("experience") or []
    if experience:
        main_section("Experience", first=not first_used)
        first_used = True
        for job in experience:
            title = f'{_get(job, "title")} — {_get(job, "company")}'.strip(" —")
            p = main_cell.add_paragraph()
            p.paragraph_format.space_after = Pt(0)
            _run(p, title, bold=True, size=10, color=TEXT, font=FONT)
            dates = _get(job, "dates")
            if dates:
                _run(p, "   " + dates, size=8.5, color=MUTED, font=FONT)
            for b in job.get("bullets") or []:
                bp = main_cell.add_paragraph(style="List Bullet")
                bp.paragraph_format.space_after = Pt(1)
                _run(bp, b, size=9, color=BODY, font=FONT)
            main_cell.add_paragraph().paragraph_format.space_after = Pt(2)

    projects = data.get("projects") or []
    if projects:
        main_section("Projects", first=not first_used)
        first_used = True
        for proj in projects:
            p = main_cell.add_paragraph()
            _run(p, _get(proj, "name"), bold=True, size=10, color=TEXT, font=FONT)
            desc = _get(proj, "description")
            if desc:
                dp = main_cell.add_paragraph()
                _run(dp, desc, italic=True, size=9, color=SUB, font=FONT)
            for b in proj.get("bullets") or []:
                bp = main_cell.add_paragraph(style="List Bullet")
                bp.paragraph_format.space_after = Pt(1)
                _run(bp, b, size=9, color=BODY, font=FONT)
            main_cell.add_paragraph().paragraph_format.space_after = Pt(2)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Metadata mirror (kept identical to preview.py so app.py can import from either)
# ---------------------------------------------------------------------------
TEMPLATE_META = {
    "modern": {"label": "Modern", "description": "Single column, blue accent, sans-serif."},
    "classic": {"label": "Classic", "description": "Centered header, serif type, black & white — traditional/ATS-safe."},
    "compact": {"label": "Compact", "description": "Two-column with a teal sidebar for skills and education."},
    "minimal": {"label": "Minimal", "description": "Ultra-clean single column, black & white, no color accents."},
}