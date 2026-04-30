from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "CareerCopilot-AI API is running"}

@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    # PDF Parsing logic will go here
    return {"filename": file.filename, "status": "Resume received"}

@app.get("/api/match-jobs")
async def match_jobs(query: str):
    # JSearch and similarity logic will go here
    return {"query": query, "matches": []}
