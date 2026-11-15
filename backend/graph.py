import json
import sqlite3
import tempfile
import time
from typing import TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

from backend.sandbox import copy_repo, apply_patch, run_pytest
from backend.tools import (
    call_llm,
    is_safe_rel_path,
    list_repo_py_files,
    read_repo_file,
    compute_diff,
    check_patch_rules,
    review_patch_llm,
    push_to_branch,
    create_github_pr,
)


class AgentState(TypedDict, total=False):
    run_id: str; repo_path: str; workdir: str; orig_dir: str; mode: str
    issue_title: str; issue_body: str; baseline_output: str
    plan: str; files_to_edit: list[str]; patch: dict[str, str]; diff: str
    test_passed: bool; test_output: str; attempts: int; max_attempts: int
    review_ok: bool; review_notes: str; approval: str; reviewer_note: str
    pr_url: str; status: str; error: str; tokens_used: int; started_at: float


def prepare_node(state: AgentState) -> dict:
    repo_path = state["repo_path"]
    orig_dir = tempfile.mkdtemp(prefix="issue_orig_")
    copy_repo(repo_path, orig_dir)
    workdir = tempfile.mkdtemp(prefix="issue_run_")
    copy_repo(orig_dir, workdir)
    code, output = run_pytest(workdir)
    if code == 5:
        return {"orig_dir": orig_dir, "workdir": workdir, "status": "failed", "error": output, "baseline_output": output}
    if code == 0:
        return {"orig_dir": orig_dir, "workdir": workdir, "status": "no_failing_test", "baseline_output": output}
    return {
        "orig_dir": orig_dir,
        "workdir": workdir,
        "status": "running",
        "baseline_output": output,
        "attempts": 0,
        "max_attempts": state.get("max_attempts", 3),
        "tokens_used": 0,
        "started_at": time.time(),
    }


def plan_node(state: AgentState) -> dict:
    files = list_repo_py_files(state["workdir"])
    sys_prompt = "You are an autonomous bug fixing planner. Reply only with JSON: {\"files\": [\"path\"], \"plan\": \"one sentence\"}."
    user_prompt = f"Issue: {state.get('issue_title', '')}\n{state.get('issue_body', '')}\nFiles:\n" + "\n".join(files) + f"\nTest Failure:\n{state.get('baseline_output', '')}\n"
    raw_json, tokens = call_llm(sys_prompt, user_prompt, json_mode=True)
    data = json.loads(raw_json)
    chosen = [f for f in data.get("files", []) if is_safe_rel_path(f)][:3]
    return {"plan": data.get("plan", ""), "files_to_edit": chosen, "tokens_used": state.get("tokens_used", 0) + tokens}


def code_node(state: AgentState) -> dict:
    attempts = state.get("attempts", 0) + 1
    file_contents = "".join(f"\n--- {f} ---\n{read_repo_file(state['workdir'], f)}\n" for f in state.get("files_to_edit", []))
    sys_prompt = "Autonomous bug fixer. JSON only: {'changes': [{'path': '...', 'new_content': '...'}], 'explanation': '...'}. Max 2 files. No test edits."
    user_prompt = f"Issue: {state.get('issue_title', '')}\nPlan: {state.get('plan', '')}\nFiles:\n{file_contents}\nFailure:\n{state.get('baseline_output', '')}\n"
    if state.get("test_output") and attempts > 1:
        user_prompt += f"\nPrevious patch failed:\n{json.dumps(state.get('patch', {}))}\nTest error:\n{state.get('test_output')}\n"
    if state.get("review_notes") and not state.get("review_ok", True):
        user_prompt += f"\nReviewer rejection:\n{state.get('review_notes')}\n"

    raw_json, tokens = call_llm(sys_prompt, user_prompt, json_mode=True)
    data = json.loads(raw_json)
    patch = {item.get("path", ""): item.get("new_content", "") for item in data.get("changes", [])[:2] if is_safe_rel_path(item.get("path", ""))}
    return {"attempts": attempts, "patch": patch, "tokens_used": state.get("tokens_used", 0) + tokens}


def test_node(state: AgentState) -> dict:
    patch = state.get("patch", {})
    workdir = state["workdir"]
    base_dir = state.get("orig_dir", state["repo_path"])
    copy_repo(base_dir, workdir)
    apply_patch(workdir, patch)
    diff = compute_diff(base_dir, patch)
    code, output = run_pytest(workdir)
    return {"diff": diff, "test_passed": (code == 0), "test_output": output}


