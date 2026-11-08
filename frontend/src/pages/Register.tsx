import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "../lib/api";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const navigate = useNavigate();

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setInfo("");
    try {
      await authApi.register(email, password, fullName || undefined);
      setInfo("Check your email for the verification code.");
      setTimeout(() => navigate(`/verify?email=${encodeURIComponent(email)}`), 800);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <form onSubmit={onSubmit} style={{ maxWidth: 360, display: "grid", gap: 8 }}>
      <h2>Register</h2>
      <input
        type="text"
        placeholder="Full name (optional)"
        value={fullName}
        onChange={(e) => setFullName(e.target.value)}
      />
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="Password (min 8 chars)"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        minLength={8}
        required
      />
      <button type="submit">Create account</button>
      {info && <p style={{ color: "green" }}>{info}</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </form>
  );
}