import React from "react";
import { Link } from "react-router-dom";

export function NavBar() {
  return (
    <nav className="container" style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      <Link to="/">Home</Link>
      <Link to="/donate">Donate</Link>
      <Link to="/wallet">Receipts</Link>
      <Link to="/impact">Impact</Link>
      <Link to="/ledger">Ledger</Link>
      <Link to="/beneficiary">Beneficiary</Link>
      <Link to="/admin">Admin</Link>
      <Link to="/treasury">Treasury</Link>
      <Link to="/compliance">Compliance</Link>
      <Link to="/reports">Reports</Link>
    </nav>
  );
}
