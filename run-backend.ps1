Set-Location "D:\University\8th Semester\FYP-II\Project Files\LegalEase"
$env:DATABASE_URL="postgresql+psycopg2://postgres:legalease123@localhost:5432/legalease"
$env:LLM_ENABLED="1"
$env:LLM_PRELOAD="1"
$env:RAG_PRELOAD="1"
$env:LIBRETRANSLATE_URL="http://localhost:5000/translate"
C:/miniconda3/envs/legalease/python.exe -m uvicorn backend.app.main:app --reload --host localhost --port 8005
