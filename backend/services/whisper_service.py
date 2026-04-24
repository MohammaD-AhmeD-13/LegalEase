import asyncio
import os
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Optional


_TRANSCRIBE_POOL = ThreadPoolExecutor(max_workers=1)


def _ensure_ffmpeg_available() -> None:
    if shutil.which("ffmpeg"):
        return
    try:
        import imageio_ffmpeg

        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "FFmpeg is required for transcription. Install ffmpeg or imageio-ffmpeg."
        ) from exc

    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    path_parts = os.getenv("PATH", "").split(os.pathsep)
    if ffmpeg_dir not in path_parts:
        os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}{os.getenv('PATH', '')}"

    # Windows imageio binaries are versioned (not literally ffmpeg.exe).
    # Create an executable shim so subprocess calls to "ffmpeg" can resolve.
    if os.name == "nt" and shutil.which("ffmpeg") is None:
        shim_dir = os.path.join(tempfile.gettempdir(), "legalease_ffmpeg")
        os.makedirs(shim_dir, exist_ok=True)
        shim_path = os.path.join(shim_dir, "ffmpeg.exe")
        if not os.path.exists(shim_path):
            shutil.copyfile(ffmpeg_exe, shim_path)

        path_parts = os.getenv("PATH", "").split(os.pathsep)
        if shim_dir not in path_parts:
            os.environ["PATH"] = f"{shim_dir}{os.pathsep}{os.getenv('PATH', '')}"

    # Some ffmpeg wrappers honor this variable explicitly.
    os.environ.setdefault("FFMPEG_BINARY", ffmpeg_exe)

    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg executable could not be resolved for Whisper transcription.")


class WhisperService:
    def __init__(self, model_name: Optional[str] = None) -> None:
        _ensure_ffmpeg_available()
        try:
            import whisper
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Whisper dependency is missing. Install openai-whisper and ensure ffmpeg is available."
            ) from exc

        self._whisper = whisper
        self.model_name = model_name or os.getenv("WHISPER_MODEL", "base")
        self.model = whisper.load_model(self.model_name)

    def transcribe_sync(self, audio_bytes: bytes, input_language: str = "auto") -> dict:
        if not audio_bytes:
            raise ValueError("Audio content is empty")

        suffix = os.getenv("WHISPER_UPLOAD_SUFFIX", ".webm")
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        try:
            kwargs = {"fp16": False}
            if input_language in {"en", "ur"}:
                kwargs["language"] = input_language
            result = self.model.transcribe(temp_path, **kwargs)
            text = str(result.get("text", "")).strip()
            detected_language = str(result.get("language", "")).strip().lower() or "unknown"
            return {"text": text, "detected_language": detected_language}
        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    async def transcribe(self, audio_bytes: bytes, input_language: str = "auto") -> dict:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_TRANSCRIBE_POOL, self.transcribe_sync, audio_bytes, input_language)


_whisper_service: Optional[WhisperService] = None


def get_whisper_service() -> WhisperService:
    global _whisper_service
    if _whisper_service is None:
        _whisper_service = WhisperService()
    return _whisper_service
