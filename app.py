import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from resume_parser import extract_text_from_pdf
from tailor import tailor_resume
from exporter import build_pdf, build_docx

st.set_page_config(page_title="JD-Tailored Resume Builder", layout="wide")
st.title("📄 JD-Tailored Resume Builder")
st.caption("Upload your resume, paste a job description, get a tailored version you can edit and export.")

if "resume_data" not in st.session_state:
    st.session_state.resume_data = None
if "raw_resume_text" not in st.session_state:
    st.session_state.raw_resume_text = ""

# ---------- Step 1: Inputs ----------
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    if uploaded_file is not None:
        st.session_state.raw_resume_text = extract_text_from_pdf(uploaded_file)
        with st.expander("Preview extracted resume text"):
            st.text_area("Extracted text", st.session_state.raw_resume_text, height=200, disabled=True)

with col2:
    job_description = st.text_area("Paste the job description", height=280)

generate = st.button("✨ Tailor my resume", type="primary", disabled=not (st.session_state.raw_resume_text and job_description))

if generate:
    with st.spinner("Tailoring your resume against the JD..."):
        try:
            st.session_state.resume_data = tailor_resume(st.session_state.raw_resume_text, job_description)
        except Exception as e:
            st.error(f"Failed to generate tailored resume: {e}")

st.divider()

# ---------- Step 2: Edit ----------
data = st.session_state.resume_data
if data:
    st.subheader("✏️ Edit your tailored resume")

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

    st.divider()
    st.subheader("⬇️ Export")

    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        pdf_bytes = build_pdf(data)
        st.download_button("Download as PDF", data=pdf_bytes, file_name="tailored_resume.pdf", mime="application/pdf")
    with exp_col2:
        docx_bytes = build_docx(data)
        st.download_button(
            "Download as DOCX",
            data=docx_bytes,
            file_name="tailored_resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
else:
    st.info("Upload a resume and paste a JD, then click 'Tailor my resume' to get started.")
