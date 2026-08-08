import type { ProjectSummary, User } from "./types";

// All requests go through the Next.js /api proxy to the FastAPI backend.
const BASE = "/api";
const TOKEN_KEY = "aisda_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const resp = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!resp.ok) {
    let message = resp.statusText;
    try {
      const body = await resp.json();
      message = body?.error?.message ?? message;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }
  return (await resp.json()) as T;
}

export const api = {
  devLogin: (email: string) =>
    request<{ access_token: string }>("/auth/dev-login", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  me: () => request<User>("/auth/me"),
  listProjects: () => request<ProjectSummary[]>("/projects"),
  getProject: (id: string) => request<ProjectSummary>(`/projects/${id}`),
};
