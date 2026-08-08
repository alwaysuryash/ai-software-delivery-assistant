"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

/**
 * Assistant Workspace shell (BRD §17). The run panel is wired to the single-agent
 * daily-health endpoint in Phase 4; for now it presents the workspace layout,
 * question input, time-period control, and the health/evidence panes as placeholders.
 */
export default function ProjectWorkspace() {
  const { id } = useParams<{ id: string }>();
  const project = useQuery({ queryKey: ["project", id], queryFn: () => api.getProject(id) });
  const [question, setQuestion] = useState("Give me today's project health");

  return (
    <div>
      <Link href="/" className="text-sm text-gray-600 underline">
        ← All projects
      </Link>
      <h1 className="mt-2 text-xl font-semibold">
        {project.data?.name ?? "Project"} — Assistant Workspace
      </h1>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <label className="mb-1 block text-sm font-medium" htmlFor="q">
            Ask about this project
          </label>
          <textarea
            id="q"
            className="w-full rounded border px-3 py-2 text-sm"
            rows={3}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <div className="mt-2 flex items-center gap-3">
            <select className="rounded border px-2 py-1 text-sm" defaultValue="today">
              <option value="today">Today</option>
              <option value="sprint">Current sprint</option>
              <option value="week">This week</option>
            </select>
            <button
              className="rounded bg-gray-900 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
              disabled
              title="Enabled in Phase 4 (single-agent MVP)"
            >
              Run analysis
            </button>
            <span className="text-xs text-gray-400">Available from Phase 4</span>
          </div>

          <div className="mt-6 rounded-lg border bg-white p-4 text-sm text-gray-500">
            Structured answer, findings, and evidence citations will render here once the
            Delivery Analyst agent (Phase 4) and deterministic health engine (Phase 3) are wired.
          </div>
        </section>

        <aside>
          <div className="rounded-lg border bg-white p-4">
            <h2 className="text-sm font-semibold">Health</h2>
            <p className="mt-2 text-sm text-gray-500">
              Overall RAG status and dimension scores appear here (BRD §12).
            </p>
          </div>
          <div className="mt-4 rounded-lg border bg-white p-4">
            <h2 className="text-sm font-semibold">Outstanding approvals</h2>
            <p className="mt-2 text-sm text-gray-500">
              Write actions require explicit human approval (Phase 7).
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}
