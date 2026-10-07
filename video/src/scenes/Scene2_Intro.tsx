import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";
import { Header } from "../components/Header";

export const Scene2_Intro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleProgress = spring({
    frame,
    fps,
    config: { damping: 14 },
  });

  const cardsProgress = spring({
    frame: frame - 15,
    fps,
    config: { damping: 12 },
  });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#080c16",
        padding: "60px 100px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        fontFamily: "system-ui, -apple-system, sans-serif",
        boxSizing: "border-box",
      }}
    >
      <Header
        category="AUTOMATED CONTROLLER VALIDATION PLATFORM"
        title="WindCtrl Validate"
        subtitle="Industrial-grade Wind Turbine Controller Validation & Automated Reporting Toolkit built with Python, MATLAB, automated testing, and CI/CD."
      />

      {/* Main Core Showcase Card */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: 28,
          transform: `scale(${Math.max(0, titleProgress)})`,
          opacity: Math.min(1, titleProgress),
        }}
      >
        {/* Card 1 */}
        <div
          style={{
            backgroundColor: "#0f172a",
            borderRadius: 16,
            padding: 36,
            border: "1px solid #1e293b",
            display: "flex",
            flexDirection: "column",
            gap: 16,
            boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              backgroundColor: "rgba(14, 165, 233, 0.15)",
              color: "#38bdf8",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 24,
              fontWeight: 800,
            }}
          >
            ⚙️
          </div>
          <h3 style={{ fontSize: 24, fontWeight: 700, color: "#f8fafc", margin: 0 }}>
            NREL 5MW Aerodynamics
          </h3>
          <p style={{ fontSize: 16, color: "#94a3b8", lineHeight: 1.5, margin: 0 }}>
            Built around the certified NREL 5MW reference turbine (126m rotor, 1170.7 RPM generator, 43,093 Nm rated torque).
          </p>
        </div>

        {/* Card 2 */}
        <div
          style={{
            backgroundColor: "#0f172a",
            borderRadius: 16,
            padding: 36,
            border: "1px solid #1e293b",
            display: "flex",
            flexDirection: "column",
            gap: 16,
            boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              backgroundColor: "rgba(16, 185, 129, 0.15)",
              color: "#34d399",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 24,
              fontWeight: 800,
            }}
          >
            🛡️
          </div>
          <h3 style={{ fontSize: 24, fontWeight: 700, color: "#f8fafc", margin: 0 }}>
            Deterministic Rules
          </h3>
          <p style={{ fontSize: 16, color: "#94a3b8", lineHeight: 1.5, margin: 0 }}>
            7 strict domain validators evaluate signal health, pitch slew rates, torque lag filters, and IEC 61400-12 power curves.
          </p>
        </div>

        {/* Card 3 */}
        <div
          style={{
            backgroundColor: "#0f172a",
            borderRadius: 16,
            padding: 36,
            border: "1px solid #1e293b",
            display: "flex",
            flexDirection: "column",
            gap: 16,
            boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              backgroundColor: "rgba(245, 158, 11, 0.15)",
              color: "#fbbf24",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 24,
              fontWeight: 800,
            }}
          >
            📄
          </div>
          <h3 style={{ fontSize: 24, fontWeight: 700, color: "#f8fafc", margin: 0 }}>
            Dual-Engine Reports
          </h3>
          <p style={{ fontSize: 16, color: "#94a3b8", lineHeight: 1.5, margin: 0 }}>
            Auto-compiles formal LaTeX and ReportLab PDF certification audits with embedded 6-panel telemetry plots in CI/CD.
          </p>
        </div>
      </div>

      {/* Engineering Spec Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          backgroundColor: "rgba(15, 23, 42, 0.6)",
          border: "1px solid #1e293b",
          borderRadius: 12,
          padding: "20px 36px",
          transform: `translateY(${Math.max(0, (1 - cardsProgress) * 40)}px)`,
          opacity: Math.min(1, Math.max(0, cardsProgress)),
        }}
      >
        <span style={{ fontSize: 16, color: "#94a3b8" }}>
          Target: <strong style={{ color: "#38bdf8" }}>SIL & HIL Controller Verification</strong>
        </span>
        <span style={{ fontSize: 16, color: "#94a3b8" }}>
          Telemetry: <strong style={{ color: "#f8fafc" }}>11 SCADA Channels (10 Hz)</strong>
        </span>
        <span style={{ fontSize: 16, color: "#94a3b8" }}>
          Standards: <strong style={{ color: "#34d399" }}>IEC 61400-1 / 61400-12</strong>
        </span>
        <span style={{ fontSize: 16, color: "#94a3b8" }}>
          Stack: <strong style={{ color: "#f8fafc" }}>Python 3.12 · FastAPI · MATLAB · React 18</strong>
        </span>
      </div>
    </div>
  );
};
