"""Tailor a resume against a job description using an LLM."""
import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re

try:
    import streamlit as st
    if "GROQ_API_KEY" in st.secrets and not os.environ.get("GROQ_API_KEY"):
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass  # no secrets.toml locally, or streamlit not in this context — fine, .env / real env var will cover it

SYSTEM_PROMPT = """You are an expert resume writer and ATS optimization specialist.
You will be given a candidate's existing resume text and a target job description (JD).

Your job:
1. Identify the key skills, tools, and keywords from the JD that ATS systems and recruiters will scan for.
2. Rewrite the resume content so it truthfully emphasizes the candidate's existing experience that matches the JD.
   NEVER invent new jobs, degrees, companies, or skills the candidate did not have. Only rephrase, reorder,
   and emphasize what already exists in the original resume.
3. Tighten bullet points into strong, quantifiable, action-verb-led statements where the original content allows it.
4. Reorder or emphasize sections so the most JD-relevant experience appears first within each section.

Return ONLY a valid JSON object with this exact structure, no markdown fences, no commentary:
{
  "name": "string",
  "contact": "string (email / phone / linkedin / location, whatever was in original)",
  "summary": "string - 2-4 sentence professional summary tailored to the JD",
  "skills": ["skill1", "skill2", "..."],
  "experience": [
    {
      "title": "string",
      "company": "string",
      "dates": "string",
      "bullets": ["bullet1", "bullet2"]
    }
  ],
  "projects": [
    {
      "name": "string",
      "description": "string",
      "bullets": ["bullet1"]
    }
  ],
  "education": [
    {
      "degree": "string",
      "institution": "string",
      "dates": "string"
    }
  ],
  "keywords_matched": ["JD keywords the candidate's real background supports"]
}

If a section (e.g. projects) doesn't exist in the original resume, return an empty list for it.
Do not fabricate any field. If contact info isn't found, leave it as an empty string.
"""


def _get_llm():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0.3,
        max_tokens=3000,
    )


def _extract_json(raw: str) -> dict:
    """Strip markdown fences if present and parse JSON, with a fallback regex grab."""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def tailor_resume(resume_text: str, job_description: str) -> dict:
    """
    Calls the LLM to produce a structured, tailored resume as a dict.
    Raises on unrecoverable parse failure (caller should show an error).
    """
    llm = _get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"ORIGINAL RESUME:\n{resume_text}\n\n---\n\nJOB DESCRIPTION:\n{job_description}"
        ),
    ]
    response = llm.invoke(messages)
    return _extract_json(response.content)
