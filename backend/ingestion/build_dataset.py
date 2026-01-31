import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


ALLOWED_STATUTES = {
	"contract act, 1872": {
		"law_name": "Contract Act, 1872",
		"domain": "Contract Law",
	},
	"companies act, 2017": {
		"law_name": "Companies Act, 2017",
		"domain": "Business / Corporate Law",
	},
	"income tax ordinance, 2001": {
		"law_name": "Income Tax Ordinance, 2001",
		"domain": "Tax Law",
	},
	"industrial relations act, 2012": {
		"law_name": "Industrial Relations Act, 2012",
		"domain": "Employment / Labour Law",
	},
}


SECTION_PATTERN = re.compile(
	r"^\s*(section|sec\.?)[\s\u00A0]+(?P<num>\d+[A-Za-z\-]*)\s*[\.:\-]?\s*(?P<title>.*)$",
	re.IGNORECASE | re.MULTILINE,
)


PAGE_LINE_PATTERN = re.compile(r"^\s*(page\s*)?\d+\s*$", re.IGNORECASE)


@dataclass
class Section:
	section_id: str
	title: str
	text: str


def detect_language(text: str) -> str:
	has_urdu = any("\u0600" <= ch <= "\u06FF" for ch in text)
	has_latin = any("A" <= ch <= "z" for ch in text)
	if has_urdu and has_latin:
		return "mixed"
	if has_urdu:
		return "ur"
	return "en"


def normalize_text(raw_text: str) -> str:
	text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
	lines = []
	for line in text.split("\n"):
		line = line.strip()
		if not line:
			lines.append("")
			continue
		if PAGE_LINE_PATTERN.match(line):
			continue
		line = re.sub(r"\s+", " ", line)
		lines.append(line)
	normalized = "\n".join(lines)
	normalized = re.sub(r"\n{3,}", "\n\n", normalized)
	return normalized.strip()


def extract_sections(text: str) -> List[Section]:
	matches = list(SECTION_PATTERN.finditer(text))
	if not matches:
		return [Section(section_id="root", title="", text=text.strip())]

	sections: List[Section] = []
	for idx, match in enumerate(matches):
		start = match.start()
		end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
		section_text = text[start:end].strip()
		section_id = match.group("num").strip()
		title = match.group("title").strip()
		sections.append(Section(section_id=section_id, title=title, text=section_text))
	return sections


def chunk_text(text: str, chunk_size: int, overlap: int) -> Iterable[Tuple[int, int, str]]:
	if chunk_size <= 0:
		raise ValueError("chunk_size must be > 0")
	if overlap >= chunk_size:
		raise ValueError("overlap must be < chunk_size")

	start = 0
	length = len(text)
	while start < length:
		end = min(start + chunk_size, length)
		if end < length:
			window = text[start:end]
			last_space = window.rfind(" ")
			if last_space > chunk_size * 0.6:
				end = start + last_space
		chunk = text[start:end].strip()
		if chunk:
			yield start, end, chunk
		if end >= length:
			break
		start = max(0, end - overlap)


def map_law_metadata(file_path: Path) -> Tuple[str, str]:
	name_lower = file_path.stem.lower()
	for key, meta in ALLOWED_STATUTES.items():
		if key in name_lower:
			return meta["law_name"], meta["domain"]
	raise ValueError(
		f"File {file_path.name} does not match allowed statutes. Allowed: {', '.join(ALLOWED_STATUTES.keys())}"
	)


def build_dataset(input_dir: Path, output_path: Path, chunk_size: int, overlap: int) -> None:
	records = []
	txt_files = sorted(input_dir.glob("*.txt"))
	if not txt_files:
		raise FileNotFoundError(f"No .txt files found in {input_dir}")

	for txt_file in txt_files:
		law_name, domain = map_law_metadata(txt_file)
		raw_text = txt_file.read_text(encoding="utf-8", errors="ignore")
		normalized = normalize_text(raw_text)
		language = detect_language(normalized)
		sections = extract_sections(normalized)

		for section in sections:
			for chunk_index, (start, end, chunk) in enumerate(
				chunk_text(section.text, chunk_size=chunk_size, overlap=overlap)
			):
				records.append(
					{
						"doc_id": txt_file.stem,
						"law_name": law_name,
						"domain": domain,
						"jurisdiction": "Pakistan",
						"source": "Statute",
						"language": language,
						"section_id": section.section_id,
						"section_title": section.title,
						"chunk_id": f"{txt_file.stem}::sec-{section.section_id}::chunk-{chunk_index}",
						"chunk_index": chunk_index,
						"chunk_char_start": start,
						"chunk_char_end": end,
						"text": chunk,
					}
				)

	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Build a minimal RAG dataset from Pakistani statutes.")
	parser.add_argument(
		"--input-dir",
		type=Path,
		required=True,
		help="Folder containing the 4 statute .txt files",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=Path(__file__).resolve().parents[1] / "data" / "legalease_rag_dataset.json",
		help="Output JSON file path",
	)
	parser.add_argument("--chunk-size", type=int, default=1200)
	parser.add_argument("--overlap", type=int, default=200)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	build_dataset(args.input_dir, args.output, args.chunk_size, args.overlap)


if __name__ == "__main__":
	main()
