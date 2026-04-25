import asyncio
import json
import re
from typing import Any, Dict


RISK_KEYWORDS = (
	"liability",
	"termination",
	"penalty",
	"indemnify",
	"indemnity",
	"breach",
	"damages",
	"governing law",
	"jurisdiction",
	"confidential",
	"non-compete",
	"exclusive",
	"dispute",
	"arbitration",
	"waiver",
)

MISSING_CLAUSE_FALLBACKS = [
	("Termination conditions are unclear or missing.", "Medium", "No clear exit terms can lock parties into unfair obligations."),
	("Liability cap or exclusion terms are missing/unclear.", "High", "Unbounded liability can expose a party to disproportionate losses."),
	("Dispute resolution and jurisdiction terms are missing.", "Medium", "Without forum and process, conflicts can become costly and prolonged."),
]


def _safe_json_parse(raw: str) -> Dict[str, Any]:
	try:
		return json.loads(raw)
	except Exception:
		if not raw:
			return {}
		# Recover from fenced or noisy generations by extracting first JSON object.
		start = raw.find("{")
		end = raw.rfind("}")
		if start >= 0 and end > start:
			candidate = raw[start:end + 1]
			try:
				return json.loads(candidate)
			except Exception:
				return {}
		return {}


def _split_by_structure(text: str) -> list[str]:
	cleaned = re.sub(r"\r\n?", "\n", text or "")
	cleaned = re.sub(r"[\t\u00A0]+", " ", cleaned).strip()
	if not cleaned:
		return []

	# Prefer structural boundaries: headings, numbered clauses, and paragraphs.
	units = re.split(
		r"\n{2,}|(?=\n\s*(?:section|clause|article)\s+\d+[\.:\)])|(?=\n\s*\d+[\.)]\s+)",
		cleaned,
		flags=re.IGNORECASE,
	)
	return [re.sub(r"\s+", " ", unit).strip() for unit in units if unit and unit.strip()]


