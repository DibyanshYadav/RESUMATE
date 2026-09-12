import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from resume_parser import extract_text_from_pdf
from tailor import tailor_resume
from exporter import build_pdf, build_docx
from preview import render_preview_html, PREVIEW_CSS, TEMPLATE_META

st.set_page_config(page_title="Resumate — JD-Tailored Resume Builder", page_icon="📄", layout="wide")

# ---------------------------------------------------------------------------
# Global styling — Enhancv-style light SaaS look
# ---------------------------------------------------------------------------
st.markdown(f"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
{PREVIEW_CSS}
<style>
:root {{
    --accent: #2F5EFF;
    --accent-light: #EEF2FF;
    --panel: #F6F7FB;
    --text: #111827;
    --sub: #6B7280;
    --border: #E5E7EB;
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
    padding-top: 2rem;
    max-width: 1280px;
}}

/* ---- Hero header ---- */
.rm-hero {{
    background: linear-gradient(135deg, #2F5EFF 0%, #1E40D8 100%);
    border-radius: 16px;
    padding: 2.1rem 2.5rem;
    margin-bottom: 1.75rem;
    color: white;
    box-shadow: 0 8px 30px rgba(47, 94, 255, 0.25);
}}
.rm-hero h1 {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 1.9rem;
    margin: 0 0 0.35rem 0;
    color: white;
}}
.rm-hero p {{
    font-size: 0.95rem;
    margin: 0;
    opacity: 0.9;
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

/* ---- Cards (bordered containers) ---- */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: white;
    border-radius: 14px !important;
    border: 1px solid var(--border) !important;
    box-shadow: 0 2px 14px rgba(17, 24, 39, 0.04);
}}

/* ---- Buttons ---- */
.stButton > button, .stDownloadButton > button {{
    border-radius: 10px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    padding: 0.6rem 1.3rem;
    border: none;
    transition: transform 0.08s ease, box-shadow 0.15s ease;
}}
.stButton > button[kind="primary"], .stDownloadButton > button {{
    background: var(--accent);
    color: white;
    box-shadow: 0 4px 14px rgba(47, 94, 255, 0.3);
}}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {{
    background: #244ED1;
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(47, 94, 255, 0.4);
}}
.stButton > button:disabled {{
    background: #E5E7EB;
    color: #9CA3AF;
    box-shadow: none;
}}

/* ---- Inputs ---- */
.stTextInput input, .stTextArea textarea {{
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    font-family: 'Inter', sans-serif;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px var(--accent) !important;
}}

/* ---- File uploader: dashed upload zone ---- */
[data-testid="stFileUploaderDropzone"] {{
    background: var(--accent-light) !important;
    border: 1.5px dashed #B4C4FF !important;
    border-radius: 12px !important;
}}

/* ---- Template picker (radio as pills) ---- */
div[data-testid="stRadio"] > div {{
    flex-direction: row;
    gap: 0.6rem;
    flex-wrap: wrap;
}}
div[data-testid="stRadio"] label {{
    background: white;
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
div[data-testid="stRadio"] label[data-checked="true"] {{
    background: var(--accent-light);
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
}}

.stAlert {{
    border-radius: 10px;
}}
</style>
""", unsafe_allow_html=True)

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
st.markdown("""
<div class="rm-hero">
    <h1>📄 Resumate</h1>
    <p>Upload your resume, paste a job description, and get a tailored version — edit it live, then export in the template you like.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Step 1: Inputs
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown('<div class="rm-section-label">📤 Your resume</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"], label_visibility="collapsed")
        if uploaded_file is not None:
            st.session_state.raw_resume_text = extract_text_from_pdf(uploaded_file)
            with st.expander("Preview extracted resume text"):
                st.text_area("Extracted text", st.session_state.raw_resume_text, height=200, disabled=True,
                              label_visibility="collapsed")

with col2:
    with st.container(border=True):
        st.markdown('<div class="rm-section-label">🎯 Job description</div>', unsafe_allow_html=True)
        job_description = st.text_area("Paste the job description", height=232, label_visibility="collapsed",
                                        placeholder="Paste the full job description here…")

st.write("")
_, btn_col, _ = st.columns([1, 1, 1])
with btn_col:
    generate = st.button(
        "✨ Tailor my resume", type="primary", use_container_width=True,
        disabled=not (st.session_state.raw_resume_text and job_description),
    )

if generate:
    with st.spinner("Tailoring your resume against the JD..."):
        try:
            st.session_state.resume_data = tailor_resume(st.session_state.raw_resume_text, job_description)
        except Exception as e:
            st.error(f"Failed to generate tailored resume: {e}")

st.write("")

# ---------------------------------------------------------------------------
# Step 2: Edit + live preview
# ---------------------------------------------------------------------------
data = st.session_state.resume_data
if data:
    edit_col, preview_col = st.columns([0.52, 0.48], gap="large")

    with edit_col:
        with st.container(border=True):
            st.markdown('<div class="rm-section-label">🎨 Template</div>', unsafe_allow_html=True)
            template_keys = list(TEMPLATE_META.keys())
            st.session_state.template = st.radio(
                "Template",
                options=template_keys,
                format_func=lambda k: TEMPLATE_META[k]["label"],
                index=template_keys.index(st.session_state.template),
                horizontal=True,
                label_visibility="collapsed",
            )
            st.caption(TEMPLATE_META[st.session_state.template]["description"])

        with st.container(border=True):
            st.markdown('<div class="rm-section-label">✏️ Edit your tailored resume</div>', unsafe_allow_html=True)

            data["name"] = st.text_input("Name", data.get("name", ""))
            data["contact"] = st.text_input("Contact info", data.get("contact", ""))
            data["summary"] = st.text_area("Summary", data.get("summary", ""), height=100)

            skills_str = st.text_area("Skills (comma-separated)", ", ".join(data.get("skills", [])), height=70)
            data["skills"] = [s.strip() for s in skills_str.split(",") if s.strip()]

            st.markdown("**Experience**")
            for i, job in enumerate(data.get("experience", [])):
                with st.expander(f"{job.get('title','')} — {job.get('company','')}", expanded=False):
                    job["title"] = st.text_input("Title", job.get("title", ""), key=f"exp_title_{i}")
                    job["company"] = st.text_input("Company", job.get("company", ""), key=f"exp_company_{i}")
                    job["dates"] = st.text_input("Dates", job.get("dates", ""), key=f"exp_dates_{i}")
                    bullets_str = st.text_area(
                        "Bullets (one per line)", "\n".join(job.get("bullets", [])), key=f"exp_bullets_{i}", height=120
                    )
                    job["bullets"] = [b.strip("- ").strip() for b in bullets_str.split("\n") if b.strip()]

            if data.get("projects"):
                st.markdown("**Projects**")
                for i, proj in enumerate(data["projects"]):
                    with st.expander(proj.get("name", f"Project {i+1}")):
                        proj["name"] = st.text_input("Project name", proj.get("name", ""), key=f"proj_name_{i}")
                        proj["description"] = st.text_area("Description", proj.get("description", ""), key=f"proj_desc_{i}")
                        bullets_str = st.text_area(
                            "Bullets (one per line)", "\n".join(proj.get("bullets", [])), key=f"proj_bullets_{i}", height=100
                        )
                        proj["bullets"] = [b.strip("- ").strip() for b in bullets_str.split("\n") if b.strip()]

            if data.get("education"):
                st.markdown("**Education**")
                for i, edu in enumerate(data["education"]):
                    cols = st.columns(3)
                    edu["degree"] = cols[0].text_input("Degree", edu.get("degree", ""), key=f"edu_degree_{i}")
                    edu["institution"] = cols[1].text_input("Institution", edu.get("institution", ""), key=f"edu_inst_{i}")
                    edu["dates"] = cols[2].text_input("Dates", edu.get("dates", ""), key=f"edu_dates_{i}")

            if data.get("keywords_matched"):
                st.info("**JD keywords matched:** " + ", ".join(data["keywords_matched"]))

        with st.container(border=True):
            st.markdown('<div class="rm-section-label">⬇️ Export</div>', unsafe_allow_html=True)
            exp_col1, exp_col2 = st.columns(2)
            with exp_col1:
                pdf_bytes = build_pdf(data, st.session_state.template)
                st.download_button("Download as PDF", data=pdf_bytes, file_name="tailored_resume.pdf",
                                    mime="application/pdf", use_container_width=True)
            with exp_col2:
                docx_bytes = build_docx(data, st.session_state.template)
                st.download_button(
                    "Download as DOCX", data=docx_bytes, file_name="tailored_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )

    with preview_col:
        st.markdown('<div class="rm-preview-shell">', unsafe_allow_html=True)
        st.markdown('<div class="rm-preview-label">Live preview</div>', unsafe_allow_html=True)
        st.markdown(render_preview_html(data, st.session_state.template), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Upload a resume and paste a JD, then click 'Tailor my resume' to get started.")