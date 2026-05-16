import React from "react";
import { useNavigate } from "react-router-dom";
import { CategoryCard } from "../components/CategoryCard";

export function LandingPage() {
  const navigate = useNavigate();

  return (
    <main className="container">
      <h1>Choose where compassion flows.</h1>
      <p>Give with clarity: every donation is routed, receipted, and auditable.</p>
      <section className="grid-4">
        <CategoryCard code="WIDOW" title="Widows" detail="Support housing, care, and direct aid." onSelect={(code) => navigate(`/pool/${code}`)} />
        <CategoryCard code="ELDER" title="Elderly" detail="Support medicine, nutrition, and dignity care." onSelect={(code) => navigate(`/pool/${code}`)} />
        <CategoryCard code="ORPHAN" title="Orphans" detail="Support education, shelter, and guardianship." onSelect={(code) => navigate(`/pool/${code}`)} />
        <CategoryCard code="MERCY" title="General Mercy Fund" detail="Flexible response for urgent needs." onSelect={(code) => navigate(`/pool/${code}`)} />
        <CategoryCard code="EARTH" title="Earth Restoration Fund" detail="Support reforestation, water healing, and soil restoration." onSelect={(code) => navigate(`/pool/${code}`)} />
      </section>
    </main>
  );
}
