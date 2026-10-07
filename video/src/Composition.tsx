import React from "react";
import { Sequence } from "remotion";
import { Scene1_Hook } from "./scenes/Scene1_Hook";
import { Scene2_Intro } from "./scenes/Scene2_Intro";
import { Scene3_Architecture } from "./scenes/Scene3_Architecture";
import { Scene4_Testing } from "./scenes/Scene4_Testing";
import { Scene5_Dashboard } from "./scenes/Scene5_Dashboard";
import { Scene6_Outro } from "./scenes/Scene6_Outro";

export const WindCtrlExplainer: React.FC = () => {
  return (
    <div style={{ flex: 1, backgroundColor: "#080c16", width: "100%", height: "100%" }}>
      {/* Scene 1: Problem / Overspeed Hook (0s - 7s) */}
      <Sequence from={0} durationInFrames={210} name="Scene 1: 15.01 RPM Hook">
        <Scene1_Hook />
      </Sequence>

      {/* Scene 2: WindCtrl Validate Intro (7s - 14s) */}
      <Sequence from={210} durationInFrames={210} name="Scene 2: Solution Intro">
        <Scene2_Intro />
      </Sequence>

      {/* Scene 3: Modular Architecture Flow (14s - 24s) */}
      <Sequence from={420} durationInFrames={300} name="Scene 3: Architecture Pipeline">
        <Scene3_Architecture />
      </Sequence>

      {/* Scene 4: Testing & Exact Boundaries (24s - 32s) */}
      <Sequence from={720} durationInFrames={240} name="Scene 4: Boundary & Faults">
        <Scene4_Testing />
      </Sequence>

      {/* Scene 5: Dashboard & PDF Audit Reports (32s - 40s) */}
      <Sequence from={960} durationInFrames={240} name="Scene 5: Dashboard & Reports">
        <Scene5_Dashboard />
      </Sequence>

      {/* Scene 6: Outro & GitHub CTA (40s - 45s) */}
      <Sequence from={1200} durationInFrames={150} name="Scene 6: Production Outro">
        <Scene6_Outro />
      </Sequence>
    </div>
  );
};
