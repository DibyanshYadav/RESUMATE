import html
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from resume_parser import extract_text_from_pdf
from tailor import tailor_resume
from exporter import build_pdf, build_docx


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Resumate — JD-Tailored Resume Builder",
    page_icon="📄",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Template metadata
# ---------------------------------------------------------------------------
TEMPLATE_META = {
    "modern": {
        "label": "Modern",
        "description": "Single column, blue accent, sans-serif.",
    },
    "classic": {
        "label": "Classic",
        "description": "Centered header, serif type, black & white — traditional/ATS-safe.",
    },
    "compact": {
        "label": "Compact",
        "description": "Two-column with a teal sidebar for skills and education.",
    },
}


# ---------------------------------------------------------------------------
# Theme (light / dark)
# ---------------------------------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

LIGHT_THEME = {
    "accent": "#2F5EFF",
    "accent_hover": "#244ED1",
    "accent_light": "#EEF2FF",
    "panel": "#F6F7FB",
    "card": "#FFFFFF",
    "text": "#111827",
    "sub": "#6B7280",
    "muted": "#9CA3AF",
    "border": "#E5E7EB",
    "input_bg": "#FFFFFF",
    "shadow": "rgba(17, 24, 39, 0.06)",
}

DARK_THEME = {
    "accent": "#6E8CFF",
    "accent_hover": "#8AA2FF",
    "accent_light": "rgba(110, 140, 255, 0.14)",
    "panel": "#0B0D12",
    "card": "#161A22",
    "text": "#F3F4F6",
    "sub": "#9CA3AF",
    "muted": "#6B7280",
    "border": "#262B36",
    "input_bg": "#1B1F29",
    "shadow": "rgba(0, 0, 0, 0.35)",
}

THEME = DARK_THEME if st.session_state.dark_mode else LIGHT_THEME


