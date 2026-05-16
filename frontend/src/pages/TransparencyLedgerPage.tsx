import React, { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

type LedgerRow = {
  disbursement_id: string;
  category: string;
  amount: string;
  currency: string;
  created_at: string;
};

type ImpactUpdate = {
  update_id: string;
  category: string;
  title: string;
  anonymized_summary: string;
  published_at: string;
};

export function TransparencyLedgerPage() {
  const [ledger, setLedger] = useState<LedgerRow[]>([]);
  const [updates, setUpdates] = useState<ImpactUpdate[]>([]);
  const [entityType, setEntityType] = useState("webhook_event");
  const [entityId, setEntityId] = useState("");
  const [proof, setProof] = useState<string>("");

  useEffect(() => {
    apiGet<LedgerRow[]>("/transparency/ledger").then(setLedger).catch(() => setLedger([]));
    apiGet<ImpactUpdate[]>("/transparency/impact-updates").then(setUpdates).catch(() => setUpdates([]));
  }, []);

  return (
    <main className="container">
      <h2>Public Transparency Ledger</h2>
      <div className="card">
        {ledger.length === 0 ? "No disbursements yet." : ledger.map((item) => (
          <div key={item.disbursement_id}>{item.category}: {item.amount} {item.currency}</div>
        ))}
      </div>
      <div className="card">
        <h3>Impact Updates</h3>
        {updates.length === 0 ? "No public updates yet." : updates.map((item) => (
          <div key={item.update_id}>
            <strong>{item.title}</strong>: {item.anonymized_summary}
          </div>
        ))}
      </div>
      <div className="card" style={{ display: "grid", gap: 8 }}>
        <h3>Signed Audit Proof</h3>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <select value={entityType} onChange={(event) => setEntityType(event.target.value)}>
            <option value="webhook_event">webhook_event</option>
            <option value="disbursement">disbursement</option>
          </select>
          <input value={entityId} onChange={(event) => setEntityId(event.target.value)} placeholder="entity id" />
          <button
            type="button"
            onClick={() =>
              apiGet<{ signature_hex: string; canonical_payload: string }>(
                `/transparency/audit-proof/${entityType}/${entityId}`
              )
                .then((res) => setProof(`signature=${res.signature_hex}\npayload=${res.canonical_payload}`))
                .catch(() => setProof("Audit proof not found"))
            }
          >
            Generate Proof
          </button>
        </div>
        {proof && <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>{proof}</pre>}
      </div>
    </main>
  );
}
