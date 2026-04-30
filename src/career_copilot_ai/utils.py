import PyPDF2

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a given PDF file."""
    text = ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
    except FileNotFoundError:
        print(f"Warning: File {pdf_path} not found. Using placeholder text.")
        text = "Experienced software engineer with skills in Python, AI, and web development."
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text.strip()
