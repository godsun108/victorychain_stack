import React, { FormEvent, useState } from "react";
import { WalletConnectButton } from "../components/WalletConnectButton";
import { API_BASE } from "../lib/api";

const categories = ["WIDOW", "ELDER", "ORPHAN", "MERCY", "EARTH"] as const;
const paymentMethods = ["card", "bank", "crypto", "vusd", "wallet"] as const;

export function DonatePage() {
  const [status, setStatus] = useState<string>("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const body = {
      donor_email: String(form.get("donor_email") || ""),
      category: String(form.get("category") || "MERCY"),
      payment_method: String(form.get("payment_method") || "card"),
      amount: Number(form.get("amount") || 0),
      currency: String(form.get("currency") || "USD"),
      impact_notes: String(form.get("impact_notes") || ""),
      project_id: String(form.get("project_id") || "GENERAL")
    };

    const res = await fetch(`${API_BASE}/donors/donate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      setStatus(`Donation failed (${res.status})`);
      return;
    }

    const payload = await res.json();
    setStatus(`Donation accepted. Receipt: ${payload.receipt_id}`);
    event.currentTarget.reset();
  }

  return (
    <main className="container">
      <h2>Donate</h2>
      <p>Connect wallet, select a mercy pool, and submit a compliant impact donation.</p>
      <WalletConnectButton />
      <form className="card" onSubmit={submit} style={{ display: "grid", gap: 10 }}>
        <input name="donor_email" type="email" placeholder="donor@email.org" required />
        <select name="category" defaultValue="MERCY">
          {categories.map((category) => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
        <select name="payment_method" defaultValue="card">
          {paymentMethods.map((method) => (
            <option key={method} value={method}>{method}</option>
          ))}
        </select>
        <input name="amount" type="number" step="0.01" placeholder="Amount" required />
        <input name="currency" defaultValue="USD" />
        <input name="project_id" defaultValue="GENERAL" />
        <textarea name="impact_notes" placeholder="Impact notes" />
        <button type="submit">Submit Donation</button>
      </form>
      {status && <div className="card">{status}</div>}
      <div className="card">Impact tokens are receipts only. No profit, yield, dividend, appreciation, or resale rights.</div>
    </main>
  );
}
