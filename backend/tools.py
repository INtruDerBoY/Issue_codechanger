import difflib
import os
import subprocess
import time
import requests
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def get_llm_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Please set it in .env or environment.")
    return Groq(api_key=api_key)


def call_llm(system_prompt: str, user_prompt: str, json_mode: bool = True) -> tuple[str, int]:
    client = get_llm_client()
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_err = None
    for _ in range(3):
        try:
            resp = client.chat.completions.create(**kwargs)
            text = resp.choices[0].message.content or ""
            tokens = resp.usage.total_tokens if resp.usage else 0
            return text, tokens
        except Exception as e:
            last_err = e
            if "model_not_found" in str(e) or "does not exist" in str(e):
                kwargs["model"] = "openai/gpt-oss-120b"
            time.sleep(1)
    raise RuntimeError(f"LLM call failed after 2 retries: {last_err}")


# Ensure path stays within repo, is .py, and not a test file
def is_safe_rel_path(rel_path: str) -> bool:
    clean = rel_path.strip().replace("\\", "/")
    if clean.startswith("/") or ".." in clean.split("/"):
        return False
    if not clean.endswith(".py"):
        return False
    parts = clean.split("/")
    if any(p.startswith("test_") or p == "tests" or p == "hidden_test.py" for p in parts):
        return False
    return True


def list_repo_py_files(repo_path: str) -> list[str]:
    py_files = []
    for root, _, files in os.walk(repo_path):
        for f in files:
            if f.endswith(".py"):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, repo_path).replace("\\", "/")
                if is_safe_rel_path(rel):
                    py_files.append(rel)
    return sorted(py_files)


def read_repo_file(repo_path: str, rel_path: str) -> str:
    if not is_safe_rel_path(rel_path):
        raise ValueError(f"Unsafe file path: {rel_path}")
    full = os.path.join(repo_path, rel_path)
    if not os.path.exists(full):
        return ""
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def compute_diff(original_dir: str, patch: dict[str, str]) -> str:
    diff_lines = []
    for rel_path, new_content in patch.items():
        orig_file = os.path.join(original_dir, rel_path)
        orig_lines = []
        if os.path.exists(orig_file):
            with open(orig_file, "r", encoding="utf-8") as f:
                orig_lines = f.readlines()
        new_lines = [line + "\n" if not line.endswith("\n") else line for line in new_content.splitlines()]
        diff = difflib.unified_diff(
            orig_lines,
            new_lines,
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}"
        )
        diff_lines.extend(diff)
    return "".join(diff_lines)


DANGEROUS_TOKENS = ["os.system", "subprocess", "eval(", "exec(", "socket", "requests", "__import__"]


def check_patch_rules(patch: dict[str, str], diff: str) -> tuple[bool, str]:
    if len(patch) > 2:
        return False, "Patch touches more than 2 files."
    for rel_path, content in patch.items():
        if not is_safe_rel_path(rel_path):
            return False, f"Unsafe or test path touched: {rel_path}"
        for token in DANGEROUS_TOKENS:
            if token in content:
                return False, f"Dangerous pattern '{token}' detected in {rel_path}."
    changed = sum(1 for ln in diff.splitlines() if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---")))
    if changed > 40:
        return False, f"Patch too large ({changed} changed lines, maximum is 40)."
    return True, ""


def review_patch_llm(issue_title: str, issue_body: str, diff: str) -> tuple[bool, str, int]:
    import json
    sys_prompt = "You are a code reviewer. Answer: Does this change address the issue and nothing else? Return JSON: {\"ok\": true/false, \"reason\": \"short reason\"}."
    user_prompt = f"Issue: {issue_title}\n{issue_body}\n\nDiff:\n{diff}"
    raw_json, tokens = call_llm(sys_prompt, user_prompt, json_mode=True)
    data = json.loads(raw_json)
    return bool(data.get("ok", False)), data.get("reason", ""), tokens


# Push only to agent/ branches, never to main
def push_to_branch(workdir: str, branch: str, commit_msg: str) -> None:
    if not branch.startswith("agent/"):
        raise ValueError(f"Safety violation: cannot push to branch {branch}")
    subprocess.run(["git", "checkout", "-b", branch], cwd=workdir, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=workdir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=workdir, check=True, capture_output=True)
    last_err = ""
    for _ in range(3):
        res = subprocess.run(["git", "push", "origin", branch], cwd=workdir, capture_output=True, text=True)
        if res.returncode == 0:
            return
        last_err = res.stderr.strip()
        time.sleep(1)
    raise RuntimeError(f"Failed to push branch {branch}: {last_err}")


def create_github_pr(repo: str, branch: str, title: str, body: str) -> str:
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("GITHUB_TOKEN is not set in environment or .env.")
    clean_repo = repo.replace("https://github.com/", "").rstrip("/").removesuffix(".git")
    url = f"https://api.github.com/repos/{clean_repo}/pulls"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {"title": title, "body": body, "head": branch, "base": "main"}
    for _ in range(3):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code in [200, 201]:
                return resp.json().get("html_url", "")
            if resp.status_code == 422 and "already exists" in resp.text:
                return f"https://github.com/{clean_repo}/pulls"
        except Exception:
            time.sleep(1)
    raise RuntimeError("Failed to create GitHub PR after 2 retries.")