# ---------------------------------------------------------------------------
# Resume preview CSS
# ---------------------------------------------------------------------------
PREVIEW_CSS = """
<style>
.resume-preview {
    background: white;
    color: #1f2937;
    width: 100%;
    min-height: 850px;
    padding: 42px;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(17, 24, 39, 0.08);
    box-sizing: border-box;
    line-height: 1.5;
}

.resume-preview * {
    box-sizing: border-box;
}

.resume-preview h1,
.resume-preview h2,
.resume-preview h3,
.resume-preview p {
    margin-top: 0;
}

.resume-modern {
    font-family: Arial, Helvetica, sans-serif;
}

.resume-modern .resume-name {
    color: #2F5EFF;
    font-size: 30px;
    font-weight: 700;
    margin-bottom: 5px;
}

.resume-modern .resume-contact {
    color: #6b7280;
    font-size: 13px;
    margin-bottom: 24px;
}

.resume-modern .section-title {
    color: #2F5EFF;
    font-size: 15px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 2px solid #2F5EFF;
    padding-bottom: 5px;
    margin-top: 22px;
    margin-bottom: 12px;
}

.resume-modern .skills-list span {
    display: inline-block;
    background: #EEF2FF;
    color: #244ED1;
    padding: 5px 9px;
    border-radius: 999px;
    font-size: 12px;
    margin: 0 6px 7px 0;
}


/* ------------------------------------------------------------------------ */
/* Classic template */
/* ------------------------------------------------------------------------ */

.resume-classic {
    font-family: Georgia, "Times New Roman", serif;
    color: #222;
}

.resume-classic .resume-header {
    text-align: center;
    border-bottom: 1px solid #222;
    padding-bottom: 14px;
    margin-bottom: 18px;
}

.resume-classic .resume-name {
    font-size: 30px;
    font-weight: 700;
    margin-bottom: 6px;
}

.resume-classic .resume-contact {
    font-size: 13px;
}

.resume-classic .section-title {
    font-size: 15px;
    font-weight: 700;
    text-transform: uppercase;
    border-bottom: 1px solid #555;
    padding-bottom: 4px;
    margin-top: 22px;
    margin-bottom: 10px;
}


/* ------------------------------------------------------------------------ */
/* Compact template */
/* ------------------------------------------------------------------------ */

.resume-compact {
    font-family: Arial, Helvetica, sans-serif;
    display: grid;
    grid-template-columns: 32% 68%;
    padding: 0;
    overflow: hidden;
}

.resume-compact .compact-sidebar {
    background: #F0F9F8;
    padding: 30px 22px;
    border-right: 1px solid #CCFBF1;
}

.resume-compact .compact-main {
    padding: 30px 28px;
}

.resume-compact .resume-name {
    font-size: 27px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 7px;
}

.resume-compact .resume-contact {
    color: #6b7280;
    font-size: 12px;
    word-break: break-word;
}

.resume-compact .section-title {
    color: #0D9488;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 2px solid #0D9488;
    padding-bottom: 5px;
    margin-top: 20px;
    margin-bottom: 10px;
}

.resume-compact .compact-sidebar .section-title {
    margin-top: 0;
}

.resume-compact .compact-sidebar .sidebar-section {
    margin-bottom: 28px;
}


/* ------------------------------------------------------------------------ */
/* Shared resume elements */
/* ------------------------------------------------------------------------ */

.resume-preview .summary {
    font-size: 13px;
    color: #374151;
}

.resume-preview .item {
    margin-bottom: 16px;
}

.resume-preview .item-header {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: flex-start;
}

.resume-preview .item-title {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
}

.resume-preview .item-subtitle {
    font-size: 13px;
    color: #6b7280;
    margin-top: 2px;
}

.resume-preview .item-date {
    font-size: 12px;
    color: #6b7280;
    white-space: nowrap;
}

.resume-preview ul {
    margin: 7px 0 0 0;
    padding-left: 19px;
}

.resume-preview li {
    font-size: 12.5px;
    color: #374151;
    margin-bottom: 4px;
}

.resume-preview .skill-list {
    padding-left: 18px;
}

.resume-preview .skill-list li {
    margin-bottom: 6px;
}

.resume-preview .education-item {
    margin-bottom: 14px;
}

.resume-preview .education-degree {
    font-size: 13px;
    font-weight: 700;
}

.resume-preview .education-institution,
.resume-preview .education-dates {
    font-size: 12px;
    color: #6b7280;
}

@media (max-width: 800px) {
    .resume-compact {
        grid-template-columns: 1fr;
    }

    .resume-compact .compact-sidebar {
        border-right: none;
        border-bottom: 1px solid #CCFBF1;
    }
}
</style>
"""


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def safe(value):
    """Escape text before inserting it into HTML."""
    return html.escape(str(value or ""))


def render_experience(experience):
    if not experience:
        return ""

    items = []

    for job in experience:
        title = safe(job.get("title", ""))
        company = safe(job.get("company", ""))
        dates = safe(job.get("dates", ""))
        bullets = job.get("bullets", []) or []

        header_left = title
        if company:
            header_left += f" — {company}"

        bullets_html = ""
        if bullets:
            bullets_html = "<ul>"
            for bullet in bullets:
                bullets_html += f"<li>{safe(bullet)}</li>"
            bullets_html += "</ul>"

        items.append(
            f"""
            <div class="item">
                <div class="item-header">
                    <div>
                        <div class="item-title">{header_left}</div>
                    </div>
                    <div class="item-date">{dates}</div>
                </div>
                {bullets_html}
            </div>
            """
        )

    return "".join(items)


def render_projects(projects):
    if not projects:
        return ""

    items = []

    for project in projects:
        name = safe(project.get("name", ""))
        description = safe(project.get("description", ""))
        bullets = project.get("bullets", []) or []

        bullets_html = ""
        if bullets:
            bullets_html = "<ul>"
            for bullet in bullets:
                bullets_html += f"<li>{safe(bullet)}</li>"
            bullets_html += "</ul>"

        description_html = ""
        if description:
            description_html = (
                f'<div class="item-subtitle">{description}</div>'
            )

        items.append(
            f"""
            <div class="item">
                <div class="item-title">{name}</div>
                {description_html}
                {bullets_html}
            </div>
            """
        )

    return "".join(items)


