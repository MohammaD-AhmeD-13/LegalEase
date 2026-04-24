# LegalEase
AI-Powered Bilingual Legal Assistant (Urdu + English)

LegalEase is a LegalTech platform that simplifies legal documents using AI. It helps users understand, analyze, and generate legal content without needing expert knowledge.

🚀 Features
📄 Contract Analysis – Detect risky clauses and obligations
🧠 Summarization – Convert legal text into simple Urdu/English
🧾 Document Generation – Create NDAs, agreements, etc.
⚠️ Risk Detection – Highlight liabilities and missing clauses
👨‍⚖️ Expert Referral – Connect with legal professionals
🎙️ Voice-to-Text – Record from microphone and transcribe in English/Urdu

🧩 Tech Stack
Backend: Python (Flask/Django)
AI/NLP: Qwen 2.5, Hugging Face, spaCy
Frontend: HTML, CSS, JavaScript
Database: PostgreSQL
🎯 Goal

To make legal information accessible, affordable, and easy to understand for individuals and SMEs in Pakistan.

⚠️ Disclaimer

LegalEase provides AI-assisted guidance and does not replace professional legal advice.

## Voice Transcription Setup

The backend now exposes an authenticated endpoint: `POST /audio/transcribe`

- Accepts multipart form field `audio` and optional fields `input_language` (`auto|en|ur`) and `output_language` (`source|en|ur`)
- Requires logged-in user session cookie
- Uses Whisper (`openai-whisper`) and supports Urdu/English transcript output

### Requirements

1. Install dependencies from `requirements.txt` (includes `openai-whisper`).
2. Install FFmpeg and ensure it is available on your system `PATH` (Whisper depends on it).
3. Optional: set `WHISPER_MODEL` (default: `base`) before starting backend.

### Frontend Behavior

- `Voice` button starts microphone recording.
- Press again to stop recording and upload audio.
- Transcript is appended into the message composer.
- Basic MVP errors are shown for unsupported browser, mic permission denied, empty speech, and transcription failure.
