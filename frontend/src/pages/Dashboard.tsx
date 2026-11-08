import { ChangeEvent, useState } from "react";
import { User } from "../lib/api";

const API_BASE = "http://localhost:8000";

export default function Dashboard({ user }: { user: User }) {
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  const onFile = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setStatus("");
    setError("");

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
      setStatus(`Uploaded as ${body.stored_as} (${body.size_bytes} bytes)`);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div>
      <h2>Dashboard</h2>
      <p>Welcome, {user.email}</p>
      <h3>Upload resume (PDF)</h3>
      <input type="file" accept="application/pdf" onChange={onFile} />
      {status && <p style={{ color: "green" }}>{status}</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </div>
  );
}