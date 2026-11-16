import os
import shutil
import stat
import subprocess
import sys

SANDBOX_IMAGE = "issue-sandbox"


def check_docker() -> bool:
    try:
        res = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def format_docker_path(path: str) -> str:
    return os.path.abspath(path).replace("\\", "/")


def safe_rmtree(path: str) -> None:
    if not os.path.exists(path):
        return
    def _onerror(func, p, exc_info):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onerror=_onerror)


def copy_repo(src_path: str, dest_path: str) -> None:
    safe_rmtree(dest_path)
    clean_src = src_path.strip().strip("'\"")
    if clean_src.startswith("github.com/"):
        clean_src = "https://" + clean_src
    if clean_src.startswith(("http://", "https://", "git@")) or "github.com/" in clean_src:
        token = os.getenv("GITHUB_TOKEN", "")
        clone_url = clean_src
        if token and token != "your_github_token_here" and "github.com" in clean_src and "@" not in clean_src:
            clone_url = clean_src.replace("https://", f"https://x-access-token:{token}@")
        res = subprocess.run(["git", "clone", "--depth", "1", clone_url, dest_path], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to clone repository: {res.stderr.strip()}")
    else:
        norm = clean_src.replace("\\", "/")
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [clean_src, norm, os.path.join(root_dir, norm.lstrip("/"))]
        if "benchmark/bugs/" in norm:
            rel = norm[norm.index("benchmark/bugs/"):]
            candidates.extend([rel, os.path.join(root_dir, rel)])
        found = next((c for c in candidates if os.path.exists(c)), None)
        if not found:
            raise FileNotFoundError(f"Local repo path not found: {clean_src}")
        shutil.copytree(found, dest_path)


def apply_patch(workdir: str, patch: dict[str, str]) -> None:
    for rel_path, content in patch.items():
        full_path = os.path.join(workdir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)


def trim_output(output: str, max_lines: int = 60) -> str:
    lines = output.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[-max_lines:])
    return output


def run_pytest(workdir: str, timeout: int = 60) -> tuple[int, str]:
    if check_docker():
        mounted = format_docker_path(workdir)
        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "512m",
            "--cpus", "1",
            "--pids-limit", "128",
            "-v", f"{mounted}:/repo",
            "-w", "/repo",
            SANDBOX_IMAGE,
            "pytest", "-x", "-q", "-o", "cache_dir=/tmp/.pytest_cache"
        ]
        cwd = None
    else:
        cmd = [sys.executable, "-m", "pytest", "-x", "-q", "-o", "cache_dir=/tmp/.pytest_cache"]
        cwd = workdir
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        combined = proc.stdout + proc.stderr
        if proc.returncode == 5:
            return 5, "No pytest tests found in repository (Python + pytest required)."
        return proc.returncode, trim_output(combined)
    except subprocess.TimeoutExpired:
        return 124, "Tests timed out after 60 seconds."

