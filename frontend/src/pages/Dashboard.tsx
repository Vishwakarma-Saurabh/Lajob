import { ChangeEvent, useState } from "react";
import { User } from "../lib/api";

const API_BASE = "http://localhost:8000";

type Match = { title: string; score: number };

type ParseResult = {
  resume_id: number;
  skills: string[];
  education: string[];
  experience_years: number | null;
  error: string | null;
};

export default function Dashboard({ user }: { user: User }) {
  const [result, setResult] = useState<ParseResult | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    setResult(null);
    setMatches([]);
    setLoading(true);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/resumes/upload`, {
        method: "POST",
        body: form,
        credentials: "include",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail || "Upload failed");
      setResult(body);

      if (!body.error && body.skills.length > 0) {
        const matchRes = await fetch(
          `${API_BASE}/resumes/${body.resume_id}/matches`,
          { credentials: "include" }
        );
        const matchBody = await matchRes.json().catch(() => ({}));
        if (matchRes.ok) setMatches(matchBody.matches || []);
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Dashboard</h2>
      <p>Welcome, {user.email}</p>

      <h3>Upload resume (PDF)</h3>
      <input type="file" accept="application/pdf" onChange={onFile} disabled={loading} />
      {loading && <p>Parsing…</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: 16 }}>
          {result.error ? (
            <p style={{ color: "crimson" }}>{result.error}</p>
          ) : (
            <>
              <h4>Extracted Skills</h4>
              <p>{result.skills.length ? result.skills.join(", ") : "None found"}</p>

              <h4>Experience</h4>
              <p>
                {result.experience_years != null
                  ? `${result.experience_years} years`
                  : "Not detected"}
              </p>

              <h4>Education</h4>
              <p>{result.education.length ? result.education.join("; ") : "Not detected"}</p>
            </>
          )}
        </div>
      )}

      {matches.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h4>Matching Job Roles</h4>
          <ul>
            {matches.map((m) => (
              <li key={m.title}>
                <strong>{m.title}</strong> — score: {m.score.toFixed(2)}
              </li>
            ))}
          </ul>
          <p style={{ fontSize: 12, color: "#666" }}>
            Scores are cosine similarity (0–1). Higher is better.
          </p>
        </div>
      )}
    </div>
  );
}