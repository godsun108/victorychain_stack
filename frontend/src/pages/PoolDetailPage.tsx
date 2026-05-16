import React from "react";
import { useParams } from "react-router-dom";

const poolCopy: Record<string, string> = {
  WIDOW: "Housing, direct care, and emergency stabilization for widows.",
  ELDER: "Dignity, medicine, and assisted daily living support for elders.",
  ORPHAN: "Shelter, nutrition, education continuity, and guardian support.",
  MERCY: "Flexible response to urgent humanitarian cases.",
  EARTH: "Reforestation, watershed repair, biodiversity, and soil restoration."
};

export function PoolDetailPage() {
  const { category = "MERCY" } = useParams();
  return (
    <main className="container">
      <h2>{category} Pool</h2>
      <div className="card">{poolCopy[category] ?? poolCopy.MERCY}</div>
      <div className="card">Flow of funds: donor checkout to category treasury, then approved disbursement, then public impact updates.</div>
    </main>
  );
}
