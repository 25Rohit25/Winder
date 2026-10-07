import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";

export const Scene6_Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
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
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "system-ui, -apple-system, sans-serif",
        boxSizing: "border-box",
        textAlign: "center",
        position: "relative",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 20,
          transform: `scale(${Math.max(0, scale)})`,
          maxWidth: 900,
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 10,
            backgroundColor: "rgba(14, 165, 233, 0.15)",
            border: "1px solid #0284c7",
            borderRadius: 30,
            padding: "8px 24px",
            color: "#38bdf8",
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
          }}
        >
          <span>PRODUCTION-READY CONTROLS TOOLKIT</span>
        </div>

        <h1
          style={{
            fontSize: 68,
            fontWeight: 900,
            color: "#f8fafc",
            letterSpacing: "-0.03em",
            margin: 0,
          }}
        >
          WindCtrl Validate
        </h1>

        <p
          style={{
            fontSize: 24,
            color: "#94a3b8",
            lineHeight: 1.5,
            margin: "0 0 20px 0",
          }}
        >
          Mathematically deterministic controller validation, 10 synthetic fault models, automated PDF audit reporting, and industrial SCADA visualization.
        </p>

        {/* Verification Badges */}
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap", justifyContent: "center" }}>
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #10b981",
              borderRadius: 10,
              padding: "10px 20px",
              color: "#34d399",
              fontSize: 16,
              fontWeight: 700,
            }}
          >
            ✓ 50/50 Automated Tests Passing
          </div>
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #38bdf8",
              borderRadius: 10,
              padding: "10px 20px",
              color: "#38bdf8",
              fontSize: 16,
              fontWeight: 700,
            }}
          >
            🐳 Docker Compose Verified
          </div>
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #818cf8",
              borderRadius: 10,
              padding: "10px 20px",
              color: "#a5b4fc",
              fontSize: 16,
              fontWeight: 700,
            }}
          >
            🚀 GitHub Actions & Jenkins CI/CD
          </div>
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #f59e0b",
              borderRadius: 10,
              padding: "10px 20px",
              color: "#fbbf24",
              fontSize: 16,
              fontWeight: 700,
            }}
          >
            📈 MATLAB .m Analysis Suite
          </div>
        </div>

        {/* GitHub Call to Action Card */}
        <div
          style={{
            marginTop: 32,
            backgroundColor: "#0f172a",
            border: "2px solid #38bdf8",
            borderRadius: 16,
            padding: "20px 48px",
            boxShadow: "0 0 30px rgba(56, 189, 248, 0.25)",
            display: "flex",
            alignItems: "center",
            gap: 20,
          }}
        >
          <span style={{ fontSize: 32 }}>⭐</span>
          <div style={{ textAlign: "left" }}>
            <div style={{ fontSize: 14, color: "#94a3b8", fontWeight: 600 }}>EXPLORE THE OPEN-SOURCE CODEBASE ON GITHUB</div>
            <div style={{ fontSize: 28, color: "#f8fafc", fontWeight: 800, letterSpacing: "-0.01em" }}>
              github.com/25Rohit25/Winder
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
