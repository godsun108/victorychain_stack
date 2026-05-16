import React, { useEffect, useState } from "react";
import { ADMIN_TOKEN, apiGet } from "../lib/api";

type TreasuryRow = {
  category: string;
  total_received: string;
  total_distributed: string;
  reserve_balance: string;
  beneficiaries_supported: number;
  pending_requests: number;
};

export function ImpactDashboardPage() {
  const [rows, setRows] = useState<TreasuryRow[]>([]);

  useEffect(() => {
    apiGet<TreasuryRow[]>("/admin/treasury")
      .then((rows) => rows)
      .catch(async () => {
        if (!ADMIN_TOKEN) {
          throw new Error("missing admin token");
        }
        return apiGet<TreasuryRow[]>("/admin/treasury", { "x-api-token": ADMIN_TOKEN });
      })
      .then(setRows)
      .catch(() => setRows([]));
  }, []);

  return (
    <main className="container">
      <h2>Impact Dashboard</h2>
      <div className="grid-4">
        {rows.map((row) => (
          <div key={row.category} className="card">
            <h3>{row.category}</h3>
            <div>Received: {row.total_received}</div>
            <div>Distributed: {row.total_distributed}</div>
            <div>Reserve: {row.reserve_balance}</div>
            <div>Beneficiaries: {row.beneficiaries_supported}</div>
            <div>Pending: {row.pending_requests}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
