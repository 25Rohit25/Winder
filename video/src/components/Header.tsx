import React from "react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  category?: string;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, category = "WIND TURBINE CONTROLLER VALIDATION" }) => {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 28 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: "#0ea5e9",
            boxShadow: "0 0 12px #0ea5e9",
          }}
        />
        <span
          style={{
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: "0.15em",
            color: "#38bdf8",
            textTransform: "uppercase",
            fontFamily: "system-ui, -apple-system, sans-serif",
          }}
        >
          {category}
        </span>
      </div>
      <h1
        style={{
          fontSize: 54,
          fontWeight: 800,
          color: "#f8fafc",
          letterSpacing: "-0.02em",
          margin: 0,
          fontFamily: "system-ui, -apple-system, sans-serif",
        }}
      >
        {title}
      </h1>
      {subtitle && (
        <p
          style={{
            fontSize: 22,
            color: "#94a3b8",
            margin: 0,
            maxWidth: 1200,
            lineHeight: 1.4,
            fontFamily: "system-ui, -apple-system, sans-serif",
          }}
        >
          {subtitle}
        </p>
      )}
    </div>
  );
};
