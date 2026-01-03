from fastapi import FastAPI

app = FastAPI(title="LegalEase")

@app.get("/")
def root():
    return {"status": "LegalEase backend running"}