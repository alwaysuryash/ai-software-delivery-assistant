"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { api, clearToken, getToken, setToken } from "@/lib/api";
import type { Health } from "@/lib/types";

const HEALTH_STYLE: Record<Health, string> = {
  green: "bg-health-green",
  amber: "bg-health-amber",
  red: "bg-health-red",
  unknown: "bg-health-unknown",
};

function LoginPanel({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("pm@acme.com");
  const login = useMutation({
    mutationFn: () => api.devLogin(email),
    onSuccess: (data) => {
      setToken(data.access_token);
      onLogin();
    },
  });

  return (
    <div className="mx-auto max-w-sm rounded-lg border bg-white p-6 shadow-sm">
      <h1 className="mb-1 text-lg font-semibold">Sign in</h1>
      <p className="mb-4 text-sm text-gray-500">
        Development login (enterprise SSO / Entra ID wired in a later phase).
      </p>
      <label className="mb-1 block text-sm font-medium" htmlFor="email">
        Work email
      </label>
      <input
        id="email"
        className="mb-3 w-full rounded border px-3 py-2 text-sm"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <button
        className="w-full rounded bg-gray-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        onClick={() => login.mutate()}
        disabled={login.isPending}
      >
        {login.isPending ? "Signing in…" : "Sign in"}
      </button>
      {login.isError ? (
        <p className="mt-2 text-sm text-health-red">{(login.error as Error).message}</p>
      ) : null}
    </div>
  );
}

function ProjectSelector({ onSignOut }: { onSignOut: () => void }) {
  const projects = useQuery({ queryKey: ["projects"], queryFn: api.listProjects });
  const me = useQuery({ queryKey: ["me"], queryFn: api.me });

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Your projects</h1>
          {me.data ? (
            <p className="text-sm text-gray-500">
              {me.data.display_name} · {me.data.role.replaceAll("_", " ")}
            </p>
          ) : null}
        </div>
        <button className="text-sm text-gray-600 underline" onClick={onSignOut}>
          Sign out
        </button>
      </div>

      {projects.isLoading ? <p>Loading…</p> : null}
      {projects.isError ? (
        <p className="text-health-red">{(projects.error as Error).message}</p>
      ) : null}

      <ul className="grid gap-3 sm:grid-cols-2">
        {projects.data?.map((p) => (
          <li key={p.id} className="rounded-lg border bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <Link href={`/projects/${p.id}`} className="font-medium hover:underline">
                {p.name}
              </Link>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium text-white ${HEALTH_STYLE[p.current_health]}`}
              >
                {p.current_health}
              </span>
            </div>
            <p className="mt-1 text-sm text-gray-500">Owner: {p.owner}</p>
          </li>
        ))}
      </ul>
      {projects.data && projects.data.length === 0 ? (
        <p className="text-sm text-gray-500">You have no authorized projects.</p>
      ) : null}
    </div>
  );
}

export default function HomePage() {
  const qc = useQueryClient();
  const [authed, setAuthed] = useState<boolean>(() => Boolean(getToken()));

  if (!authed) return <LoginPanel onLogin={() => setAuthed(true)} />;
  return (
    <ProjectSelector
      onSignOut={() => {
        clearToken();
        qc.clear();
        setAuthed(false);
      }}
    />
  );
}
