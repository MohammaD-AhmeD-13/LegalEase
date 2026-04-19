from __future__ import annotations

import html
import re
from typing import Any, Dict, List, Tuple


TEMPLATES: Dict[str, Dict[str, Any]] = {
    "nda": {
        "id": "nda",
        "name": "Non-Disclosure Agreement (NDA)",
        "description": "Mutual NDA for sharing confidential information.",
        "fields": [
            {
                "key": "effective_date",
                "label": "Effective date",
                "required": True,
                "placeholder": "April 19, 2026",
            },
            {
                "key": "disclosing_party",
                "label": "Disclosing party",
                "required": True,
                "placeholder": "Company A",
            },
            {
                "key": "receiving_party",
                "label": "Receiving party",
                "required": True,
                "placeholder": "Company B",
            },
            {
                "key": "purpose",
                "label": "Purpose",
                "required": True,
                "placeholder": "Evaluation of a potential partnership",
            },
            {
                "key": "term",
                "label": "Confidentiality term",
                "required": True,
                "placeholder": "2 years",
            },
            {
                "key": "governing_law",
                "label": "Governing law",
                "required": False,
                "placeholder": "Pakistan",
                "default": "Pakistan",
            },
        ],
        "body": (
            "NON-DISCLOSURE AGREEMENT (NDA)\n\n"
            "This Non-Disclosure Agreement (\"Agreement\") is made on {effective_date} between "
            "{disclosing_party} (\"Disclosing Party\") and {receiving_party} (\"Receiving Party\").\n\n"
            "Purpose: {purpose}.\n\n"
            "1. Definition of Confidential Information: Any non-public information shared by the Disclosing Party "
            "in any form that is marked or reasonably understood to be confidential.\n"
            "2. Obligations: The Receiving Party will keep Confidential Information strictly confidential and "
            "use it only for the stated Purpose.\n"
            "3. Exclusions: Confidential Information does not include information that is publicly available, "
            "already known, independently developed, or lawfully received from a third party.\n"
            "4. Term: The confidentiality obligations will remain in effect for {term} from the Effective Date.\n"
            "5. Return/Destruction: Upon request, the Receiving Party will return or destroy all Confidential "
            "Information and certify completion.\n"
            "6. Governing Law: This Agreement is governed by the laws of {governing_law}.\n\n"
            "Signed by the parties:\n\n"
            "Disclosing Party: ________________________\n"
            "Receiving Party: ________________________\n"
        ),
    },
    "affidavit": {
        "id": "affidavit",
        "name": "Affidavit",
        "description": "General affidavit template for statements under oath.",
        "fields": [
            {
                "key": "deponent_name",
                "label": "Deponent name",
                "required": True,
                "placeholder": "Ahsan Ali",
            },
            {
                "key": "father_name",
                "label": "Father or guardian name",
                "required": True,
                "placeholder": "Muhammad Ali",
            },
            {
                "key": "address",
                "label": "Address",
                "required": True,
                "placeholder": "House #12, Street 5, Lahore",
            },
            {
                "key": "statement",
                "label": "Statement of facts",
                "required": True,
                "placeholder": "State the facts you are affirming",
            },
            {
                "key": "place",
                "label": "Place",
                "required": True,
                "placeholder": "Lahore",
            },
            {
                "key": "date",
                "label": "Date",
                "required": True,
                "placeholder": "April 19, 2026",
            },
        ],
        "body": (
            "AFFIDAVIT\n\n"
            "I, {deponent_name}, son/daughter of {father_name}, resident of {address}, do hereby solemnly affirm "
            "and declare as under:\n\n"
            "{statement}\n\n"
            "I affirm that the above statement is true to the best of my knowledge and belief.\n\n"
            "Place: {place}\n"
            "Date: {date}\n\n"
            "Deponent Signature: ________________________\n"
        ),
    },
    "service_agreement": {
        "id": "service_agreement",
        "name": "Service Agreement",
        "description": "Basic agreement for professional or business services.",
        "fields": [
            {
                "key": "effective_date",
                "label": "Effective date",
                "required": True,
                "placeholder": "April 19, 2026",
            },
            {
                "key": "client_name",
                "label": "Client name",
                "required": True,
                "placeholder": "Client Co",
            },
            {
                "key": "service_provider",
                "label": "Service provider",
                "required": True,
                "placeholder": "Provider Co",
            },
            {
                "key": "services",
                "label": "Scope of services",
                "required": True,
                "placeholder": "Software development and maintenance",
            },
            {
                "key": "fee",
                "label": "Fee",
                "required": True,
                "placeholder": "PKR 200,000",
            },
            {
                "key": "payment_terms",
                "label": "Payment terms",
                "required": True,
                "placeholder": "50% upfront, 50% on delivery",
            },
            {
                "key": "term",
                "label": "Term",
                "required": True,
                "placeholder": "6 months",
            },
            {
                "key": "governing_law",
                "label": "Governing law",
                "required": False,
                "placeholder": "Pakistan",
                "default": "Pakistan",
            },
        ],
        "body": (
            "SERVICE AGREEMENT\n\n"
            "This Service Agreement (\"Agreement\") is made on {effective_date} between {client_name} (\"Client\") "
            "and {service_provider} (\"Service Provider\").\n\n"
            "1. Services: The Service Provider will provide the following services: {services}.\n"
            "2. Term: This Agreement will remain in effect for {term} unless terminated earlier.\n"
            "3. Fees: The Client will pay {fee} under the following terms: {payment_terms}.\n"
            "4. Confidentiality: Both parties agree to keep confidential information private.\n"
            "5. Termination: Either party may terminate with written notice in case of material breach.\n"
            "6. Governing Law: This Agreement is governed by the laws of {governing_law}.\n\n"
            "Signed by the parties:\n\n"
            "Client: ________________________\n"
            "Service Provider: ________________________\n"
        ),
    },
    "rental_agreement": {
        "id": "rental_agreement",
        "name": "Rental Agreement",
        "description": "Residential rental agreement template.",
        "fields": [
            {
                "key": "effective_date",
                "label": "Effective date",
                "required": True,
                "placeholder": "April 19, 2026",
            },
            {
                "key": "landlord_name",
                "label": "Landlord name",
                "required": True,
                "placeholder": "Landlord Name",
            },
            {
                "key": "tenant_name",
                "label": "Tenant name",
                "required": True,
                "placeholder": "Tenant Name",
            },
            {
                "key": "property_address",
                "label": "Property address",
                "required": True,
                "placeholder": "House #12, Street 5, Lahore",
            },
            {
                "key": "rent",
                "label": "Monthly rent",
                "required": True,
                "placeholder": "PKR 45,000",
            },
            {
                "key": "deposit",
                "label": "Security deposit",
                "required": True,
                "placeholder": "PKR 90,000",
            },
            {
                "key": "term",
                "label": "Lease term",
                "required": True,
                "placeholder": "12 months",
            },
            {
                "key": "payment_due",
                "label": "Rent due date",
                "required": True,
                "placeholder": "5th of each month",
            },
        ],
        "body": (
            "RENTAL AGREEMENT\n\n"
            "This Rental Agreement is made on {effective_date} between {landlord_name} (\"Landlord\") and "
            "{tenant_name} (\"Tenant\") for the property located at {property_address}.\n\n"
            "1. Term: The lease term is {term}.\n"
            "2. Rent: Monthly rent is {rent}, due on {payment_due}.\n"
            "3. Security Deposit: Tenant will pay {deposit} as a security deposit, refundable subject to inspection.\n"
            "4. Maintenance: Tenant will keep the property in good condition and report issues promptly.\n"
            "5. Termination: Either party may terminate per applicable law with written notice.\n\n"
            "Signed by the parties:\n\n"
            "Landlord: ________________________\n"
            "Tenant: ________________________\n"
        ),
    },
}