def _build_chunks(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
	units = _split_by_structure(text)
	if not units:
		return []

	chunks: list[str] = []
	current_words: list[str] = []

	for unit in units:
		words = unit.split()
		if not words:
			continue

		if len(current_words) + len(words) <= chunk_size:
			current_words.extend(words)
			continue

		if current_words:
			chunks.append(" ".join(current_words))
			current_words = current_words[-overlap:] if overlap > 0 else []

		if len(words) <= chunk_size:
			current_words.extend(words)
		else:
			start = 0
			step = max(1, chunk_size - overlap)
			while start < len(words):
				window = words[start:start + chunk_size]
				if not window:
					break
				chunks.append(" ".join(window))
				start += step
			current_words = []

	if current_words:
		chunks.append(" ".join(current_words))

	return chunks


def _prioritize_chunks(chunks: list[str], limit: int = 8) -> list[str]:
	if not chunks:
		return []

	def score(chunk: str) -> int:
		lower = chunk.lower()
		keyword_hits = sum(1 for key in RISK_KEYWORDS if key in lower)
		# Prefer richer, clause-like content over tiny fragments.
		length_bonus = min(len(chunk.split()) // 50, 4)
		return keyword_hits * 4 + length_bonus

	scored = sorted(enumerate(chunks), key=lambda item: (score(item[1]), -item[0]), reverse=True)
	selected = [chunk for _, chunk in scored[:max(1, limit)]]
	return selected


def _normalize_risk_payload(parsed: Dict[str, Any]) -> Dict[str, Any]:
	risky_raw = parsed.get("risky_clauses") if isinstance(parsed, dict) else []
	issues_raw = parsed.get("compliance_issues") if isinstance(parsed, dict) else []
	recs_raw = parsed.get("recommendations") if isinstance(parsed, dict) else []

	risky_clauses: list[Dict[str, str]] = []
	if isinstance(risky_raw, list):
		for item in risky_raw:
			if not isinstance(item, dict):
				continue
			clause = str(item.get("clause") or "").strip()
			reason = str(item.get("reason") or "").strip()
			severity = str(item.get("severity") or "Medium").capitalize()
			if severity not in {"High", "Medium", "Low"}:
				severity = "Medium"
			if not clause and not reason:
				continue
			risky_clauses.append(
				{
					"clause": clause or "Potential missing or ambiguous clause.",
					"severity": severity,
					"reason": reason or "The text may create uncertainty or imbalance between parties.",
				}
			)

	if len(risky_clauses) < 3:
		for clause, severity, reason in MISSING_CLAUSE_FALLBACKS:
			if len(risky_clauses) >= 3:
				break
			risky_clauses.append({"clause": clause, "severity": severity, "reason": reason})

	compliance_issues: list[Dict[str, str]] = []
	if isinstance(issues_raw, list):
		for item in issues_raw:
			if not isinstance(item, dict):
				continue
			issue = str(item.get("issue") or "").strip()
			reason = str(item.get("reason") or "").strip()
			if not issue and not reason:
				continue
			compliance_issues.append({"issue": issue or "Potential compliance gap.", "reason": reason or "Requires legal review."})

	recommendations: list[str] = []
	if isinstance(recs_raw, list):
		recommendations = [str(item).strip() for item in recs_raw if str(item).strip()]
	if not recommendations:
		recommendations = [
			"Add explicit termination triggers and notice periods.",
			"Define balanced liability and indemnity limits.",
			"Add governing law and dispute resolution clauses.",
		]

	return {
		"risky_clauses": risky_clauses,
		"compliance_issues": compliance_issues,
		"recommendations": recommendations,
	}


async def analyze_risks(text: str, llm) -> Dict[str, Any]:
	chunks = _build_chunks(text, chunk_size=500, overlap=100)
	selected = _prioritize_chunks(chunks, limit=8)
	excerpt = "\n\n---\n\n".join(selected).strip()[:18000]
	if not excerpt:
		excerpt = (text or "").strip()[:12000]

	prompt = (
		"You are a legal risk analyzer. "
		"Your task is to STRICTLY identify risky clauses in the document. "
		"You MUST always return at least 3 potential risks, even when confidence is low. "
		"If explicit risks are limited, return missing-clause risks (termination, liability, jurisdiction, dispute resolution, penalties). "
		"For each risk, quote exact clause text when available; otherwise state the likely missing clause. "
		"Return output ONLY as valid JSON with this exact schema and no extra keys: "
		"{\"summary\": string, "
		"\"risky_clauses\": [{\"clause\": string, \"risk\": string, \"severity\": \"Low\"|\"Medium\"|\"High\", \"reason\": string, \"confidence\": number}], "
		"\"compliance_issues\": [{\"issue\": string, \"reason\": string}], "
		"\"recommendations\": [string]}. "
		"confidence must be a decimal between 0 and 1. "
		"Do not output markdown or prose outside JSON."
		"\n\nDocument excerpt:\n"
		f"{excerpt}"
	)
	try:
		raw = await asyncio.wait_for(llm.generate(prompt, max_new_tokens=512), timeout=480)
	except asyncio.TimeoutError:
		return {
			"summary": "Review timed out. Please try again with a shorter document.",
			"risky_clauses": [
				{"clause": clause, "severity": severity, "reason": reason}
				for clause, severity, reason in MISSING_CLAUSE_FALLBACKS
			],
			"compliance_issues": [],
			"recommendations": ["Retry with a shorter section-focused document for deeper review."],
		}
	parsed = _safe_json_parse(raw)
	normalized = _normalize_risk_payload(parsed)

	summary = "Review completed with potential risks identified."
	if isinstance(parsed, dict) and parsed.get("summary"):
		summary = str(parsed.get("summary")).strip()

	return {
		"summary": summary,
		"risky_clauses": normalized["risky_clauses"],
		"compliance_issues": normalized["compliance_issues"],
		"recommendations": normalized["recommendations"],
	}
