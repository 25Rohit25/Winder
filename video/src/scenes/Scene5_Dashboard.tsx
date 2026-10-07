import React from "react";
import { useCurrentFrame, interpolate, staticFile, Img } from "remotion";
import { Header } from "../components/Header";

export const Scene5_Dashboard: React.FC = () => {
  const frame = useCurrentFrame();

  // Subtle floating motion
  const translateY = Math.sin(frame * 0.05) * 8;
  const zoom = interpolate(frame, [0, 240], [1.0, 1.05], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#080c16",
        padding: "50px 80px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        fontFamily: "system-ui, -apple-system, sans-serif",
        boxSizing: "border-box",
      }}
    >
      <Header
        category="SCADA DASHBOARD & REPORTING"
        title="Industrial UI & Certification Reports"
        subtitle="Flight-recorder telemetry inspection in React 18 / TypeScript, alongside audit-ready LaTeX and PDF certification reports."
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.2fr 0.8fr",
          gap: 32,
          alignItems: "center",
          transform: `translateY(${translateY}px) scale(${zoom})`,
        }}
      >
        {/* Main Dashboard Preview Card */}
        <div
          style={{
            borderRadius: 16,
            overflow: "hidden",
            border: "2px solid #38bdf8",
            boxShadow: "0 20px 50px rgba(14, 165, 233, 0.25)",
            backgroundColor: "#0f172a",
            position: "relative",
          }}
        >
          <div
            style={{
              backgroundColor: "#1e293b",
              padding: "10px 18px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderBottom: "1px solid #334155",
            }}
          >
            <div style={{ display: "flex", gap: 8 }}>
              <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#ef4444" }} />
              <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#f59e0b" }} />
              <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#10b981" }} />
            </div>
            <span style={{ fontSize: 13, color: "#94a3b8", fontWeight: 600 }}>
              WindCtrl Validate · SCADA Telemetry Flight-Recorder
            </span>
            <span style={{ fontSize: 12, color: "#38bdf8", fontWeight: 700 }}>LIVE AT :5173</span>
          </div>

          <Img
            src={staticFile("dashboard_overview.png")}
            style={{
              width: "100%",
              height: 480,
              objectFit: "cover",
              display: "block",
            }}
          />
        </div>

        {/* Side Stack: Signal Explorer + Audit PDF Stamp */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Signal Explorer Thumbnail */}
          <div
            style={{
              borderRadius: 12,
              overflow: "hidden",
              border: "1px solid #334155",
              boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
              backgroundColor: "#0f172a",
            }}
          >
            <div style={{ backgroundColor: "#1e293b", padding: "8px 16px", fontSize: 13, color: "#cbd5e1", fontWeight: 600 }}>
              Multi-Channel Signal Explorer (1x to 10x Downsampling)
            </div>
            <Img
              src={staticFile("signal_explorer.png")}
              style={{
                width: "100%",
                height: 200,
                objectFit: "cover",
                display: "block",
              }}
            />
          </div>

          {/* Audit Certificate Badge */}
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #10b981",
              borderRadius: 12,
              padding: "18px 24px",
              display: "flex",
              alignItems: "center",
              gap: 18,
              boxShadow: "0 10px 24px rgba(16, 185, 129, 0.15)",
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: 12,
                backgroundColor: "rgba(16, 185, 129, 0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 26,
              }}
            >
              📄
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 16, fontWeight: 800, color: "#f8fafc" }}>
                332 KB Formal Certification PDF Report
              </span>
              <span style={{ fontSize: 13, color: "#94a3b8" }}>
                Auto-generated in CI with embedded 6-panel telemetry plots & engineering sign-off stamps.
              </span>
            </div>
          </div>
        </div>
      </div>

      <div style={{ textAlign: "center", color: "#64748b", fontSize: 15 }}>
        Vite · React 18 · TypeScript · Tailwind CSS · Recharts · Jinja2 · LaTeX · ReportLab
      </div>
    </div>
  );
};
