from pypdf import PdfReader

def load_resume():
    reader = PdfReader("data/resume.pdf")
    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text