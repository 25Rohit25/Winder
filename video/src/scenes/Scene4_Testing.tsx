import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";
import { Header } from "../components/Header";

export const Scene4_Testing: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const leftProgress = spring({
    frame,
    fps,
    config: { damping: 12 },
  });

  const rightProgress = spring({
    frame: frame - 15,
    fps,
    config: { damping: 12 },
  });

  const boundaries = [
    { rpm: "14.49 RPM", status: "PASS", color: "#10b981", desc: "Strictly below operational ceiling" },
    { rpm: "14.50 RPM", status: "PASS", color: "#10b981", desc: "Exact boundary of operational envelope" },
    { rpm: "14.51 RPM", status: "WARNING", color: "#f59e0b", desc: "Exceeds envelope, enters safety buffer" },
    { rpm: "14.99 RPM", status: "WARNING", color: "#f59e0b", desc: "Advisory margin, approaching trip limit" },
    { rpm: "15.00 RPM", status: "WARNING", color: "#f59e0b", desc: "Exact hard trip boundary (inclusive)" },
    { rpm: "15.01 RPM", status: "FAIL", color: "#ef4444", desc: "Emergency overspeed breach -> Hard Trip!" },
  ];

  const faults = [
    { title: "Blade Pitch Actuator Delay", icon: "⏱️", desc: "Simulates 1.5s electro-hydraulic valve lag" },
    { title: "SCADA Sensor Dropout & NaN", icon: "📡", desc: "Simulates communication loss & missing samples" },
    { title: "Zero-Variance Sensor Freeze", icon: "❄️", desc: "Detects stuck shaft encoders and pitch sensors" },
    { title: "Converter Torque Spikes", icon: "⚡", desc: "Catches >15,000 Nm/s drivetrain shock impulses" },
    { title: "IEC Power Underperformance", icon: "📉", desc: "Detects aerodynamic blade degradation & icing" },
  ];

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#080c16",
        padding: "60px 80px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        fontFamily: "system-ui, -apple-system, sans-serif",
        boxSizing: "border-box",
      }}
    >
      <Header
        category="RIGOROUS VERIFICATION & FAULT INJECTION"
        title="Exact Boundary & Fault Models"
        subtitle="Mathematical verification: proving zero false positives on baseline runs and 100% detection of injected anomalies."
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 36 }}>
        {/* Left: Boundary Matrix */}
        <div
          style={{
            backgroundColor: "#0f172a",
            borderRadius: 16,
            border: "1px solid #1e293b",
            padding: 28,
            display: "flex",
            flexDirection: "column",
            gap: 14,
            transform: `scale(${Math.max(0, leftProgress)})`,
            boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <span style={{ fontSize: 18, fontWeight: 700, color: "#f8fafc" }}>
              Exact Threshold Boundary Tests
            </span>
            <span style={{ fontSize: 13, color: "#38bdf8", fontWeight: 600 }}>pytest Parametrized</span>
          </div>

          {boundaries.map((b, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                backgroundColor: "#1e293b",
                borderRadius: 8,
                padding: "8px 16px",
                borderLeft: `4px solid ${b.color}`,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <span style={{ fontSize: 16, fontWeight: 800, color: "#f8fafc", width: 90 }}>{b.rpm}</span>
                <span style={{ fontSize: 13, color: "#94a3b8" }}>{b.desc}</span>
              </div>
              <span
                style={{
                  fontSize: 12,
                  fontWeight: 800,
                  color: "#ffffff",
                  backgroundColor: b.color,
                  padding: "4px 10px",
                  borderRadius: 12,
                }}
              >
                {b.status}
              </span>
            </div>
          ))}
        </div>

        {/* Right: Fault Models */}
        <div
          style={{
            backgroundColor: "#0f172a",
            borderRadius: 16,
            border: "1px solid #1e293b",
            padding: 28,
            display: "flex",
            flexDirection: "column",
            gap: 14,
            transform: `scale(${Math.max(0, rightProgress)})`,
            boxShadow: "0 10px 30px rgba(0,0,0,0.4)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
            <span style={{ fontSize: 18, fontWeight: 700, color: "#f8fafc" }}>
              10 Controlled Synthetic Fault Models
            </span>
            <span style={{ fontSize: 13, color: "#34d399", fontWeight: 600 }}>100% Detection Rate</span>
          </div>

          {faults.map((f, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                backgroundColor: "#1e293b",
                borderRadius: 8,
                padding: "10px 16px",
              }}
            >
              <span style={{ fontSize: 20 }}>{f.icon}</span>
              <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                <span style={{ fontSize: 15, fontWeight: 700, color: "#f8fafc" }}>{f.title}</span>
                <span style={{ fontSize: 12, color: "#94a3b8" }}>{f.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ textAlign: "center", color: "#64748b", fontSize: 15 }}>
        Hypothesis Property-Based Testing · Zero False-Positives on Baseline Golden Datasets
      </div>
    </div>
  );
};
