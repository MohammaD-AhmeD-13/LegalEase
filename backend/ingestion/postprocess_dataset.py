import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


SECTION_NUMBER_PATTERN = re.compile(
    r"^\s*(?P<num>\d+[A-Za-z\-]*)\.\s+(?P<title>[^\n]+)$",
    re.MULTILINE,
)

SECTION_WORD_PATTERN = re.compile(
    r"^\s*(section|sec\.?)[\s\u00A0]+(?P<num>\d+[A-Za-z\-]*)\.\s*(?P<title>[^\n]+)$",
    re.IGNORECASE | re.MULTILINE,
)

PAGE_LINE_PATTERN = re.compile(r"^\s*(page\s*)?\d+\s*(of\s*\d+)?\s*$", re.IGNORECASE)

SCHEDULE_PATTERN = re.compile(
    r"\b(schedule|schedules|forms|tables?|index|fee chart|fees|appendix)\b",
    re.IGNORECASE,
)

TOC_LINE_PATTERN = re.compile(r"^\s*\d+[A-Za-z\-]*\.?\s+.+$")

FOOTNOTE_PATTERN = re.compile(r"^\s*\d+\s*(ins\.|subs\.|omitted)\b", re.IGNORECASE)


@dataclass
class Section:
    section_id: str
    title: str
    text: str


