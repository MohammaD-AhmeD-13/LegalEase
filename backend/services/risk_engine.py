import asyncio
import json
from typing import Any, Dict


def _safe_json_parse(raw: str) -> Dict[str, Any]:
	try:
		return json.loads(raw)
	except Exception:
		return {}


async def analyze_risks(text: str, llm) -> Dict[str, Any]:
	excerpt = text.strip()[:12000]
	prompt = (
		"You are a legal contract analysis assistant specialized in identifying risky, unfair, or illegal clauses. "
		"Analyze the provided contract carefully and return a structured response. "
		"Identify: risky clauses (unfair, one-sided, exploitative terms), compliance issues "
		"(illegal or unethical clauses), and recommendations for improvement. "
		"For each risky clause: quote the exact clause text, assign severity High/Medium/Low, "
		"and explain why it is risky. Be strict. Assume the user is non-expert and needs protection. "
		"Return output ONLY in JSON format with this schema: "
		"{\"risky_clauses\": [{\"clause\": string, \"severity\": \"High\"|\"Medium\"|\"Low\", \"reason\": string}], "
		"\"compliance_issues\": [{\"issue\": string, \"reason\": string}], "
		"\"recommendations\": [string]}. "
		"If the document contains absurd, unethical, or illegal clauses, you MUST flag them. "
		"Do not add any keys outside the schema."
		"\n\nDocument excerpt:\n"
		f"{excerpt}"
	)
	try:
		raw = await asyncio.wait_for(llm.generate(prompt, max_new_tokens=384), timeout=480)
	except asyncio.TimeoutError:
		return {
			"summary": "Review timed out. Please try again with a shorter document.",
			"risky_clauses": [],
			"compliance_issues": [],
			"recommendations": [],
		}
	parsed = _safe_json_parse(raw)

	summary = parsed.get("summary") or "Review completed."
	risky_clauses = parsed.get("risky_clauses") or []
	compliance_issues = parsed.get("compliance_issues") or []
	recommendations = parsed.get("recommendations") or []

	return {
		"summary": summary,
		"risky_clauses": risky_clauses,
		"compliance_issues": compliance_issues,
		"recommendations": recommendations,
	}
