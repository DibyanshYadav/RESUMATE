"""Render a structured resume dict to downloadable PDF and DOCX bytes."""
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from docx import Document
from docx.shared import Pt, Inches
import io


def _safe(text):
    """fpdf's core fonts don't support all unicode; replace unsupported chars."""
    if not text:
        return ""
    return text.encode("latin-1", "replace").decode("latin-1")


def build_pdf(data: dict) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Name
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, _safe(data.get("name", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Contact
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 5, _safe(data.get("contact", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    def section_title(title):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_draw_color(150, 150, 150)
        pdf.cell(0, 8, _safe(title.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y())
        pdf.ln(2)

    # Summary
    if data.get("summary"):
        section_title("Summary")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _safe(data["summary"]), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    # Skills
    if data.get("skills"):
        section_title("Skills")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _safe(", ".join(data["skills"])), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    # Experience
    if data.get("experience"):
        section_title("Experience")
        for job in data["experience"]:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, _safe(f"{job.get('title','')} — {job.get('company','')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 5, _safe(job.get("dates", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 10)
            for bullet in job.get("bullets", []):
                pdf.multi_cell(0, 5, _safe(f"- {bullet}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)

    # Projects
    if data.get("projects"):
        section_title("Projects")
        for proj in data["projects"]:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 6, _safe(proj.get("name", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 10)
            if proj.get("description"):
                pdf.multi_cell(0, 5, _safe(proj["description"]), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            for bullet in proj.get("bullets", []):
                pdf.multi_cell(0, 5, _safe(f"- {bullet}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)

    # Education
    if data.get("education"):
        section_title("Education")
        for edu in data["education"]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, _safe(edu.get("degree", "")), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 5, _safe(f"{edu.get('institution','')} | {edu.get('dates','')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

    return bytes(pdf.output(dest="S"))


def build_docx(data: dict) -> bytes:
    doc = Document()

    name = doc.add_heading(data.get("name", ""), level=0)

    contact_p = doc.add_paragraph(data.get("contact", ""))
    contact_p.runs[0].font.size = Pt(10) if contact_p.runs else None

    def add_section(title):
        h = doc.add_heading(title.upper(), level=2)
        return h

    if data.get("summary"):
        add_section("Summary")
        doc.add_paragraph(data["summary"])

    if data.get("skills"):
        add_section("Skills")
        doc.add_paragraph(", ".join(data["skills"]))

    if data.get("experience"):
        add_section("Experience")
        for job in data["experience"]:
            p = doc.add_paragraph()
            run = p.add_run(f"{job.get('title','')} — {job.get('company','')}")
            run.bold = True
            date_p = doc.add_paragraph(job.get("dates", ""))
            date_p.runs[0].italic = True
            for bullet in job.get("bullets", []):
                doc.add_paragraph(bullet, style="List Bullet")

    if data.get("projects"):
        add_section("Projects")
        for proj in data["projects"]:
            p = doc.add_paragraph()
            run = p.add_run(proj.get("name", ""))
            run.bold = True
            if proj.get("description"):
                doc.add_paragraph(proj["description"])
            for bullet in proj.get("bullets", []):
                doc.add_paragraph(bullet, style="List Bullet")

    if data.get("education"):
        add_section("Education")
        for edu in data["education"]:
            p = doc.add_paragraph()
            run = p.add_run(edu.get("degree", ""))
            run.bold = True
            doc.add_paragraph(f"{edu.get('institution','')} | {edu.get('dates','')}")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()