import type { ProjectSummary, User } from "./types";

// All requests go through the Next.js /api proxy to the FastAPI backend.
const BASE = "http://localhost:8000"; // Point directly to the FastAPI backend for development
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
      message = body?.error?.message ?? body?.detail ?? message;
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

  // Extended Endpoints for Phase 2-7
  runAssistant: (id: string, prompt: string) =>
    request<{ run_id: string; report: any }>(`/projects/${id}/run`, {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),
  listReports: (id: string) =>
    request<any[]>(`/projects/${id}/reports`),
  approveReport: (id: string, reportId: string) =>
    request<any>(`/projects/${id}/reports/${reportId}/approve`, {
      method: "POST",
    }),
  listActions: (id: string) =>
    request<any[]>(`/projects/${id}/actions`),
  approveAction: (id: string, actionId: string) =>
    request<any>(`/projects/${id}/actions/${actionId}/approve`, {
      method: "POST",
    }),
  executeAction: (id: string, actionId: string, payload: any) =>
    request<any>(`/projects/${id}/actions/${actionId}/execute`, {
      method: "POST",
      body: JSON.stringify({ payload }),
    }),
  submitFeedback: (id: string, data: any) =>
    request<any>(`/projects/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listAudit: (id: string) =>
    request<any[]>(`/projects/${id}/audit`),
};
