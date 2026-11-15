import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function App() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [form, setForm] = useState({ repo: "", issue_title: "", issue_body: "", mode: "local" });
  const [decisionNote, setDecisionNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchRuns = async () => {
    try {
      const res = await fetch(`${API_BASE}/runs`);
      if (res.ok) {
        const data = await res.json();
        setRuns(data);
      }
    } catch (e) {
      console.error("Failed to load runs", e);
    }
  };

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  const selectRun = async (id) => {
    setError("");
    try {
      const res = await fetch(`${API_BASE}/runs/${id}`);
      if (res.ok) setSelectedRun(await res.json());
    } catch (e) {
      setError("Failed to fetch run details.");
    }
  };

  const handleStartRun = async (e) => {
    e.preventDefault();
    if (!form.repo || !form.issue_title || !form.issue_body) {
      setError("All fields are required.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form)
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to start run");
      const created = await res.json();
      setSelectedRun(created);
      fetchRuns();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision) => {
    if (!selectedRun) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/runs/${selectedRun.id}/decision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, note: decisionNote })
      });
      if (!res.ok) throw new Error((await res.json()).detail || "Failed to submit decision");
      const updated = await res.json();
      setSelectedRun(updated);
      setDecisionNote("");
      fetchRuns();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderDiff = (diffText) => {
    if (!diffText) return <p style={{ color: "#666" }}>No diff generated.</p>;
    return (
      <pre style={{ background: "#f8f9fa", padding: "12px", borderRadius: "6px", overflowX: "auto", fontSize: "13px", lineHeight: "1.4" }}>
        {diffText.split("\n").map((line, idx) => {
          let style = { padding: "2px 4px", display: "block" };
          if (line.startsWith("+") && !line.startsWith("+++")) {
            style.backgroundColor = "#e6ffed";
            style.color = "#22863a";
          } else if (line.startsWith("-") && !line.startsWith("---")) {
            style.backgroundColor = "#ffeef0";
            style.color = "#cb2431";
          } else if (line.startsWith("@")) {
            style.backgroundColor = "#f1f8ff";
            style.color = "#0366d6";
          }
          return <span key={idx} style={style}>{line || " "}</span>;
        })}
      </pre>
    );
  };

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, sans-serif", maxWidth: "1200px", margin: "0 auto", padding: "24px", color: "#1f2328" }}>
      <header style={{ borderBottom: "1px solid #d0d7de", paddingBottom: "16px", marginBottom: "24px" }}>
        <h1 style={{ margin: "0 0 6px 0", fontSize: "24px" }}>Issue-to-PR Agent</h1>
        <p style={{ margin: 0, color: "#656d76", fontSize: "14px" }}>Autonomous Bug-Fix Agent with Human Approval</p>
      </header>

      {error && (
        <div style={{ background: "#ffebe9", border: "1px solid #ff8182", color: "#cf222e", padding: "10px 14px", borderRadius: "6px", marginBottom: "16px" }}>
          {error}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: "24px" }}>
        {/* Left Column: Start Run & Runs List */}
        <div>
          <div style={{ border: "1px solid #d0d7de", borderRadius: "6px", padding: "16px", marginBottom: "20px", background: "#f6f8fa" }}>
            <h3 style={{ margin: "0 0 12px 0", fontSize: "16px" }}>Start New Run</h3>
            <form onSubmit={handleStartRun}>
              <div style={{ marginBottom: "10px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>Repository (Path or URL)</label>
                <input
                  type="text"
                  placeholder="e.g. benchmark/bugs/bug1_off_by_one"
                  value={form.repo}
                  onChange={(e) => setForm({ ...form, repo: e.target.value })}
                  style={{ width: "100%", padding: "6px 8px", border: "1px solid #d0d7de", borderRadius: "4px", boxSizing: "border-box" }}
                />
              </div>
              <div style={{ marginBottom: "10px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>Issue Title</label>
                <input
                  type="text"
                  placeholder="e.g. Pagination off-by-one error"
                  value={form.issue_title}
                  onChange={(e) => setForm({ ...form, issue_title: e.target.value })}
                  style={{ width: "100%", padding: "6px 8px", border: "1px solid #d0d7de", borderRadius: "4px", boxSizing: "border-box" }}
                />
              </div>
              <div style={{ marginBottom: "10px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>Issue Body</label>
                <textarea
                  rows="3"
                  placeholder="Describe the bug behavior..."
                  value={form.issue_body}
                  onChange={(e) => setForm({ ...form, issue_body: e.target.value })}
                  style={{ width: "100%", padding: "6px 8px", border: "1px solid #d0d7de", borderRadius: "4px", boxSizing: "border-box", fontFamily: "inherit" }}
                />
              </div>
              <div style={{ marginBottom: "12px" }}>
                <label style={{ display: "block", fontSize: "12px", fontWeight: "600", marginBottom: "4px" }}>Mode</label>
                <select
                  value={form.mode}
                  onChange={(e) => setForm({ ...form, mode: e.target.value })}
                  style={{ width: "100%", padding: "6px 8px", border: "1px solid #d0d7de", borderRadius: "4px" }}
                >
                  <option value="local">Local (Benchmark / Sandbox only)</option>
                  <option value="github">GitHub (Branch & Pull Request)</option>
                </select>
              </div>
              <button
                type="submit"
                disabled={loading}
                style={{ width: "100%", padding: "8px", background: "#1f883d", color: "#fff", border: "none", borderRadius: "6px", fontWeight: "600", cursor: loading ? "not-allowed" : "pointer" }}
              >
                {loading ? "Processing..." : "Submit Run"}
              </button>
            </form>
          </div>

          <div style={{ border: "1px solid #d0d7de", borderRadius: "6px", background: "#fff" }}>
            <div style={{ padding: "10px 14px", borderBottom: "1px solid #d0d7de", background: "#f6f8fa", fontWeight: "600", fontSize: "14px" }}>
              Run History ({runs.length})
            </div>
            <div style={{ maxHeight: "420px", overflowY: "auto" }}>
              {runs.length === 0 ? (
                <div style={{ padding: "16px", color: "#656d76", textAlign: "center", fontSize: "13px" }}>No runs recorded yet.</div>
              ) : (
                runs.map((r) => (
                  <div
                    key={r.id}
                    onClick={() => selectRun(r.id)}
                    style={{
                      padding: "10px 14px",
                      borderBottom: "1px solid #f0f2f5",
                      cursor: "pointer",
                      background: selectedRun && selectedRun.id === r.id ? "#f3f4f6" : "#fff"
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                      <span style={{ fontWeight: "600", fontSize: "13px" }}>{r.id}</span>
                      <span style={{
                        fontSize: "11px",
                        padding: "2px 6px",
                        borderRadius: "10px",
                        fontWeight: "600",
                        background: r.status === "approved" || r.status === "pr_opened" ? "#dafbe1" : r.status === "awaiting_approval" ? "#fff8c5" : "#ffebe9",
                        color: r.status === "approved" || r.status === "pr_opened" ? "#1a7f37" : r.status === "awaiting_approval" ? "#9a6700" : "#cf222e"
                      }}>
                        {r.status}
                      </span>
                    </div>
                    <div style={{ fontSize: "12px", color: "#656d76", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {r.issue_title}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Run Detail View */}
        <div>
          {selectedRun ? (
            <div style={{ border: "1px solid #d0d7de", borderRadius: "6px", padding: "20px", background: "#fff" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                <div>
                  <h2 style={{ margin: "0 0 6px 0", fontSize: "20px" }}>{selectedRun.issue_title}</h2>
                  <div style={{ fontSize: "13px", color: "#656d76" }}>Run: <code>{selectedRun.id}</code> | Repo: <code>{selectedRun.repo}</code></div>
                </div>
                <span style={{
                  fontSize: "13px",
                  padding: "4px 10px",
                  borderRadius: "12px",
                  fontWeight: "600",
                  background: selectedRun.status === "approved" || selectedRun.status === "pr_opened" ? "#dafbe1" : selectedRun.status === "awaiting_approval" ? "#fff8c5" : "#ffebe9",
                  color: selectedRun.status === "approved" || selectedRun.status === "pr_opened" ? "#1a7f37" : selectedRun.status === "awaiting_approval" ? "#9a6700" : "#cf222e"
                }}>
                  {selectedRun.status}
                </span>
              </div>

              {/* Stats Bar */}
              <div style={{ display: "flex", gap: "16px", background: "#f6f8fa", padding: "10px 14px", borderRadius: "6px", marginBottom: "16px", fontSize: "13px" }}>
                <div><strong>Attempts:</strong> {selectedRun.attempts || 0} / 3</div>
                <div><strong>Tokens:</strong> {selectedRun.tokens_used || 0}</div>
                <div><strong>Duration:</strong> {selectedRun.duration_seconds || 0}s</div>
                {selectedRun.pr_url && (
                  <div>
                    <strong>PR:</strong> <a href={selectedRun.pr_url} target="_blank" rel="noreferrer" style={{ color: "#0969da" }}>View on GitHub</a>
                  </div>
                )}
              </div>

              {/* Human Approval Controls */}
              {selectedRun.status === "awaiting_approval" && (
                <div style={{ background: "#fff8c5", border: "1px solid #d4a72c", padding: "14px", borderRadius: "6px", marginBottom: "20px" }}>
                  <h4 style={{ margin: "0 0 8px 0", color: "#7d4e00" }}>Human Approval Required</h4>
                  <p style={{ margin: "0 0 10px 0", fontSize: "13px", color: "#573a08" }}>Review the proposed fix diff and test execution below before deciding.</p>
                  <input
                    type="text"
                    placeholder="Optional reviewer note..."
                    value={decisionNote}
                    onChange={(e) => setDecisionNote(e.target.value)}
                    style={{ width: "100%", padding: "6px 8px", border: "1px solid #d0d7de", borderRadius: "4px", marginBottom: "10px", boxSizing: "border-box" }}
                  />
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button
                      onClick={() => handleDecision("approved")}
                      disabled={loading}
                      style={{ padding: "6px 16px", background: "#1f883d", color: "#fff", border: "none", borderRadius: "6px", fontWeight: "600", cursor: "pointer" }}
                    >
                      Approve Fix
                    </button>
                    <button
                      onClick={() => handleDecision("rejected")}
                      disabled={loading}
                      style={{ padding: "6px 16px", background: "#cf222e", color: "#fff", border: "none", borderRadius: "6px", fontWeight: "600", cursor: "pointer" }}
                    >
                      Reject Fix
                    </button>
                  </div>
                </div>
              )}

              {/* Issue Description */}
              <div style={{ marginBottom: "16px" }}>
                <h4 style={{ margin: "0 0 6px 0", fontSize: "14px" }}>Issue Description</h4>
                <div style={{ background: "#f6f8fa", padding: "10px 12px", borderRadius: "6px", fontSize: "13px", whiteSpace: "pre-wrap" }}>
                  {selectedRun.issue_body}
                </div>
              </div>

              {/* Reviewer Notes */}
              {selectedRun.review_notes && (
                <div style={{ marginBottom: "16px" }}>
                  <h4 style={{ margin: "0 0 6px 0", fontSize: "14px" }}>Reviewer Notes</h4>
                  <div style={{ background: "#f6f8fa", padding: "10px 12px", borderRadius: "6px", fontSize: "13px", whiteSpace: "pre-wrap" }}>
                    {selectedRun.review_notes}
                  </div>
                </div>
              )}

              {/* Proposed Diff */}
              <div style={{ marginBottom: "16px" }}>
                <h4 style={{ margin: "0 0 6px 0", fontSize: "14px" }}>Proposed Diff (Unified)</h4>
                {renderDiff(selectedRun.diff)}
              </div>

              {/* Sandbox Test Output */}
              <div>
                <h4 style={{ margin: "0 0 6px 0", fontSize: "14px" }}>Sandbox Test Output</h4>
                <pre style={{ background: "#24292e", color: "#f0f6fc", padding: "12px", borderRadius: "6px", overflowX: "auto", fontSize: "12px", maxHeight: "250px" }}>
                  {selectedRun.test_output || "No test output available."}
                </pre>
              </div>
            </div>
          ) : (
            <div style={{ border: "1px dashed #d0d7de", borderRadius: "6px", padding: "48px 16px", textAlign: "center", color: "#656d76" }}>
              Select a run from the history on the left, or submit a new run to begin.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

