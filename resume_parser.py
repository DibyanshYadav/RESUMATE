"""Extract raw text from an uploaded PDF resume."""
from pypdf import PdfReader
import io


def extract_text_from_pdf(uploaded_file) -> str:
    """
    uploaded_file: a file-like object from st.file_uploader (BytesIO)
    Returns the concatenated text of all pages.
    """
    reader = PdfReader(io.BytesIO(uploaded_file.read()))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n".join(text_parts).strip()