def list_templates() -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    for template in TEMPLATES.values():
        summaries.append(
            {
                "id": template["id"],
                "name": template["name"],
                "description": template["description"],
                "fields": [
                    {
                        "key": field["key"],
                        "label": field["label"],
                        "required": field.get("required", False),
                        "placeholder": field.get("placeholder", ""),
                        "default": field.get("default", ""),
                    }
                    for field in template["fields"]
                ],
            }
        )
    return summaries


def _get_template(template_id: str) -> Dict[str, Any]:
    template = TEMPLATES.get(template_id)
    if template is None:
        raise KeyError(f"Unknown template '{template_id}'")
    return template


def render_template(template_id: str, fields: Dict[str, Any]) -> Tuple[str, str]:
    template = _get_template(template_id)
    missing: List[str] = []
    values: Dict[str, str] = {}

    for field in template["fields"]:
        key = field["key"]
        raw_value = fields.get(key) if isinstance(fields, dict) else None
        value = str(raw_value).strip() if raw_value is not None else ""
        if not value:
            default = field.get("default")
            value = str(default).strip() if default else ""
        if field.get("required") and not value:
            missing.append(field["label"])
        values[key] = value

    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(f"Missing required fields: {missing_list}")

    title = template["name"]
    body = template["body"].format(**values)
    lines = body.splitlines()
    if lines:
        first_line = lines[0].strip()
        if first_line and first_line.lower() == title.strip().lower():
            lines = lines[1:]
            if lines and not lines[0].strip():
                lines = lines[1:]
            body = "\n".join(lines)
    return title, body


def _contains_urdu(text: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", text or ""))


def render_html_document(title: str, content: str) -> str:
    safe_title = (title or "Document").strip()
    raw_content = (content or "").strip()
    escaped_content = html.escape(raw_content)
    safe_content = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped_content)
    body_font = "'Times New Roman', serif"
    if _contains_urdu(raw_content) or _contains_urdu(safe_title):
        body_font = "'Noto Nastaliq Urdu', 'Noto Naskh Arabic', serif"
    return (
        "<html><head><meta charset='utf-8'>"
        "<style>"
        "@import url('https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu:wght@400;600&display=swap');"
        f"body {{ font-family: {body_font}; padding: 32px; color: #1d1b16; }}"
        "h1 { font-size: 20px; letter-spacing: 0.04em; }"
        "pre { white-space: pre-wrap; font-size: 12.5px; line-height: 1.5; }"
        "</style></head><body>"
        f"<h1>{safe_title}</h1>"
        f"<pre>{safe_content}</pre>"
        "</body></html>"
    )


def render_pdf_from_html(html: str) -> bytes:
    try:
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Missing HTML-to-PDF renderer. Install weasyprint.") from exc

    return HTML(string=html).write_pdf()
