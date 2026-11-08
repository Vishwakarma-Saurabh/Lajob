import { FormEvent, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { authApi } from "../lib/api";

export default function Verify() {
  const [params] = useSearchParams();
  const [email, setEmail] = useState(params.get("email") || "");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const navigate = useNavigate();

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setInfo("");
    try {
      await authApi.verify(email, code);
      setInfo("Verified. Redirecting to login...");
      setTimeout(() => navigate("/login"), 800);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <form onSubmit={onSubmit} style={{ maxWidth: 360, display: "grid", gap: 8 }}>
      <h2>Verify email</h2>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="text"
        placeholder="4-digit code"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        maxLength={4}
        required
      />
      <button type="submit">Verify</button>
      {info && <p style={{ color: "green" }}>{info}</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </form>
  );
}