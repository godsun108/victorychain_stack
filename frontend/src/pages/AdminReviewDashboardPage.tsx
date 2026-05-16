import React, { useEffect, useState } from "react";
import { ADMIN_TOKEN, apiGet, apiPatch, apiPost } from "../lib/api";

type WebhookRow = {
  id: string;
  provider: string;
  provider_event_id: string;
  event_type: string | null;
  delivery_count: number;
  processing_status: string;
  retry_count: number;
  max_retries: number;
  last_error: string | null;
  next_retry_at: string | null;
  last_seen_at: string;
  remediation_owner_user_id?: string | null;
  remediation_status?: string | null;
  remediation_notes?: string | null;
};

type RetryResult = {
  attempted: number;
  processed: number;
  queued: number;
  dead_lettered: number;
};

type QueueMetrics = {
  retry_queue_depth: number;
  total_retry_queued: number;
  dead_letter_count: number;
  oldest_pending_event_id: string | null;
  oldest_pending_first_seen_at: string | null;
};

const ADMIN_HEADERS = { "x-api-token": ADMIN_TOKEN || "admin-token" };

export function AdminReviewDashboardPage() {
  const [provider, setProvider] = useState("");
  const [status, setStatus] = useState("");
  const [remediationFilter, setRemediationFilter] = useState("");
  const [rows, setRows] = useState<WebhookRow[]>([]);
  const [message, setMessage] = useState("");
  const [metrics, setMetrics] = useState<QueueMetrics | null>(null);
  const [ownerUserId, setOwnerUserId] = useState("");
  const [remediationStatus, setRemediationStatus] = useState("open");
  const [remediationNotes, setRemediationNotes] = useState("");
  const [targetEventId, setTargetEventId] = useState("");

  async function loadEvents() {
    const params = new URLSearchParams();
    if (provider) params.set("provider", provider);
    if (status) params.set("processing_status", status);
    if (remediationFilter) params.set("remediation_status", remediationFilter);
    params.set("limit", "100");
    const data = await apiGet<WebhookRow[]>(`/admin/webhooks/events?${params.toString()}`, ADMIN_HEADERS);
    setRows(data);
  }

  async function retryQueued(includeDeadLetter: boolean) {
    const payload = { include_dead_letter: includeDeadLetter, limit: 100 };
    const result = await apiPost<RetryResult>("/admin/webhooks/retry", payload, ADMIN_HEADERS);
    setMessage(
      `Retry run complete: attempted ${result.attempted}, processed ${result.processed}, queued ${result.queued}, dead-lettered ${result.dead_lettered}.`
    );
    await loadEvents();
    await loadMetrics();
  }

  async function updateRemediation() {
    if (!targetEventId) {
      setMessage("Enter event ID for remediation update.");
      return;
    }
    await apiPatch(
      `/admin/webhooks/events/${targetEventId}/remediation`,
      {
        owner_user_id: ownerUserId || null,
        remediation_status: remediationStatus,
        remediation_notes: remediationNotes || null
      },
      ADMIN_HEADERS
    );
    setMessage(`Remediation updated for ${targetEventId}.`);
    await loadEvents();
  }

  async function loadMetrics() {
    const data = await apiGet<QueueMetrics>("/admin/webhooks/metrics", ADMIN_HEADERS);
    setMetrics(data);
  }

  useEffect(() => {
    loadEvents().catch(() => setRows([]));
    loadMetrics().catch(() => setMetrics(null));
  }, []);

  return (
    <main className="container">
      <h2>Admin Review Dashboard</h2>
      <div className="card">Pending compliance reviews, beneficiary approvals, and disbursement execution controls.</div>
      <div className="card" style={{ display: "grid", gap: 10 }}>
        <h3>Webhook Replay Monitor</h3>
        {metrics && (
          <div>
            Queue Ready: {metrics.retry_queue_depth} · Total Queued: {metrics.total_retry_queued} · Dead Letters: {metrics.dead_letter_count}
            {metrics.oldest_pending_event_id && ` · Oldest Pending: ${metrics.oldest_pending_event_id}`}
          </div>
        )}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            value={provider}
            onChange={(event) => setProvider(event.target.value)}
            placeholder="provider (stripe, vusd)"
          />
          <input
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            placeholder="status (processed, retry_queued, dead_letter)"
          />
          <input
            value={remediationFilter}
            onChange={(event) => setRemediationFilter(event.target.value)}
            placeholder="remediation (open, in_progress, resolved)"
          />
          <button type="button" onClick={() => loadEvents().catch(() => setRows([]))}>Apply</button>
          <button type="button" onClick={() => loadMetrics().catch(() => setMetrics(null))}>Refresh Metrics</button>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button" onClick={() => retryQueued(false).catch(() => setMessage("Retry failed"))}>
            Retry Queued
          </button>
          <button type="button" onClick={() => retryQueued(true).catch(() => setMessage("Retry failed"))}>
            Retry + Include Dead Letter
          </button>
        </div>
        <div style={{ display: "grid", gap: 8 }}>
          <strong>Dead-Letter Remediation</strong>
          <input value={targetEventId} onChange={(event) => setTargetEventId(event.target.value)} placeholder="event id" />
          <input value={ownerUserId} onChange={(event) => setOwnerUserId(event.target.value)} placeholder="owner user id (optional)" />
          <select value={remediationStatus} onChange={(event) => setRemediationStatus(event.target.value)}>
            <option value="open">open</option>
            <option value="in_progress">in_progress</option>
            <option value="resolved">resolved</option>
            <option value="none">none</option>
          </select>
          <textarea value={remediationNotes} onChange={(event) => setRemediationNotes(event.target.value)} placeholder="remediation notes" />
          <button type="button" onClick={() => updateRemediation().catch(() => setMessage("Remediation update failed"))}>
            Update Remediation
          </button>
        </div>
        {message && <small>{message}</small>}
        {rows.length === 0 ? (
          <small>No webhook events yet.</small>
        ) : (
          rows.map((row) => (
            <div key={row.id} style={{ borderTop: "1px solid #eadcc8", paddingTop: 8 }}>
              <div><strong>{row.provider}</strong> · {row.event_type ?? "unknown"} · {row.processing_status}</div>
              <div>ID: {row.id}</div>
              <div>Provider Event: {row.provider_event_id}</div>
              <div>Deliveries: {row.delivery_count} · Retries: {row.retry_count}/{row.max_retries}</div>
              <div>Remediation: {row.remediation_status ?? "none"} {row.remediation_owner_user_id ? `· owner ${row.remediation_owner_user_id}` : ""}</div>
              {row.remediation_notes && <div>Notes: {row.remediation_notes}</div>}
              {row.last_error && <div>Error: {row.last_error}</div>}
              {row.next_retry_at && <div>Next Retry: {row.next_retry_at}</div>}
              <div>Last Seen: {row.last_seen_at}</div>
            </div>
          ))
        )}
      </div>
    </main>
  );
}
