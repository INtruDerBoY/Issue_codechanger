import time
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.db import create_run_record, update_run_record, get_run, list_runs
from backend.graph import build_graph, get_checkpointer, resume_run

app = FastAPI(title="Issue-to-PR Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunCreate(BaseModel):
    repo: str = Field(..., min_length=1, max_length=500)
    issue_title: str = Field(..., min_length=1, max_length=200)
    issue_body: str = Field(..., min_length=1, max_length=5000)
    mode: str = Field("local", max_length=20)


class DecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    note: Optional[str] = Field("", max_length=500)


@app.post("/runs")
def create_run(req: RunCreate):
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    start_t = time.time()
    clean_repo = req.repo.strip().strip("'\"")
    create_run_record(run_id, clean_repo, req.issue_title, req.issue_body)
    checkpointer = get_checkpointer()
    graph = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": run_id}}
    initial_state = {
        "run_id": run_id,
        "repo_path": clean_repo,
        "issue_title": req.issue_title,
        "issue_body": req.issue_body,
        "mode": req.mode,
    }
    try:
        res = graph.invoke(initial_state, config=config)
        dur = round(time.time() - start_t, 2)
        status = "awaiting_approval" if "__interrupt__" in res else res.get("status", "unknown")
        update_run_record(
            run_id,
            status=status,
            attempts=res.get("attempts", 0),
            diff=res.get("diff", ""),
            test_output=res.get("test_output", "") or res.get("baseline_output", "") or res.get("error", ""),
            review_notes=res.get("review_notes", "") or res.get("error", ""),
            tokens_used=res.get("tokens_used", 0),
            duration_seconds=dur,
        )
        return get_run(run_id)
    except Exception as e:
        dur = round(time.time() - start_t, 2)
        update_run_record(run_id, status="failed", duration_seconds=dur)
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/runs")
def get_runs_list():
    return list_runs()


@app.get("/runs/{run_id}")
def get_run_detail(run_id: str):
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    return record


@app.post("/runs/{run_id}/decision")
def submit_decision(run_id: str, req: DecisionRequest):
    record = get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Run not found")
    try:
        res = resume_run(run_id, req.decision, req.note or "")
        status = res.get("status", "unknown")
        notes = f"{record.get('review_notes', '')}\nDecision note: {req.note}".strip()
        update_run_record(run_id, status=status, review_notes=notes, pr_url=res.get("pr_url", record.get("pr_url", "")))
        return get_run(run_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to resume run: {str(e)}")
