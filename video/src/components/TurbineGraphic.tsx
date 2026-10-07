import React from "react";

interface TurbineGraphicProps {
  rotationDeg: number;
  alert?: boolean;
  size?: number;
}

export const TurbineGraphic: React.FC<TurbineGraphicProps> = ({ rotationDeg, alert = false, size = 320 }) => {
  const accentColor = alert ? "#ef4444" : "#38bdf8";
  const glowColor = alert ? "rgba(239, 68, 68, 0.4)" : "rgba(56, 189, 248, 0.25)";

  return (
    <div
      style={{
        position: "relative",
        width: size,
        height: size * 1.3,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-end",
      }}
    >
      {/* Tower */}
      <svg
        width={size}
        height={size * 1.3}
        viewBox="0 0 200 260"
        style={{ position: "absolute", bottom: 0, overflow: "visible" }}
      >
        {/* Tower Base & Column */}
        <polygon points="94,90 85,250 115,250 106,90" fill="#334155" stroke="#475569" strokeWidth="2" />
        <line x1="80" y1="250" x2="120" y2="250" stroke="#64748b" strokeWidth="4" />
        {/* Foundation Rings */}
        <ellipse cx="100" cy="250" rx="28" ry="6" fill="#1e293b" stroke="#475569" strokeWidth="2" />

        {/* Nacelle */}
        <rect x="85" y="78" width="45" height="18" rx="6" fill="#1e293b" stroke={accentColor} strokeWidth="2" />
        <circle cx="100" cy="87" r="10" fill="#0f172a" stroke={accentColor} strokeWidth="2" />
      </svg>

      {/* Rotating Hub and 3 Blades */}
      <div
        style={{
          position: "absolute",
          top: size * 0.435,
          left: size * 0.5,
          transform: `translate(-50%, -50%) rotate(${rotationDeg}deg)`,
          width: 0,
          height: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Hub Cap */}
        <div
          style={{
            position: "absolute",
            width: 22,
            height: 22,
            borderRadius: "50%",
            backgroundColor: "#0f172a",
            border: `3px solid ${accentColor}`,
            boxShadow: `0 0 16px ${glowColor}`,
            zIndex: 10,
          }}
        />

        {/* 3 Blades spaced at 120 degrees */}
        {[0, 120, 240].map((angle, idx) => (
          <div
            key={idx}
            style={{
              position: "absolute",
              width: 8,
              height: size * 0.48,
              transformOrigin: "bottom center",
              transform: `rotate(${angle}deg) translateY(-${size * 0.48}px)`,
              background: `linear-gradient(to top, ${accentColor}, #ffffff)`,
              borderRadius: "4px 4px 1px 1px",
              boxShadow: `0 0 10px ${glowColor}`,
            }}
          />
        ))}
      </div>
    </div>
  );
};
