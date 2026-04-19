import json
import os
import urllib.request
from typing import Optional


_DEFAULT_ENDPOINT = "https://libretranslate.de/translate"


def _normalize_endpoint(value: str) -> str:
    endpoint = (value or "").strip()
    if not endpoint:
        return _DEFAULT_ENDPOINT
    if endpoint.endswith("/"):
        endpoint = endpoint[:-1]
    if not endpoint.endswith("/translate"):
        endpoint = f"{endpoint}/translate"
    return endpoint


def _contains_urdu(text: str) -> bool:
    return bool(text and any("\u0600" <= char <= "\u06FF" for char in text))


def _post_translate(text: str, source: str, target: str, endpoint: str, timeout: int) -> Optional[str]:
    payload = {
        "q": text,
        "source": source,
        "target": target,
        "format": "text",
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        result = json.loads(body)
    translated = result.get("translatedText")
    return translated.strip() if isinstance(translated, str) else None


def translate_text(text: str, source: str, target: str, timeout: int = 20) -> str:
    cleaned = (text or "").strip()
    if not cleaned or source == target:
        return cleaned

    endpoint = _normalize_endpoint(os.getenv("LIBRETRANSLATE_URL", _DEFAULT_ENDPOINT))
    translated = None

    try:
        translated = _post_translate(cleaned, source, target, endpoint, timeout)
    except Exception:
        translated = None

    if translated is None:
        try:
            translated = _post_translate(cleaned, "auto", target, endpoint, timeout)
        except Exception:
            translated = None

    if translated is None:
        return cleaned

    if target == "ur" and not _contains_urdu(translated):
        return cleaned

    return translated


def translate_to_urdu(text: str) -> str:
    return translate_text(text, "en", "ur")


def translate_to_english(text: str) -> str:
    return translate_text(text, "auto", "en")
