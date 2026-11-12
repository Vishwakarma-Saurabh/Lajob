import { ChangeEvent, useEffect, useState } from "react";
import { User } from "../lib/api";

const API_BASE = "http://localhost:8000";

type Match = {
  job_id: number;
  title: string;
  company: string;
  location: string;
  job_url: string;
  score: number;
  matched_skills: string[];
};

type Application = {
  id: number;
  job_id: number;
  status: string;
  job_title: string;
  job_company: string;
  job_url: string;
  applied_at: string;
};

export default function Dashboard({ user }: { user: User }) {
  const [tab, setTab] = useState<"upload" | "matches" | "apps">("upload");
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [skills, setSkills] = useState<string[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("Python Developer");
  const [fetchStatus, setFetchStatus] = useState("");

  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    setLoading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${API_BASE}/resumes/upload`, {
        method: "POST", body: form, credentials: "include",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || "Upload failed");
      setResumeId(body.resume_id);
      setSkills(body.skills || []);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const fetchJobs = async () => {
    setFetchStatus("Fetching...");
    try {
      const res = await fetch(
        `${API_BASE}/jobs/fetch?search_term=${encodeURIComponent(searchTerm)}&limit=20`,
        { method: "POST", credentials: "include" }
      );
      const body = await res.json();
      setFetchStatus(`Fetched ${body.fetched} new jobs.`);
    } catch {
      setFetchStatus("Fetch failed.");
    }
  };

  const loadMatches = async () => {
    if (!resumeId) return;
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/jobs/matches?resume_id=${resumeId}&top_k=15`,
        { credentials: "include" }
      );
      const body = await res.json();
      setMatches(body.matches || []);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const loadApps = async () => {
    const res = await fetch(`${API_BASE}/applications`, { credentials: "include" });
    const body = await res.json();
    setApps(body || []);
  };

  const applyToJob = async (jobId: number) => {
    try {
      const res = await fetch(`${API_BASE}/applications`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId }),
      });
      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.detail);
      }
      alert("Application tracked. Open the job URL to submit manually.");
      loadApps();
    } catch (err) {
      alert((err as Error).message);
    }
  };

  useEffect(() => {
    if (tab === "apps") loadApps();
  }, [tab]);

  return (
    <div>
      <h2>Dashboard</h2>
      <p>Welcome, {user.email}</p>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button onClick={() => setTab("upload")}>1. Upload Resume</button>
        <button onClick={() => setTab("matches")} disabled={!resumeId}>2. Matches</button>
        <button onClick={() => setTab("apps")}>3. Applications</button>
      </div>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {tab === "upload" && (
        <div>
          <h3>Upload Resume (PDF)</h3>
          <input type="file" accept="application/pdf" onChange={onFile} disabled={loading} />
          {loading && <p>Parsing…</p>}
          {skills.length > 0 && (
            <p><strong>Skills found:</strong> {skills.join(", ")}</p>
          )}
        </div>
      )}

      {tab === "matches" && (
        <div>
          <h3>Job Matches</h3>
          <div style={{ marginBottom: 12 }}>
            <input value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Search term" />
            <button onClick={fetchJobs}>Fetch Jobs from Naukri</button>
            <button onClick={loadMatches} style={{ marginLeft: 8 }}>Refresh Matches</button>
            {fetchStatus && <span style={{ marginLeft: 8 }}>{fetchStatus}</span>}
          </div>
          {loading && <p>Loading…</p>}
          {matches.length === 0 && <p>No matches yet. Fetch jobs first.</p>}
          <ul>
            {matches.map((m) => (
              <li key={m.job_id} style={{ marginBottom: 12 }}>
                <strong>{m.title}</strong> at {m.company} — score: {m.score}
                <br />
                <small>{m.location} | Matched: {m.matched_skills.join(", ")}</small>
                <br />
                <a href={m.job_url} target="_blank" rel="noreferrer">Open job</a>
                {" | "}
                <button onClick={() => applyToJob(m.job_id)}>Track Application</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {tab === "apps" && (
        <div>
          <h3>My Applications</h3>
          {apps.length === 0 && <p>No applications tracked yet.</p>}
          <table style={{ borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #ccc", textAlign: "left" }}>
                <th>Job</th><th>Company</th><th>Status</th><th>Applied</th><th>Link</th>
              </tr>
            </thead>
            <tbody>
              {apps.map((a) => (
                <tr key={a.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td>{a.job_title}</td>
                  <td>{a.job_company}</td>
                  <td>{a.status}</td>
                  <td>{new Date(a.applied_at).toLocaleDateString()}</td>
                  <td><a href={a.job_url} target="_blank" rel="noreferrer">Open</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}