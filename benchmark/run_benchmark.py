import json
import os
import subprocess
import time

from backend.graph import build_graph, resume_run, get_checkpointer
from backend.sandbox import check_docker, format_docker_path, SANDBOX_IMAGE

BUGS_DIR = os.path.join(os.path.dirname(__file__), "bugs")


def run_hidden_test(workdir: str) -> bool:
    # Run hidden test in Docker container to evaluate general fix quality
    mounted = format_docker_path(workdir)
    cmd = [
        "docker", "run", "--rm", "--network", "none",
        "--memory", "512m", "--cpus", "1",
        "-v", f"{mounted}:/repo", "-w", "/repo",
        SANDBOX_IMAGE, "pytest", "-q", "hidden_test.py", "-o", "cache_dir=/tmp/.pytest_cache"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return res.returncode == 0


def run_single_bug(bug_name: str) -> dict:
    bug_path = os.path.join(BUGS_DIR, bug_name)
    issue_file = os.path.join(bug_path, "issue.json")
    with open(issue_file, "r", encoding="utf-8") as f:
        issue = json.load(f)

    saver = get_checkpointer()
    graph = build_graph(checkpointer=saver)
    run_id = f"bench_{bug_name}_{int(time.time())}"
    config = {"configurable": {"thread_id": run_id}}
    start_t = time.time()
    res = graph.invoke({
        "run_id": run_id,
        "repo_path": bug_path,
        "issue_title": issue.get("title", ""),
        "issue_body": issue.get("body", ""),
    }, config=config)

    # Auto-approve if paused at interrupt
    if "__interrupt__" in res:
        res = resume_run(run_id, "approved")

    dur = round(time.time() - start_t, 2)
    workdir = res.get("workdir", "")
    vis_pass = bool(res.get("test_passed", False))
    hid_pass = run_hidden_test(workdir) if vis_pass and os.path.exists(workdir) else False

    reason = ""
    if not vis_pass:
        reason = f"Visible tests failed after {res.get('attempts', 0)} attempts"
    elif not hid_pass:
        reason = "Passed visible test but failed hidden evaluation tests"

    return {
        "bug": bug_name,
        "vis_pass": vis_pass,
        "hid_pass": hid_pass,
        "attempts": res.get("attempts", 0),
        "tokens": res.get("tokens_used", 0),
        "time": dur,
        "rejected": not res.get("review_ok", True),
        "reason": reason,
    }


def print_summary(results: list[dict]) -> None:
    n = len(results)
    vis_count = sum(1 for r in results if r["vis_pass"])
    hid_count = sum(1 for r in results if r["hid_pass"])
    avg_attempts = round(sum(r["attempts"] for r in results) / n, 2) if n else 0
    avg_time = round(sum(r["time"] for r in results) / n, 2) if n else 0
    avg_tokens = round(sum(r["tokens"] for r in results) / n, 2) if n else 0
    total_rejections = sum(1 for r in results if r["rejected"])

    print("\n================ BENCHMARK RESULTS ================")
    print(f"1. Visible test success rate: {vis_count}/{n} ({round(vis_count/n*100, 1)}%)")
    print(f"2. Hidden test success rate:  {hid_count}/{n} ({round(hid_count/n*100, 1)}%)")
    print(f"3. Average attempts per run: {avg_attempts}")
    print(f"4. Average time per run:     {avg_time}s | Average tokens: {avg_tokens}")
    print(f"5. Patches rejected:         {total_rejections}")
    print("\n6. Unsolved bug reasons:")
    for r in results:
        if not r["hid_pass"]:
            print(f"   - {r['bug']}: {r['reason']}")
    print("===================================================\n")


def main():
    check_docker()
    bugs = sorted(os.listdir(BUGS_DIR))
    print(f"Running benchmark across {len(bugs)} seeded bugs...")
    results = []
    for bug in bugs:
        print(f"-> Testing {bug}...")
        res = run_single_bug(bug)
        print(f"   Result: visible={'PASS' if res['vis_pass'] else 'FAIL'}, hidden={'PASS' if res['hid_pass'] else 'FAIL'}")
        results.append(res)
    print_summary(results)


if __name__ == "__main__":
    main()

