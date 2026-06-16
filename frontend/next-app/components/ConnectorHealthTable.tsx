import React from "react";

export type ConnectorStatus = {
  platform: string;
  module_present: boolean;
  mode: "api" | "browser_automation" | "manual_session_required" | "unavailable";
  auth_requirement: string;
  ingest_ready: boolean;
  submission_ready: boolean;
  payout_tracking_ready: boolean;
  notes?: string | null;
};

export function ConnectorHealthTable({ connectors }: { connectors: ConnectorStatus[] }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {["Platform", "Mode", "Ingest", "Submit", "Payout", "Auth", "Notes"].map((h) => (
              <th key={h} style={{ textAlign: "left", borderBottom: "1px solid #ddd", padding: 8 }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {connectors.map((c) => (
            <tr key={c.platform}>
              <td style={{ padding: 8 }}>{c.platform}</td>
              <td style={{ padding: 8 }}>{c.mode}</td>
              <td style={{ padding: 8 }}>{c.ingest_ready ? "yes" : "no"}</td>
              <td style={{ padding: 8 }}>{c.submission_ready ? "yes" : "no"}</td>
              <td style={{ padding: 8 }}>{c.payout_tracking_ready ? "yes" : "no"}</td>
              <td style={{ padding: 8 }}>{c.auth_requirement}</td>
              <td style={{ padding: 8 }}>{c.notes ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
