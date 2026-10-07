import React from "react";
import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { Header } from "../components/Header";
import { TurbineGraphic } from "../components/TurbineGraphic";

export const Scene1_Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // RPM accelerates from 11.2 up to 15.01
  const rpm = interpolate(frame, [0, 80, 150, 200], [11.2, 14.5, 14.99, 15.01], {
    extrapolateRight: "clamp",
  });

  const isTrip = rpm >= 15.01;
  const isWarning = rpm >= 14.51 && !isTrip;

  // Rotation increases with RPM
  const rotationDeg = frame * (rpm * 0.85);

  const alertOpacity = isTrip ? (Math.sin(frame * 0.5) > 0 ? 1 : 0.4) : 0;

  const cardScale = spring({
    frame,
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
        border: isTrip ? "6px solid rgba(239, 68, 68, 0.8)" : "none",
        boxSizing: "border-box",
      }}
    >
      <Header
        category="SAFETY-CRITICAL CONTROLS VALIDATION"
        title="What happens at 15.01 RPM?"
        subtitle="In a multi-megawatt wind turbine, a 0.01 RPM error represents the boundary between certified operation and catastrophic drivetrain destruction."
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-around",
          transform: `scale(${cardScale})`,
        }}
      >
        {/* Turbine Graphic */}
        <TurbineGraphic rotationDeg={rotationDeg} alert={isTrip} size={360} />

        {/* Telemetry Gauge & Alert Card */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 24,
            width: 580,
            backgroundColor: "#0f172a",
            border: `2px solid ${isTrip ? "#ef4444" : isWarning ? "#f59e0b" : "#1e293b"}`,
            borderRadius: 16,
            padding: 36,
            boxShadow: isTrip
              ? "0 0 40px rgba(239, 68, 68, 0.35)"
              : "0 20px 40px rgba(0,0,0,0.5)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: 18, color: "#94a3b8", fontWeight: 600 }}>ROTOR SPEED TELEMETRY</span>
            <span
              style={{
                fontSize: 14,
                padding: "6px 14px",
                borderRadius: 20,
                fontWeight: 700,
                backgroundColor: isTrip ? "#ef4444" : isWarning ? "#f59e0b" : "#10b981",
                color: "#ffffff",
              }}
            >
              {isTrip ? "HARD TRIP" : isWarning ? "ADVISORY MARGIN" : "NOMINAL"}
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
            <span
              style={{
                fontSize: 84,
                fontWeight: 900,
                color: isTrip ? "#ef4444" : isWarning ? "#fbbf24" : "#38bdf8",
                letterSpacing: "-0.04em",
              }}
            >
              {rpm.toFixed(2)}
            </span>
            <span style={{ fontSize: 32, fontWeight: 700, color: "#64748b" }}>RPM</span>
          </div>

          {/* Progress Bar with safety markers */}
          <div style={{ width: "100%", height: 14, backgroundColor: "#1e293b", borderRadius: 8, overflow: "hidden", position: "relative" }}>
            <div
              style={{
                width: `${Math.min(100, ((rpm - 10) / 6) * 100)}%`,
                height: "100%",
                backgroundColor: isTrip ? "#ef4444" : isWarning ? "#f59e0b" : "#0284c7",
                transition: "width 0.1s linear",
              }}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#64748b" }}>
            <span>Rated: 12.1 RPM</span>
            <span>Advisory Limit: 14.50 RPM</span>
            <span style={{ color: "#ef4444", fontWeight: 700 }}>Trip Limit: 15.00 RPM</span>
          </div>

          {/* Flash Warning Box */}
          {isTrip && (
            <div
              style={{
                backgroundColor: "rgba(239, 68, 68, 0.15)",
                border: "1px solid #ef4444",
                borderRadius: 8,
                padding: 16,
                opacity: alertOpacity,
                display: "flex",
                flexDirection: "column",
                gap: 6,
              }}
            >
              <span style={{ fontSize: 16, fontWeight: 800, color: "#fca5a5" }}>
                [CRITICAL TRIP] IEC 61400 OVERSPEED LIMIT BREACHED
              </span>
              <span style={{ fontSize: 14, color: "#f87171" }}>
                Rotor speed exceeded 15.00 RPM. Aerodynamic pitch feathering & mechanical braking initiated.
              </span>
            </div>
          )}
        </div>
      </div>

      <div style={{ textAlign: "center", color: "#64748b", fontSize: 18, fontWeight: 500 }}>
        NREL 5MW Baseline Turbine · 11-Channel Continuous SCADA Telemetry Stream
      </div>
    </div>
  );
};