def render_education(education):
    if not education:
        return ""

    items = []

    for edu in education:
        degree = safe(edu.get("degree", ""))
        institution = safe(edu.get("institution", ""))
        dates = safe(edu.get("dates", ""))

        items.append(
            f"""
            <div class="education-item">
                <div class="education-degree">{degree}</div>
                <div class="education-institution">{institution}</div>
                <div class="education-dates">{dates}</div>
            </div>
            """
        )

    return "".join(items)


def render_skills_pills(skills):
    if not skills:
        return ""

    return "".join(
        f"<span>{safe(skill)}</span>"
        for skill in skills
    )


def render_skills_list(skills):
    if not skills:
        return ""

    skills_html = '<ul class="skill-list">'

    for skill in skills:
        skills_html += f"<li>{safe(skill)}</li>"

    skills_html += "</ul>"

    return skills_html


def render_section(title, content):
    if not content:
        return ""

    return f"""
        <div class="section-title">{safe(title)}</div>
        {content}
    """


# ---------------------------------------------------------------------------
# Live preview renderer
# ---------------------------------------------------------------------------
def render_preview_html(data, template="modern"):
    name = safe(data.get("name", "Your Name"))
    contact = safe(data.get("contact", ""))
    summary = safe(data.get("summary", ""))

    skills = data.get("skills", []) or []
    experience = data.get("experience", []) or []
    projects = data.get("projects", []) or []
    education = data.get("education", []) or []

    experience_html = render_experience(experience)
    projects_html = render_projects(projects)
    education_html = render_education(education)

    summary_html = ""
    if summary:
        summary_html = render_section(
            "Summary",
            f'<div class="summary">{summary}</div>'
        )

    if template == "classic":
        skills_html = render_skills_list(skills)

        return f"""
        <div class="resume-preview resume-classic">
            <div class="resume-header">
                <div class="resume-name">{name}</div>
                <div class="resume-contact">{contact}</div>
            </div>

            {summary_html}
            {render_section("Skills", skills_html)}
            {render_section("Experience", experience_html)}
            {render_section("Projects", projects_html)}
            {render_section("Education", education_html)}
        </div>
        """

    if template == "compact":
        skills_html = render_skills_list(skills)

        sidebar_html = f"""
            <div class="compact-sidebar">
                <div class="resume-name">{name}</div>
                <div class="resume-contact">{contact}</div>

                <div class="sidebar-section">
                    {render_section("Skills", skills_html)}
                </div>

                <div class="sidebar-section">
                    {render_section("Education", education_html)}
                </div>
            </div>
        """

        main_html = f"""
            <div class="compact-main">
                {summary_html}
                {render_section("Experience", experience_html)}
                {render_section("Projects", projects_html)}
            </div>
        """

        return f"""
        <div class="resume-preview resume-compact">
            {sidebar_html}
            {main_html}
        </div>
        """

    # Default: Modern
    skills_html = f'<div class="skills-list">{render_skills_pills(skills)}</div>'

    return f"""
    <div class="resume-preview resume-modern">
        <div class="resume-name">{name}</div>
        <div class="resume-contact">{contact}</div>

        {summary_html}
        {render_section("Skills", skills_html)}
        {render_section("Experience", experience_html)}
        {render_section("Projects", projects_html)}
        {render_section("Education", education_html)}
    </div>
    """


