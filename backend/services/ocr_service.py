import io
from typing import Optional


def _extract_pdf_text(data: bytes) -> str:
	try:
		from pypdf import PdfReader
	except Exception as exc:  # pragma: no cover
		raise RuntimeError("Missing PDF parser. Install pypdf.") from exc

	reader = PdfReader(io.BytesIO(data))
	pages = []
	for page in reader.pages:
		text = page.extract_text() or ""
		if text.strip():
			pages.append(text)
	return "\n\n".join(pages).strip()


def _extract_docx_text(data: bytes) -> str:
	try:
		import docx
	except Exception as exc:  # pragma: no cover
		raise RuntimeError("Missing DOCX parser. Install python-docx.") from exc

	document = docx.Document(io.BytesIO(data))
	paragraphs = [para.text for para in document.paragraphs if para.text.strip()]
	return "\n".join(paragraphs).strip()


def extract_text(filename: str, data: bytes) -> Optional[str]:
	if not data:
		return None
	name = (filename or "").lower()
	if name.endswith(".pdf"):
		return _extract_pdf_text(data)
	if name.endswith(".docx"):
		return _extract_docx_text(data)
	return None
