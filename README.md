# RESUMATE

An AI-powered resume builder that tailors your existing resume to a specific job description — then lets you edit it in-app and export a polished PDF or DOCX.

## What it does

1. **Upload** your resume as a PDF.
2. **Paste** a job description you're applying to.
3. RESUMATE uses an LLM (via Groq) to rewrite and reorder your resume — emphasizing the experience, skills, and keywords that actually match the JD.
4. **Edit** every section directly in the app before exporting.
5. **Download** the final result as a formatted PDF or DOCX.

Nothing is fabricated — the model is instructed to only rephrase, reorder, and emphasize content that already exists in your original resume. It won't invent jobs, degrees, or skills you don't have.

## Tech stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| LLM orchestration | LangChain |
| Model inference | Groq (`openai/gpt-oss-120b`) |
| PDF parsing | pypdf |
| PDF export | fpdf2 |
| DOCX export | python-docx |

## Project structure

```
resume_builder/
├── app.py              # Streamlit UI — upload, edit, export
├── tailor.py           # LLM logic — tailors resume JSON against the JD
├── exporter.py         # Renders structured resume data to PDF / DOCX
├── resume_parser.py    # Extracts raw text from an uploaded PDF
└── requirements.txt
```

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/DibyanshYadav/RESUMATE.git
   cd RESUMATE
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add your Groq API key. Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```
   Get a free key at [console.groq.com](https://console.groq.com).

4. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deployment

Deployed on [Streamlit Community Cloud](https://share.streamlit.io). To deploy your own copy:

1. Fork/push this repo to your own GitHub.
2. Create a new app on Streamlit Cloud pointing to `app.py`.
3. Add `GROQ_API_KEY` under the app's **Secrets** settings (TOML format):
   ```
   GROQ_API_KEY = "your_key_here"
   ```

## Roadmap

- Match-score indicator showing JD keyword coverage
- Cover letter generation from the same JD
- Resume version history (Supabase-backed)

## License

MIT
