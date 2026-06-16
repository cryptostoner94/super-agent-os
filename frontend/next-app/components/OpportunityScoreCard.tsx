import React from "react";

export type OpportunityScore = {
  opportunity_id: string;
  total_score: number;
  reward_score: number;
  trust_score: number;
  speed_score: number;
  fit_score: number;
  clarity_score: number;
  risk_penalty: number;
  recommendation: string;
  reasons: string[];
};

export function OpportunityScoreCard({ score }: { score: OpportunityScore }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16 }}>
      <h3 style={{ marginTop: 0 }}>Opportunity score</h3>
      <p><strong>Total:</strong> {score.total_score}</p>
      <p><strong>Recommendation:</strong> {score.recommendation}</p>
      <ul>
        {score.reasons.map((reason, idx) => (
          <li key={idx}>{reason}</li>
        ))}
      </ul>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 8 }}>
        <Metric label="Reward" value={score.reward_score} />
        <Metric label="Trust" value={score.trust_score} />
        <Metric label="Speed" value={score.speed_score} />
        <Metric label="Fit" value={score.fit_score} />
        <Metric label="Clarity" value={score.clarity_score} />
        <Metric label="Risk penalty" value={score.risk_penalty} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ border: "1px solid #eee", borderRadius: 8, padding: 8 }}>
      <div style={{ fontSize: 12, opacity: 0.7 }}>{label}</div>
      <div style={{ fontWeight: 700 }}>{value}</div>
    </div>
  );
}