def review_node(state: AgentState) -> dict:
    patch = state.get("patch", {})
    diff = state.get("diff", "")
    ok, rule_err = check_patch_rules(patch, diff)
    if not ok:
        return {"review_ok": False, "review_notes": f"Rule rejection: {rule_err}"}
    llm_ok, reason, tokens = review_patch_llm(state.get("issue_title", ""), state.get("issue_body", ""), diff)
    return {"review_ok": llm_ok, "review_notes": reason, "tokens_used": state.get("tokens_used", 0) + tokens}


def approval_node(state: AgentState) -> dict:
    decision_data = interrupt({"run_id": state.get("run_id"), "diff": state.get("diff"), "attempts": state.get("attempts")})
    decision = decision_data.get("decision", "approved") if isinstance(decision_data, dict) else str(decision_data)
    note = decision_data.get("note", "") if isinstance(decision_data, dict) else ""
    return {"approval": decision, "reviewer_note": note, "status": "approved" if decision == "approved" else "rejected"}


# Create branch, commit, push, and open PR via GitHub API
def open_pr_node(state: AgentState) -> dict:
    branch = f"agent/issue-{state.get('run_id', 'bug')}"
    commit_msg = f"Fix: {state.get('issue_title', 'Resolved bug')}"
    body = f"Autonomous bug fix by Issue-to-PR Agent\n\n- Attempts: {state.get('attempts', 1)}\n- Status: PASSED\n\n```diff\n{state.get('diff', '')}\n```"
    push_to_branch(state["workdir"], branch, commit_msg)
    url = create_github_pr(state["repo_path"], branch, f"Fix: {state.get('issue_title', '')}", body)
    return {"pr_url": url, "status": "pr_opened"}


def finish_node(state: AgentState) -> dict:
    if state.get("status") in ["no_failing_test", "approved", "rejected", "pr_opened"]:
        return {}
    return {"status": "approved" if state.get("approval") == "approved" else "failed"}


def route_after_prepare(state: AgentState) -> str:
    return "finish" if state.get("status") in ["no_failing_test", "failed"] else "plan"


def route_after_test(state: AgentState) -> str:
    if state.get("test_passed"):
        return "review"
    return "code" if state.get("attempts", 0) < state.get("max_attempts", 3) else "finish"


def route_after_review(state: AgentState) -> str:
    if state.get("review_ok"):
        return "approval"
    return "code" if state.get("attempts", 0) < state.get("max_attempts", 3) else "finish"


def route_after_approval(state: AgentState) -> str:
    if state.get("approval") == "approved":
        return "open_pr" if state.get("mode") == "github" else "finish"
    return "finish"


def get_checkpointer(db_path: str = "checkpoints.sqlite") -> SqliteSaver:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SqliteSaver(conn)


def build_graph(checkpointer: SqliteSaver | None = None):
    builder = StateGraph(AgentState)
    builder.add_node("prepare", prepare_node)
    builder.add_node("plan", plan_node)
    builder.add_node("code", code_node)
    builder.add_node("test", test_node)
    builder.add_node("review", review_node)
    builder.add_node("approval", approval_node)
    builder.add_node("open_pr", open_pr_node)
    builder.add_node("finish", finish_node)

    builder.add_edge(START, "prepare")
    builder.add_conditional_edges("prepare", route_after_prepare, {"finish": "finish", "plan": "plan"})
    builder.add_edge("plan", "code")
    builder.add_edge("code", "test")
    builder.add_conditional_edges("test", route_after_test, {"review": "review", "code": "code", "finish": "finish"})
    builder.add_conditional_edges("review", route_after_review, {"approval": "approval", "code": "code", "finish": "finish"})
    builder.add_conditional_edges("approval", route_after_approval, {"open_pr": "open_pr", "finish": "finish"})
    builder.add_edge("open_pr", "finish")
    builder.add_edge("finish", END)

    return builder.compile(checkpointer=checkpointer)


def resume_run(run_id: str, decision: str, note: str = "", db_path: str = "checkpoints.sqlite") -> dict:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    saver = SqliteSaver(conn)
    app = build_graph(checkpointer=saver)
    try:
        return app.invoke(Command(resume={"decision": decision, "note": note}), config={"configurable": {"thread_id": run_id}})
    finally:
        conn.close()