def normalize_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines: List[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if PAGE_LINE_PATTERN.match(stripped):
            continue
        stripped = re.sub(r"\s+", " ", stripped)
        lines.append(stripped)
    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def remove_toc_blocks(text: str) -> str:
    lines = text.split("\n")
    output: List[str] = []
    skipping = False

    for line in lines:
        stripped = line.strip()
        if stripped.lower() in {"sections", "sections."}:
            skipping = True
            continue
        if skipping:
            if not stripped:
                continue
            if TOC_LINE_PATTERN.match(stripped):
                continue
            skipping = False
        output.append(line)
    cleaned = "\n".join(output)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def is_toc_chunk(text: str) -> bool:
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return True
    if any("table of contents" in ln.lower() for ln in lines[:5]):
        return True
    if len(lines) >= 6:
        toc_like = sum(1 for ln in lines[:20] if TOC_LINE_PATTERN.match(ln))
        if toc_like / min(len(lines), 20) >= 0.6:
            return True
    if any(ln.lower() in {"sections.", "sections"} for ln in lines[:5]):
        numbered = sum(1 for ln in lines[:20] if re.match(r"^\d+\.", ln))
        if numbered >= 5:
            return True
    return False


def clean_section_title(raw_title: str) -> str | None:
    title = raw_title.strip()
    if not title:
        return None
    if not is_heading_candidate(title):
        return None
    for sep in ("—", "–"):
        if sep in title:
            title = title.split(sep)[0].strip()
    if "-(" in title:
        title = title.split("-(")[0].strip()
    if "(1)" in title:
        title = title.split("(1)")[0].strip()
    if PAGE_LINE_PATTERN.search(title):
        return None
    if SCHEDULE_PATTERN.search(title):
        return None
    if title.lower().startswith("page "):
        return None
    if len(title) > 120:
        return None
    return title


def is_heading_candidate(title: str) -> bool:
    lowered = title.strip().lower()
    if not lowered:
        return False
    if lowered in {"sections", "sections."}:
        return False
    if lowered.startswith("of the ") or lowered.startswith("of "):
        return False
    if FOOTNOTE_PATTERN.match(title):
        return False
    if any(lowered.startswith(prefix) for prefix in ("ins.", "subs.", "omitted", "subs ", "ins ")):
        return False
    if PAGE_LINE_PATTERN.search(title):
        return False
    return True


def extract_sections(text: str) -> List[Section]:
    matches = []
    for pattern in (SECTION_NUMBER_PATTERN, SECTION_WORD_PATTERN):
        matches.extend(list(pattern.finditer(text)))

    if not matches:
        return []

    matches.sort(key=lambda m: m.start())
    unique_matches = []
    seen_starts = set()
    for match in matches:
        if match.start() in seen_starts:
            continue
        title = match.group("title").strip()
        if not is_heading_candidate(title):
            continue
        seen_starts.add(match.start())
        unique_matches.append(match)

    sections: List[Section] = []
    for idx, match in enumerate(unique_matches):
        start = match.start()
        end = unique_matches[idx + 1].start() if idx + 1 < len(unique_matches) else len(text)
        section_text = text[start:end].strip()
        section_id = match.group("num").strip()
        title = match.group("title").strip()
        sections.append(Section(section_id=section_id, title=title, text=section_text))
    return sections


def is_non_substantive_section(section: Section) -> bool:
    combined = f"{section.title} {section.text}".lower()
    if section.title.strip().lower() in {"sections", "sections."}:
        return True
    if SCHEDULE_PATTERN.search(combined):
        return True
    if is_toc_chunk(section.text):
        return True
    if len(section.text.split()) < 25 and "(1)" not in section.text:
        return True
    return False


def estimate_tokens(text: str) -> int:
    words = len(text.split())
    return int(words * 1.3)


def chunk_section_text(text: str, min_tokens: int, max_tokens: int) -> Iterable[str]:
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    current: List[str] = []
    current_tokens = 0

    for word in words:
        current.append(word)
        current_tokens = estimate_tokens(" ".join(current))
        if current_tokens >= max_tokens:
            chunks.append(" ".join(current).strip())
            current = []
            current_tokens = 0

    if current:
        if chunks and estimate_tokens(" ".join(current)) < min_tokens:
            chunks[-1] = (chunks[-1] + " " + " ".join(current)).strip()
        else:
            chunks.append(" ".join(current).strip())

    return chunks


def load_dataset(path: Path) -> List[Dict]:
    records = json.loads(path.read_text(encoding="utf-8"))
    for idx, record in enumerate(records):
        record["__index"] = idx
    return records


def group_by_doc(records: List[Dict]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {}
    for record in records:
        grouped.setdefault(record["doc_id"], []).append(record)
    return grouped


def rebuild_text(records: List[Dict]) -> str:
    records_sorted = sorted(records, key=lambda r: r.get("__index", 0))
    return "\n\n".join(r.get("text", "") for r in records_sorted if r.get("text"))


def clean_dataset(input_path: Path, output_path: Path) -> None:
    records = load_dataset(input_path)
    grouped = group_by_doc(records)
    cleaned_records: List[Dict] = []

    for doc_id, doc_records in grouped.items():
        sample = doc_records[0]
        law_name = sample.get("law_name", doc_id)
        domain = sample.get("domain", "")
        jurisdiction = sample.get("jurisdiction", "Pakistan")
        source = sample.get("source", "Statute")
        language = sample.get("language", "en")

        raw_text = rebuild_text(doc_records)
        normalized = normalize_text(raw_text)
        normalized = remove_toc_blocks(normalized)
        sections = extract_sections(normalized)

        for section in sections:
            if is_non_substantive_section(section):
                continue

            section_title = clean_section_title(section.title)
            chunk_texts = chunk_section_text(section.text, min_tokens=300, max_tokens=500)
            for idx, chunk in enumerate(chunk_texts):
                cleaned_records.append(
                    {
                        "doc_id": doc_id,
                        "law_name": law_name,
                        "domain": domain,
                        "jurisdiction": jurisdiction,
                        "source": source,
                        "language": language,
                        "section_id": section.section_id,
                        "section_title": section_title,
                        "chunk_id": f"{doc_id}::sec-{section.section_id}::chunk-{idx}",
                        "chunk_index": idx,
                        "text": chunk,
                    }
                )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(cleaned_records, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post-process a Pakistani statutes RAG dataset.")
    parser.add_argument("--input", type=Path, required=True, help="Input JSON dataset path")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON dataset path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    clean_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
