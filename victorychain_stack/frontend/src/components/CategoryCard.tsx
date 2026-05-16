import React from "react";

export type CategoryCode = "WIDOW" | "ELDER" | "ORPHAN" | "MERCY" | "EARTH";

export function CategoryCard(props: {
  code: CategoryCode;
  title: string;
  detail: string;
  onSelect: (code: CategoryCode) => void;
}) {
  return (
    <button className="card" onClick={() => props.onSelect(props.code)}>
      <h3>{props.title}</h3>
      <p>{props.detail}</p>
    </button>
  );
}
