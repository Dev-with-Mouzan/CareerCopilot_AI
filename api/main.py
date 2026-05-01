import io
import os
import sys
import uuid
import asyncio
from typing import Optional
from datetime import datetime

import PyPDF2
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()


_SRC = os.path.join(os.path.dirname(__file__), "..", "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


app = FastAPI(
    title="CareerCopilot-AI API",
    description="Agentic job matching and career coaching backend.",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Replace "*" with your Vercel URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)


_session: dict = {
    "resume_text": "",
    "chat_history": [],   
    "job_results": None,  
    "raw_jobs_md": "",    
}


_pipeline_jobs: dict = {}


def _extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    """Extract plain text from in-memory PDF bytes (no temp file needed)."""
    text = ""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to parse PDF: {exc}")
    return text.strip()


def _build_coach_prompt(user_message: str, resume_text: str, history: list) -> str:
    """Build a prompt that gives the coach memory of previous messages."""
    lines = [
        "You are an expert career coach. You have access to the user's resume.",
        "",
        f"RESUME:\n{resume_text[:3000]}", 
        "",
    ]
    if history:
        lines.append("CONVERSATION SO FAR:")
        for turn in history[-6:]:          
            role = "User" if turn["role"] == "user" else "Coach"
            lines.append(f"{role}: {turn['content']}")
        lines.append("")
    lines.append(f"Now answer this new message from the user:\nUser: {user_message}")
    return "\n".join(lines)




def _run_pipeline_sync(job_id: str, resume_text: str, websites: str, user_query: str):
    """
    Runs the full CrewAI pipeline synchronously in a background thread.
    Updates _pipeline_jobs[job_id] on completion or failure.
    """
    try:
        from career_copilot_ai.crew import CareerCopilotAi

        inputs = {
            "resume": resume_text,
            "websites": websites,
            "user_query": user_query,
        }

        result = CareerCopilotAi().crew().kickoff(inputs=inputs)

        
        _session["job_results"] = result.pydantic
        _session["raw_jobs_md"] = result.raw

        _pipeline_jobs[job_id] = {
            "status": "done",
            "result": {
                "raw": result.raw,
                "jobs": result.pydantic.model_dump() if result.pydantic else None,
            },
            "error": None,
            "completed_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        _pipeline_jobs[job_id] = {
            "status": "failed",
            "result": None,
            "error": str(exc),
            "completed_at": datetime.utcnow().isoformat(),
        }



class RunCrewRequest(BaseModel):
    user_query: Optional[str] = "What are the best job matches for me based on my resume?"
    websites: Optional[str] = (
        "https://www.workingnomads.com/jobs\n"
        "https://www.flexjobs.com/remote-jobs#remote-jobs-list"
    )

class ChatRequest(BaseModel):
    message: str
    resume_text: Optional[str] = None   



@app.get("/api/health", tags=["General"])
def health_check():
    """Quick health check — confirms API is alive."""
    return {
        "status": "ok",
        "service": "CareerCopilot-AI",
        "resume_loaded": bool(_session["resume_text"]),
        "jobs_available": _session["job_results"] is not None,
    }


@app.post("/api/upload-resume", tags=["Resume"])
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a PDF resume.
    Extracts text, stores it in the session, and returns a preview.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:   # 10 MB limit
        raise HTTPException(status_code=400, detail="File too large. Max size is 10 MB.")

    resume_text = _extract_text_from_pdf_bytes(file_bytes)

    if not resume_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from PDF. Please ensure it is not scanned/image-only.",
        )

    _session["resume_text"] = resume_text
    _session["chat_history"] = []      

    return {
        "status": "success",
        "filename": file.filename,
        "characters_extracted": len(resume_text),
        "preview": resume_text[:300] + "..." if len(resume_text) > 300 else resume_text,
    }


@app.post("/api/run-crew", tags=["Pipeline"])
async def run_crew(request: RunCrewRequest, background_tasks: BackgroundTasks):
    """
    Starts the full agentic pipeline in the background:
      job_scraper → ats_scorer → career_coach (initial advice)

    Returns a job_id immediately. Poll /api/status/{job_id} for results.
    The pipeline typically takes 2–5 minutes.
    """
    if not _session["resume_text"]:
        raise HTTPException(
            status_code=400,
            detail="No resume found. Please upload a resume first via /api/upload-resume.",
        )

    job_id = str(uuid.uuid4())
    _pipeline_jobs[job_id] = {
        "status": "running",
        "result": None,
        "error": None,
        "started_at": datetime.utcnow().isoformat(),
    }

    background_tasks.add_task(
        _run_pipeline_sync,
        job_id,
        _session["resume_text"],
        request.websites,
        request.user_query,
    )

    return {
        "status": "started",
        "job_id": job_id,
        "message": "Pipeline started. Poll /api/status/{job_id} for results.",
        "estimated_time": "2-5 minutes",
    }


@app.get("/api/status/{job_id}", tags=["Pipeline"])
def get_status(job_id: str):
    """
    Poll the status of a background pipeline job.
    Status values: 'running' | 'done' | 'failed'
    """
    if job_id not in _pipeline_jobs:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    job = _pipeline_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job.get("result"),
        "error": job.get("error"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
    }


@app.get("/api/jobs", tags=["Jobs"])
def get_jobs():
    """
    Returns the latest job matching results from the most recent pipeline run.
    Returns 404 if no pipeline has been run yet.
    """
    if _session["job_results"] is None and not _session["raw_jobs_md"]:
        raise HTTPException(
            status_code=404,
            detail="No job results yet. Run the pipeline first via /api/run-crew.",
        )

    result = {}
    if _session["raw_jobs_md"]:
        result["raw_markdown"] = _session["raw_jobs_md"]
    if _session["job_results"]:
        try:
            result["jobs"] = _session["job_results"].model_dump()
        except Exception:
            result["jobs"] = str(_session["job_results"])

    return result



@app.post("/api/chat", tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Chat with the Career Coach agent (powered by Gemini).
    The coach has memory of the last 3 exchanges and knows the user's resume.
    It can also query the saved job chunks (VectorDBQueryTool).
    """
    
    resume_text = request.resume_text or _session["resume_text"]
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No resume available. Upload a resume first or pass resume_text in the request.",
        )

    history = _session["chat_history"]
    prompt = _build_coach_prompt(request.message, resume_text, history)

    try:
        from career_copilot_ai.crew import CareerCopilotAi

        crew_instance = CareerCopilotAi()
        coach_agent = crew_instance.career_coach()

        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, coach_agent.kickoff, prompt)
        reply = result.raw

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Career coach error: {str(exc)}")

    
    _session["chat_history"].append({"role": "user", "content": request.message})
    _session["chat_history"].append({"role": "coach", "content": reply})

    
    if len(_session["chat_history"]) > 20:
        _session["chat_history"] = _session["chat_history"][-20:]

    return {
        "reply": reply,
        "history_length": len(_session["chat_history"]),
    }


@app.delete("/api/session", tags=["General"])
def clear_session():
    """
    Clears all stored data: resume text, chat history, job results.
    Useful when a user wants to start fresh with a new resume.
    """
    _session["resume_text"] = ""
    _session["chat_history"] = []
    _session["job_results"] = None
    _session["raw_jobs_md"] = ""
    _pipeline_jobs.clear()

    return {"status": "success", "message": "Session cleared."}
