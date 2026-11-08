const API_BASE = "http://localhost:8000";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export type User = {
  id: number;
  email: string;
  full_name: string | null;
  is_verified: boolean;
};

export const authApi = {
  register: (email: string, password: string, full_name?: string) =>
    apiFetch<{ message: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
  verify: (email: string, code: string) =>
    apiFetch<{ message: string }>("/auth/verify", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    }),
  login: (email: string, password: string) =>
    apiFetch<User>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () =>
    apiFetch<{ message: string }>("/auth/logout", { method: "POST" }),
  me: () => apiFetch<User>("/auth/me"),
};