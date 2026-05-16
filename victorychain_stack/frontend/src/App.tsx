import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { NavBar } from "./components/NavBar";
import { AdminReviewDashboardPage } from "./pages/AdminReviewDashboardPage";
import { BeneficiaryPortalPage } from "./pages/BeneficiaryPortalPage";
import { ComplianceDashboardPage } from "./pages/ComplianceDashboardPage";
import { DonatePage } from "./pages/DonatePage";
import { ImpactDashboardPage } from "./pages/ImpactDashboardPage";
import { ImpactReportsPage } from "./pages/ImpactReportsPage";
import { LandingPage } from "./pages/LandingPage";
import { PoolDetailPage } from "./pages/PoolDetailPage";
import { ReceiptWalletPage } from "./pages/ReceiptWalletPage";
import { TransparencyLedgerPage } from "./pages/TransparencyLedgerPage";
import { TreasuryDashboardPage } from "./pages/TreasuryDashboardPage";

export function App() {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/donate" element={<DonatePage />} />
        <Route path="/pool/:category" element={<PoolDetailPage />} />
        <Route path="/wallet" element={<ReceiptWalletPage />} />
        <Route path="/impact" element={<ImpactDashboardPage />} />
        <Route path="/ledger" element={<TransparencyLedgerPage />} />
        <Route path="/beneficiary" element={<BeneficiaryPortalPage />} />
        <Route path="/admin" element={<AdminReviewDashboardPage />} />
        <Route path="/treasury" element={<TreasuryDashboardPage />} />
        <Route path="/compliance" element={<ComplianceDashboardPage />} />
        <Route path="/reports" element={<ImpactReportsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
