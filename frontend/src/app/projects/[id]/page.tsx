"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

const HEALTH_COLORS: Record<string, string> = {
  green: "bg-green-100 text-green-800 border-green-200",
  amber: "bg-amber-100 text-amber-800 border-amber-200",
  red: "bg-red-100 text-red-800 border-red-200",
  unknown: "bg-gray-100 text-gray-800 border-gray-200",

  // Status and evaluation mappings (B8)
  pass: "bg-green-100 text-green-800 border-green-200",
  fail: "bg-red-100 text-red-800 border-red-200",
  approved: "bg-green-100 text-green-800 border-green-200",
  evaluated: "bg-blue-100 text-blue-800 border-blue-200",
  pending: "bg-amber-100 text-amber-800 border-amber-200",
  executed: "bg-green-100 text-green-800 border-green-200",
  blocked: "bg-red-100 text-red-800 border-red-200",
  draft: "bg-gray-100 text-gray-800 border-gray-200",
};

const HEALTH_DOTS: Record<string, string> = {
  green: "bg-green-600",
  amber: "bg-amber-500",
  red: "bg-red-600",
  unknown: "bg-gray-500",
};

export default function ProjectWorkspace() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();

  const project = useQuery({ queryKey: ["project", id], queryFn: () => api.getProject(id) });
  const reports = useQuery({ queryKey: ["reports", id], queryFn: () => api.listReports(id) });
  const actions = useQuery({ queryKey: ["actions", id], queryFn: () => api.listActions(id) });
  const audits = useQuery({ queryKey: ["audits", id], queryFn: () => api.listAudit(id) });

  const [question, setQuestion] = useState("Review Project Alpha for the current sprint. Identify the top five risks and draft a concise stakeholder update.");
  const [activeTab, setActiveTab] = useState<"findings" | "report" | "approvals" | "audit">("findings");
  const [selectedFinding, setSelectedFinding] = useState<any | null>(null);
  const [feedbackFindingId, setFeedbackFindingId] = useState<string | null>(null);
  const [feedbackText, setFeedbackFeedbackText] = useState("");
  const [feedbackCategory, setFeedbackCategory] = useState("correct");
  const [feedbackRating, setFeedbackRating] = useState(5);

  const runAnalysis = useMutation({
    mutationFn: () => api.runAssistant(id, question),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports", id] });
      qc.invalidateQueries({ queryKey: ["project", id] });
      qc.invalidateQueries({ queryKey: ["actions", id] });
      qc.invalidateQueries({ queryKey: ["audits", id] });
      setActiveTab("findings");
    },
  });

  const approveReport = useMutation({
    mutationFn: (reportId: string) => api.approveReport(id, reportId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports", id] });
      qc.invalidateQueries({ queryKey: ["audits", id] });
    },
  });

  const approveAction = useMutation({
    mutationFn: (actionId: string) => api.approveAction(id, actionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["actions", id] });
      qc.invalidateQueries({ queryKey: ["audits", id] });
    },
  });

  const executeAction = useMutation({
    mutationFn: ({ actionId, payload }: { actionId: string; payload: any }) =>
      api.executeAction(id, actionId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["actions", id] });
      qc.invalidateQueries({ queryKey: ["audits", id] });
      alert("Outbound action executed successfully!");
    },
    onError: (err: any) => {
      alert(`Execution failed: ${err.message}`);
    },
  });

  const submitFeedback = useMutation({
    mutationFn: (data: any) => api.submitFeedback(id, data),
    onSuccess: () => {
      setFeedbackFindingId(null);
      setFeedbackFeedbackText("");
      alert("Thank you for your feedback!");
    },
  });

  const latestReport = reports.data && reports.data.length > 0 ? reports.data[0] : null;
  const scoring = latestReport?.content?.scoring_engine ?? {
    overall_health: "unknown",
    overall_score: 0,
    dimensions: {},
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      <Link href="/" className="inline-flex items-center text-sm text-blue-600 hover:underline">
        ← All projects
      </Link>

      <div className="mt-4 md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl">
            {project.data?.name ?? "Project Workspace"}
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Owner: {project.data?.owner} · Status: <span className="capitalize">{project.data?.status}</span>
          </p>
        </div>
      </div>

      {/* Assistant Query Panel */}
      <section className="mt-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900">AI Software Delivery Copilot</h3>
        <p className="text-sm text-gray-500 mb-4">
          Decomposes queries, gathers live connector evidence, analyzes dimensions, and triggers quality gates.
        </p>

        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            type="text"
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about this project..."
          />
          <button
            onClick={() => runAnalysis.mutate()}
            disabled={runAnalysis.isPending}
            className="inline-flex justify-center items-center rounded-lg bg-gray-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-gray-800 disabled:opacity-50"
          >
            {runAnalysis.isPending ? "Running Multi-Agent Intelligence..." : "Run Analysis"}
          </button>
        </div>
      </section>

      {/* Health Dimensions Dashboard */}
      <section className="mt-6 grid gap-4 grid-cols-2 lg:grid-cols-6">
        {/* Overall Score */}
        <div className="col-span-2 rounded-xl border border-gray-200 bg-gray-50 p-5 flex flex-col justify-between">
          <div>
            <h4 className="text-sm font-medium text-gray-500">Overall Health</h4>
            <div className="mt-2 flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-gray-900">
                {scoring.overall_score}
              </span>
              <span className="text-sm text-gray-500">/ 100</span>
            </div>
          </div>
          <div className="mt-4">
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border capitalize ${HEALTH_COLORS[scoring.overall_health]}`}>
              <span className={`mr-1.5 h-1.5 w-1.5 rounded-full ${HEALTH_DOTS[scoring.overall_health]}`} />
              {scoring.overall_health}
            </span>
          </div>
        </div>

        {/* 5 Dimensions */}
        {["scope", "schedule", "quality", "engineering", "operations"].map((dim) => {
          const dimData = scoring.dimensions?.[dim] ?? { health: "unknown", score: 0, triggers_hit: [] };
          return (
            <div key={dim} className="rounded-xl border border-gray-200 bg-white p-5 flex flex-col justify-between">
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 capitalize">{dim}</h4>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="text-xl font-bold text-gray-900">{dimData.score}</span>
                  <span className="text-xs text-gray-400">/100</span>
                </div>
              </div>
              <div className="mt-3">
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-2xs font-semibold border capitalize ${HEALTH_COLORS[dimData.health]}`}>
                  {dimData.health}
                </span>
                {dimData.triggers_hit?.length > 0 && (
                  <p className="mt-2 text-3xs text-red-500 leading-tight truncate" title={dimData.triggers_hit.join(", ")}>
                    ⚠ {dimData.triggers_hit[0]}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </section>

      {/* Main Workspace Workspace Tabs */}
      <div className="mt-8 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: "findings", label: "Findings & Evidence" },
            { id: "report", label: "Status Report Editor" },
            { id: "approvals", label: "Approval Center" },
            { id: "audit", label: "Audit Log & Telemetry" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`whitespace-nowrap border-b-2 py-4 px-1 text-sm font-semibold ${
                activeTab === tab.id
                  ? "border-gray-900 text-gray-900"
                  : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
              }`}
            >
              {tab.id === "approvals" && actions.data && actions.data.filter(a => a.approval_status === "pending").length > 0 ? (
                <span className="inline-flex items-center gap-1.5">
                  {tab.label}
                  <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
                    {actions.data.filter(a => a.approval_status === "pending").length}
                  </span>
                </span>
              ) : (
                tab.label
              )}
            </button>
          ))}
        </nav>
      </div>

      <div className="mt-6">
        {/* TAB 1: FINDINGS & EVIDENCE */}
        {activeTab === "findings" && (
          <div className="grid gap-6 md:grid-cols-3">
            <div className="md:col-span-2 space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Specialized Agent Findings</h3>
              {latestReport?.findings?.length === 0 && (
                <p className="text-sm text-gray-500">No findings generated yet. Run analysis above!</p>
              )}
              {latestReport?.findings?.map((f: any) => (
                <div
                  key={f.id}
                  onClick={() => setSelectedFinding(f)}
                  className={`cursor-pointer rounded-xl border p-5 shadow-2xs transition-all ${
                    selectedFinding?.id === f.id ? "border-gray-900 bg-gray-50" : "border-gray-200 bg-white hover:border-gray-300"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-semibold text-gray-800 uppercase">
                      {f.agent.replace("_agent", "")}
                    </span>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold border capitalize ${HEALTH_COLORS[f.health]}`}>
                      {f.health}
                    </span>
                  </div>
                  <h4 className="mt-3 text-base font-bold text-gray-900">{f.title}</h4>
                  <p className="mt-2 text-sm text-gray-600 line-clamp-2">{f.summary}</p>

                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xs text-red-500 font-medium capitalize">Severity: {f.severity}</span>
                    <span className="text-xs text-blue-600 underline">View Evidence Citations ({f.evidence_refs?.length || 0})</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Citations Sidebar */}
            <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-2xs">
              <h3 className="text-lg font-semibold text-gray-900">Evidence Citation Trace</h3>
              {selectedFinding ? (
                <div className="mt-4 space-y-4">
                  <div>
                    <h4 className="text-sm font-bold text-gray-900">{selectedFinding.title}</h4>
                    <p className="mt-2 text-xs text-gray-600">{selectedFinding.summary}</p>
                  </div>

                  <div className="border-t border-gray-100 pt-4">
                    <h5 className="text-xs font-semibold uppercase tracking-wider text-gray-400">Provenance & Sources</h5>
                    <ul className="mt-3 space-y-3">
                      {selectedFinding.evidence_refs?.map((ref: any, idx: number) => (
                        <li key={idx} className="rounded-lg border border-gray-100 bg-gray-50 p-3 text-xs">
                          <p className="font-semibold text-gray-900">{ref.source || "External System"}</p>
                          <p className="mt-1 text-gray-500">Record ID: {ref.record_id || ref.record_ref || "N/A"}</p>
                          <p className="mt-0.5 text-gray-400">Retrieved: {ref.retrieved_at ? new Date(ref.retrieved_at).toLocaleString() : "Unknown"}</p>
                          {ref.access_uri && (
                            <a
                              href={ref.access_uri}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-2 inline-block text-blue-600 hover:underline"
                            >
                              Open Source Link ↗
                            </a>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Feedback System */}
                  <div className="border-t border-gray-100 pt-4">
                    <button
                      onClick={() => setFeedbackFindingId(selectedFinding.id)}
                      className="w-full text-center rounded bg-gray-100 px-3 py-1.5 text-xs font-semibold text-gray-800 hover:bg-gray-200"
                    >
                      Rate Finding & Give Feedback (BR-10)
                    </button>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-gray-500">Click a specialized finding card on the left to trace its supporting retrieved evidence.</p>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: REPORT EDITOR */}
        {activeTab === "report" && (
          <div className="max-w-4xl space-y-6">
            <div className="flex items-center justify-between border-b border-gray-100 pb-4">
              <div>
                <h3 className="text-lg font-bold text-gray-900">Project Status Report</h3>
                <p className="text-sm text-gray-500">Drafted by PM orchestrator agent (Appendix A format).</p>
              </div>
              {latestReport && (
                <div className="flex items-center gap-3">
                  <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold border capitalize ${HEALTH_COLORS[latestReport.status]}`}>
                    {latestReport.status}
                  </span>
                  {latestReport.status !== "approved" && latestReport.status !== "published" && (
                    <button
                      onClick={() => approveReport.mutate(latestReport.id)}
                      disabled={approveReport.isPending}
                      className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50"
                    >
                      Approve & Publish Status Report
                    </button>
                  )}
                </div>
              )}
            </div>

            {latestReport ? (
              <div className="space-y-6 rounded-xl border border-gray-200 bg-white p-6 shadow-xs prose">
                {/* 1. Exec Summary */}
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-gray-400">1. Overall Health & Executive Summary</h4>
                  <p className="mt-2 text-sm text-gray-800 bg-gray-50 p-4 rounded-lg leading-relaxed">{latestReport.content.executive_summary}</p>
                </div>

                {/* 2. Progress */}
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-gray-400">2. Progress & Milestones</h4>
                  <p className="mt-2 text-sm text-gray-800 bg-gray-50 p-4 rounded-lg leading-relaxed">{latestReport.content.progress_milestones}</p>
                </div>

                {/* 3. Scope */}
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-gray-400">3. Scope & Requirement Readiness</h4>
                  <p className="mt-2 text-sm text-gray-800 bg-gray-50 p-4 rounded-lg leading-relaxed">{latestReport.content.scope_requirements}</p>
                </div>

                {/* 4. Development */}
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-gray-400">4. Development Health</h4>
                  <p className="mt-2 text-sm text-gray-800 bg-gray-50 p-4 rounded-lg leading-relaxed">{latestReport.content.development_health}</p>
                </div>

                {/* 5. Quality */}
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-gray-400">5. Quality & Release Readiness</h4>
                  <p className="mt-2 text-sm text-gray-800 bg-gray-50 p-4 rounded-lg leading-relaxed">{latestReport.content.quality_readiness}</p>
                </div>

                {/* 6. Operations */}
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider text-gray-400">6. Build, Deployment, & Environment Health</h4>
                  <p className="mt-2 text-sm text-gray-800 bg-gray-50 p-4 rounded-lg leading-relaxed">{latestReport.content.operations_environments}</p>
                </div>

                {/* Evaluations list */}
                <div className="border-t border-gray-100 pt-6">
                  <h4 className="text-sm font-bold uppercase tracking-wider text-gray-400">AI Quality Gate Evaluations</h4>
                  <div className="mt-4 grid gap-4 sm:grid-cols-3">
                    {latestReport.evaluations?.map((ev: any, idx: number) => (
                      <div key={idx} className="rounded-lg border border-gray-200 p-4">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold capitalize text-gray-500">{ev.evaluator_type}</span>
                          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-2xs font-semibold border capitalize ${HEALTH_COLORS[ev.result]}`}>
                            {ev.result}
                          </span>
                        </div>
                        <p className="mt-2 text-lg font-bold text-gray-900">{Math.round(ev.score * 100)}%</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">No reports generated yet. Run analysis above!</p>
            )}
          </div>
        )}

        {/* TAB 3: APPROVAL CENTER */}
        {activeTab === "approvals" && (
          <div className="max-w-4xl space-y-6">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Outbound Action Approvals</h3>
              <p className="text-sm text-gray-500">Proposed system modifications. Actions remain pending until exact payload hash matches approval (BR-03).</p>
            </div>

            {actions.data?.length === 0 && (
              <p className="text-sm text-gray-500">No proposed actions currently require approval.</p>
            )}

            <div className="space-y-4">
              {actions.data?.map((act: any) => (
                <div key={act.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-2xs">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-gray-500">Proposed Action ID: {act.id}</span>
                    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold border capitalize ${HEALTH_COLORS[act.approval_status]}`}>
                      {act.approval_status}
                    </span>
                  </div>

                  <h4 className="mt-3 text-base font-bold text-gray-900">{act.description}</h4>
                  <p className="mt-1 text-sm text-gray-500">Owner: {act.owner} · Priority: <span className="capitalize">{act.priority}</span></p>

                  <div className="mt-4 rounded-lg bg-gray-50 p-4 font-mono text-xs text-gray-700">
                    <p className="font-bold text-gray-500 mb-2">PROPOSED OUTBOUND TRANSACTION PAYLOAD:</p>
                    <pre className="overflow-x-auto">{JSON.stringify(act.proposed_write_payload, null, 2)}</pre>
                    <p className="mt-3 text-2xs text-gray-400">Exact Payload Hash constraint: {act.payload_hash}</p>
                  </div>

                  <div className="mt-4 flex gap-3">
                    {act.approval_status === "pending" && (
                      <button
                        onClick={() => approveAction.mutate(act.id)}
                        disabled={approveAction.isPending}
                        className="rounded bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-700"
                      >
                        Approve Write Action
                      </button>
                    )}
                    {act.approval_status === "approved" && (
                      <button
                        onClick={() => executeAction.mutate({ actionId: act.id, payload: act.proposed_write_payload })}
                        disabled={executeAction.isPending}
                        className="rounded bg-gray-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-gray-800"
                      >
                        Execute Outbound Action
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: AUDIT LOG */}
        {activeTab === "audit" && (
          <div className="max-w-4xl space-y-6">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Immutable Audit Trail</h3>
              <p className="text-sm text-gray-500">Complete execution provenance, tool calls, and human approvals scoped by correlation ID (NFR-05).</p>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-2xs">
              <table className="min-w-full divide-y divide-gray-200 text-xs">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left font-semibold uppercase text-gray-500">Timestamp</th>
                    <th className="px-6 py-3 text-left font-semibold uppercase text-gray-500">Actor</th>
                    <th className="px-6 py-3 text-left font-semibold uppercase text-gray-500">Action</th>
                    <th className="px-6 py-3 text-left font-semibold uppercase text-gray-500">Resource</th>
                    <th className="px-6 py-3 text-left font-semibold uppercase text-gray-500">Metadata</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {audits.data?.map((ev: any) => (
                    <tr key={ev.id}>
                      <td className="whitespace-nowrap px-6 py-4 text-gray-500">{new Date(ev.timestamp).toLocaleString()}</td>
                      <td className="whitespace-nowrap px-6 py-4 font-semibold text-gray-900">{ev.actor}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-gray-500 capitalize">{ev.action.replaceAll("_", " ")}</td>
                      <td className="whitespace-nowrap px-6 py-4 text-gray-500 truncate max-w-xs" title={ev.resource}>{ev.resource}</td>
                      <td className="px-6 py-4 text-gray-400 font-mono text-2xs max-w-sm overflow-x-auto">
                        {JSON.stringify(ev.event_metadata)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* FEEDBACK POPUP OVERLAY */}
      {feedbackFindingId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg">
            <h3 className="text-lg font-bold text-gray-900">Rate and Correct AI Finding</h3>
            <p className="mt-1 text-xs text-gray-500">Submit corrections without overwriting source systems (BR-10).</p>

            <div className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-500">Category</label>
                <select
                  value={feedbackCategory}
                  onChange={(e) => setFeedbackCategory(e.target.value)}
                  className="mt-1 w-full rounded border border-gray-300 p-2 text-xs"
                >
                  <option value="correct">Correct / Highly Accurate</option>
                  <option value="incorrect">Incorrect / Hallucination</option>
                  <option value="irrelevant">Irrelevant to current scope</option>
                  <option value="missing_context">Missing crucial context</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500">Rating (1 to 5 Stars)</label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={feedbackRating}
                  onChange={(e) => setFeedbackRating(parseInt(e.target.value))}
                  className="mt-1 w-full rounded border border-gray-300 p-2 text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500">Comments</label>
                <textarea
                  rows={3}
                  value={feedbackText}
                  onChange={(e) => setFeedbackFeedbackText(e.target.value)}
                  placeholder="Your corrections or observations..."
                  className="mt-1 w-full rounded border border-gray-300 p-2 text-xs"
                />
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2 text-xs font-semibold">
              <button
                onClick={() => setFeedbackFindingId(null)}
                className="rounded border border-gray-300 px-3 py-2 hover:bg-gray-100"
              >
                Cancel
              </button>
              <button
                onClick={() => submitFeedback.mutate({ finding_id: feedbackFindingId, rating: feedbackRating, category: feedbackCategory, comments: feedbackText })}
                className="rounded bg-gray-900 px-4 py-2 text-white hover:bg-gray-800"
              >
                Submit Feedback
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
