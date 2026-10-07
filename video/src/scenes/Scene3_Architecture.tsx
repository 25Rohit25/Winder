import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";
import { Header } from "../components/Header";

interface NodeProps {
  step: number;
  title: string;
  subtitle: string;
  icon: string;
  delay: number;
  highlight?: boolean;
}

const ArchNode: React.FC<NodeProps> = ({ step, title, subtitle, icon, delay, highlight = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - delay,
    fps,
    config: { damping: 12 },
  });

  const opacity = Math.min(1, Math.max(0, progress));
  const scale = Math.max(0, progress);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        opacity,
        transform: `scale(${scale})`,
        width: 280,
      }}
    >
      <div
        style={{
          width: 72,
          height: 72,
          borderRadius: 20,
          backgroundColor: highlight ? "rgba(14, 165, 233, 0.2)" : "#1e293b",
          border: `2px solid ${highlight ? "#38bdf8" : "#475569"}`,
          boxShadow: highlight ? "0 0 24px rgba(56, 189, 248, 0.35)" : "none",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 32,
        }}
      >
        {icon}
      </div>
      <div
        style={{
          backgroundColor: "#0f172a",
          border: `1px solid ${highlight ? "#0284c7" : "#1e293b"}`,
          borderRadius: 12,
          padding: "16px 20px",
          width: "100%",
          textAlign: "center",
          display: "flex",
          flexDirection: "column",
          gap: 6,
          boxShadow: "0 10px 20px rgba(0,0,0,0.4)",
        }}
      >
        <span style={{ fontSize: 12, color: highlight ? "#38bdf8" : "#64748b", fontWeight: 700, letterSpacing: "0.1em" }}>
          STAGE 0{step}
        </span>
        <span style={{ fontSize: 18, color: "#f8fafc", fontWeight: 700 }}>{title}</span>
        <span style={{ fontSize: 13, color: "#94a3b8", lineHeight: 1.3 }}>{subtitle}</span>
      </div>
    </div>
  );
};

export const Scene3_Architecture: React.FC = () => {
  const frame = useCurrentFrame();

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
        category="MODULAR DETERMINISTIC ARCHITECTURE"
        title="Automated Validation Pipeline"
        subtitle="End-to-end telemetry flow: from continuous 10 Hz SCADA signals to mathematically verified release gates."
      />

      {/* 5 Sequential Architecture Nodes with Animated Connector Line */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          position: "relative",
          margin: "40px 0",
        }}
      >
        {/* Background Connecting Line */}
        <div
          style={{
            position: "absolute",
            top: 36,
            left: 80,
            right: 80,
            height: 4,
            backgroundColor: "#1e293b",
            zIndex: 0,
          }}
        >
          {/* Animated Glow Flow */}
          <div
            style={{
              position: "absolute",
              top: -2,
              height: 8,
              width: 120,
              borderRadius: 4,
              backgroundColor: "#38bdf8",
              boxShadow: "0 0 16px #38bdf8",
              left: `${(frame * 1.5) % 100}%`,
            }}
          />
        </div>

        <div style={{ zIndex: 1 }}>
          <ArchNode
            step={1}
            title="Telemetry Ingest"
            subtitle="11 SCADA channels, sampling sanity, schema validation"
            icon="📡"
            delay={0}
          />
        </div>

        <div style={{ zIndex: 1 }}>
          <ArchNode
            step={2}
            title="Signal Quality"
            subtitle="NaN dropout, time monotonicity, zero-variance freeze"
            icon="🔍"
            delay={15}
          />
        </div>

        <div style={{ zIndex: 1 }}>
          <ArchNode
            step={3}
            title="7 Rule Engines"
            subtitle="Overspeed, Rotor, Pitch slew, Torque lag, Power curve, Yaw"
            icon="⚙️"
            delay={30}
            highlight
          />
        </div>

        <div style={{ zIndex: 1 }}>
          <ArchNode
            step={4}
            title="Evidence & Score"
            subtitle="Deterministic 0-100 index, pass/warn/fail triage"
            icon="📊"
            delay={45}
          />
        </div>

        <div style={{ zIndex: 1 }}>
          <ArchNode
            step={5}
            title="CI / PDF / UI"
            subtitle="Signed LaTeX/PDF certificate, React dashboard, GitHub CI"
            icon="🚀"
            delay={60}
            highlight
          />
        </div>
      </div>

      {/* Bottom Architectural Callout */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          backgroundColor: "#0f172a",
          border: "1px solid #1e293b",
          borderRadius: 12,
          padding: "18px 32px",
        }}
      >
        <span style={{ fontSize: 16, color: "#cbd5e1" }}>
          ⚡ <strong>Full Execution Speed:</strong> A complete 10-minute simulation dataset (6,000 samples) validates in <strong>&lt; 25 ms</strong>.
        </span>
        <span style={{ fontSize: 14, color: "#38bdf8", fontWeight: 700 }}>
          ZERO FLAKINESS · 100% REPRODUCIBLE · MATHEMATICALLY TRACEABLE
        </span>
      </div>
    </div>
  );
};