# ---------------------------------------------------------------------------
# Global styling — Enhancv-style light SaaS look, theme-aware
# ---------------------------------------------------------------------------
st.html(
    f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

    {PREVIEW_CSS}

    <style>
    :root {{
        --accent: {THEME["accent"]};
        --accent-hover: {THEME["accent_hover"]};
        --accent-light: {THEME["accent_light"]};
        --panel: {THEME["panel"]};
        --card: {THEME["card"]};
        --text: {THEME["text"]};
        --sub: {THEME["sub"]};
        --muted: {THEME["muted"]};
        --border: {THEME["border"]};
        --input-bg: {THEME["input_bg"]};
        --shadow: {THEME["shadow"]};
    }}

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: var(--text);
    }}

    .stApp {{
        background: var(--panel);
    }}

    #MainMenu, footer, header[data-testid="stHeader"] {{
        background: transparent;
    }}

    .block-container {{
        padding-top: 1.2rem;
        max-width: 1280px;
    }}

    /* ---- Top navbar ---- */
    .rm-navbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.9rem 0.25rem 1.1rem 0.25rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.75rem;
    }}

    .rm-navbar-brand {{
        font-family: 'Poppins', sans-serif;
        font-weight: 800;
        font-size: 1.35rem;
        color: var(--text);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .rm-navbar-brand span.dot {{
        color: var(--accent);
    }}

    div[data-testid="stCheckbox"] label,
    div[data-testid="stToggle"] label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: var(--sub);
    }}

    /* ---- Hero header ---- */
    .rm-hero {{
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
        border-radius: 18px;
        padding: 2.4rem 2.6rem;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 12px 34px var(--shadow);
    }}

    .rm-hero h1 {{
        font-family: 'Poppins', sans-serif;
        font-weight: 800;
        font-size: 2.1rem;
        margin: 0 0 0.5rem 0;
        color: white;
        letter-spacing: -0.01em;
    }}

    .rm-hero p {{
        font-size: 1rem;
        margin: 0;
        opacity: 0.92;
        max-width: 640px;
        line-height: 1.5;
    }}

    /* ---- Section headers ---- */
    .rm-section-label {{
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 1.05rem;
        color: var(--text);
        margin: 0 0 0.9rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    /* ---- Cards ---- */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: var(--card);
        border-radius: 16px !important;
        border: 1px solid var(--border) !important;
        box-shadow: 0 2px 16px var(--shadow);
    }}

    /* ---- Buttons ---- */
    .stButton > button,
    .stDownloadButton > button {{
        border-radius: 10px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        padding: 0.6rem 1.3rem;
        border: none;
        transition: transform 0.08s ease, box-shadow 0.15s ease;
    }}

    .stButton > button[kind="primary"],
    .stDownloadButton > button {{
        background: var(--accent);
        color: white;
        box-shadow: 0 4px 14px var(--shadow);
    }}

    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button:hover {{
        background: var(--accent-hover);
        transform: translateY(-1px);
        box-shadow: 0 6px 18px var(--shadow);
    }}

    .stButton > button:disabled {{
        background: var(--border);
        color: var(--muted);
        box-shadow: none;
    }}

    /* ---- Inputs ---- */
    .stTextInput input,
    .stTextArea textarea {{
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
        font-family: 'Inter', sans-serif;
        background: var(--input-bg) !important;
        color: var(--text) !important;
    }}

    .stTextInput input:focus,
    .stTextArea textarea:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 1px var(--accent) !important;
    }}

    /* ---- File uploader ---- */
    [data-testid="stFileUploaderDropzone"] {{
        background: var(--accent-light) !important;
        border: 1.5px dashed var(--accent) !important;
        border-radius: 12px !important;
    }}

    /* ---- Template picker ---- */
    div[data-testid="stRadio"] > div {{
        flex-direction: row;
        gap: 0.6rem;
        flex-wrap: wrap;
    }}

    div[data-testid="stRadio"] label {{
        background: var(--card);
        border: 1.5px solid var(--border);
        border-radius: 10px;
        padding: 0.55rem 1rem !important;
        margin: 0 !important;
        cursor: pointer;
        transition: all 0.12s ease;
    }}

    div[data-testid="stRadio"] label:hover {{
        border-color: var(--accent);
    }}

    /* ---- Sticky preview panel ---- */
    .rm-preview-shell {{
        position: sticky;
        top: 1.2rem;
        background: var(--panel);
    }}

    .rm-preview-label {{
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.03em;
        color: var(--sub);
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }}

    hr {{
        border-color: var(--border) !important;
    }}

    [data-testid="stExpander"] {{
        border-radius: 10px !important;
        border: 1px solid var(--border) !important;
        background: var(--card) !important;
    }}

    .stAlert {{
        border-radius: 10px;
    }}
    </style>
    """
)


# ---------------------------------------------------------------------------
# Top navbar + theme toggle
# ---------------------------------------------------------------------------
nav_left, nav_right = st.columns([0.82, 0.18])

with nav_left:
    st.markdown(
        '<div class="rm-navbar-brand">📄 Resumate<span class="dot">.</span></div>',
        unsafe_allow_html=True,
    )

with nav_right:
    st.toggle("🌙 Dark mode", key="dark_mode")


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "resume_data" not in st.session_state:
    st.session_state.resume_data = None

if "raw_resume_text" not in st.session_state:
    st.session_state.raw_resume_text = ""

if "template" not in st.session_state:
    st.session_state.template = "modern"


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="rm-hero">
        <h1>Tailor your resume to any job, instantly</h1>
        <p>
            Upload your resume, paste a job description, and get a tailored
            version — edit it live, then export in the template you like.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Step 1: Inputs
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown(
            '<div class="rm-section-label">📤 Your resume</div>',
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Upload your resume (PDF)",
            type=["pdf"],
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            try:
                st.session_state.raw_resume_text = extract_text_from_pdf(
                    uploaded_file
                )

                with st.expander("Preview extracted resume text"):
                    st.text_area(
                        "Extracted text",
                        st.session_state.raw_resume_text,
                        height=200,
                        disabled=True,
                        label_visibility="collapsed",
                    )

            except Exception as e:
                st.error(f"Failed to read the resume PDF: {e}")


with col2:
    with st.container(border=True):
        st.markdown(
            '<div class="rm-section-label">🎯 Job description</div>',
            unsafe_allow_html=True,
        )

        job_description = st.text_area(
            "Paste the job description",
            height=232,
            label_visibility="collapsed",
            placeholder="Paste the full job description here…",
        )


st.write("")

_, btn_col, _ = st.columns([1, 1, 1])

with btn_col:
    generate = st.button(
        "✨ Tailor my resume",
        type="primary",
        use_container_width=True,
        disabled=not (
            st.session_state.raw_resume_text
            and job_description
        ),
    )


if generate:
    with st.spinner("Tailoring your resume against the JD..."):
        try:
            st.session_state.resume_data = tailor_resume(
                st.session_state.raw_resume_text,
                job_description,
            )

        except Exception as e:
            st.error(f"Failed to generate tailored resume: {e}")


st.write("")


# ---------------------------------------------------------------------------
# Step 2: Edit + live preview
# ---------------------------------------------------------------------------
data = st.session_state.resume_data

if data:
    edit_col, preview_col = st.columns(
        [0.52, 0.48],
        gap="large",
    )

    # -----------------------------------------------------------------------
    # Editor
    # -----------------------------------------------------------------------
    with edit_col:

        # Template selector
        with st.container(border=True):
            st.markdown(
                '<div class="rm-section-label">🎨 Template</div>',
                unsafe_allow_html=True,
            )

            template_keys = list(TEMPLATE_META.keys())

            # Safety check in case session state contains an invalid template.
            if st.session_state.template not in template_keys:
                st.session_state.template = "modern"

            st.session_state.template = st.radio(
                "Template",
                options=template_keys,
                format_func=lambda key: TEMPLATE_META[key]["label"],
                index=template_keys.index(
                    st.session_state.template
                ),
                horizontal=True,
                label_visibility="collapsed",
            )

            st.caption(
                TEMPLATE_META[
                    st.session_state.template
                ]["description"]
            )


        # Resume editor
        with st.container(border=True):
            st.markdown(
                '<div class="rm-section-label">✏️ Edit your tailored resume</div>',
                unsafe_allow_html=True,
            )

            data["name"] = st.text_input(
                "Name",
                data.get("name", ""),
            )

            data["contact"] = st.text_input(
                "Contact info",
                data.get("contact", ""),
            )

            data["summary"] = st.text_area(
                "Summary",
                data.get("summary", ""),
                height=100,
            )


            # Skills
            skills_str = st.text_area(
                "Skills (comma-separated)",
                ", ".join(data.get("skills", [])),
                height=70,
            )

            data["skills"] = [
                skill.strip()
                for skill in skills_str.split(",")
                if skill.strip()
            ]


            # Experience
            st.markdown("**Experience**")

            for i, job in enumerate(
                data.get("experience", [])
            ):
                title = job.get("title", "")
                company = job.get("company", "")

                exp_title = (
                    f"{title} — {company}"
                    if title or company
                    else f"Experience {i + 1}"
                )

                with st.expander(
                    exp_title,
                    expanded=False,
                ):
                    job["title"] = st.text_input(
                        "Title",
                        job.get("title", ""),
                        key=f"exp_title_{i}",
                    )

                    job["company"] = st.text_input(
                        "Company",
                        job.get("company", ""),
                        key=f"exp_company_{i}",
                    )

                    job["dates"] = st.text_input(
                        "Dates",
                        job.get("dates", ""),
                        key=f"exp_dates_{i}",
                    )

                    bullets_str = st.text_area(
                        "Bullets (one per line)",
                        "\n".join(
                            job.get("bullets", [])
                        ),
                        key=f"exp_bullets_{i}",
                        height=120,
                    )

                    job["bullets"] = [
                        bullet.strip("- ").strip()
                        for bullet in bullets_str.split("\n")
                        if bullet.strip()
                    ]


            # Projects
            if data.get("projects"):
                st.markdown("**Projects**")

                for i, project in enumerate(
                    data["projects"]
                ):
                    with st.expander(
                        project.get(
                            "name",
                            f"Project {i + 1}",
                        )
                    ):
                        project["name"] = st.text_input(
                            "Project name",
                            project.get("name", ""),
                            key=f"proj_name_{i}",
                        )

                        project["description"] = st.text_area(
                            "Description",
                            project.get(
                                "description",
                                "",
                            ),
                            key=f"proj_desc_{i}",
                        )

                        bullets_str = st.text_area(
                            "Bullets (one per line)",
                            "\n".join(
                                project.get("bullets", [])
                            ),
                            key=f"proj_bullets_{i}",
                            height=100,
                        )

                        project["bullets"] = [
                            bullet.strip("- ").strip()
                            for bullet in bullets_str.split("\n")
                            if bullet.strip()
                        ]


            # Education
            if data.get("education"):
                st.markdown("**Education**")

                for i, edu in enumerate(
                    data["education"]
                ):
                    cols = st.columns(3)

                    edu["degree"] = cols[0].text_input(
                        "Degree",
                        edu.get("degree", ""),
                        key=f"edu_degree_{i}",
                    )

                    edu["institution"] = cols[1].text_input(
                        "Institution",
                        edu.get("institution", ""),
                        key=f"edu_inst_{i}",
                    )

                    edu["dates"] = cols[2].text_input(
                        "Dates",
                        edu.get("dates", ""),
                        key=f"edu_dates_{i}",
                    )


            # Matched keywords
            if data.get("keywords_matched"):
                st.info(
                    "**JD keywords matched:** "
                    + ", ".join(
                        data["keywords_matched"]
                    )
                )


        # -------------------------------------------------------------------
        # Export
        # -------------------------------------------------------------------
        with st.container(border=True):
            st.markdown(
                '<div class="rm-section-label">⬇️ Export</div>',
                unsafe_allow_html=True,
            )

            exp_col1, exp_col2 = st.columns(2)

            with exp_col1:
                try:
                    pdf_bytes = build_pdf(
                        data,
                        st.session_state.template,
                    )

                    st.download_button(
                        "Download as PDF",
                        data=pdf_bytes,
                        file_name="tailored_resume.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

                except Exception as e:
                    st.error(f"Failed to build PDF: {e}")


            with exp_col2:
                try:
                    docx_bytes = build_docx(
                        data,
                        st.session_state.template,
                    )

                    st.download_button(
                        "Download as DOCX",
                        data=docx_bytes,
                        file_name="tailored_resume.docx",
                        mime=(
                            "application/"
                            "vnd.openxmlformats-officedocument."
                            "wordprocessingml.document"
                        ),
                        use_container_width=True,
                    )

                except Exception as e:
                    st.error(f"Failed to build DOCX: {e}")


    # -----------------------------------------------------------------------
    # Live preview
    # -----------------------------------------------------------------------
    with preview_col:
        st.html(
            f"""
            <div class="rm-preview-shell">
                <div class="rm-preview-label">Live preview</div>
                {render_preview_html(
                    data,
                    st.session_state.template,
                )}
            </div>
            """
        )


else:
    st.info(
        "Upload a resume and paste a JD, then click "
        "'Tailor my resume' to get started."
    )