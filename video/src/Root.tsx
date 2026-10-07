import React from "react";
import { Composition } from "remotion";
import { WindCtrlExplainer } from "./Composition";

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="WindCtrlExplainer"
        component={WindCtrlExplainer}
        durationInFrames={1350} // 45 seconds at 30 fps
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{}}
      />
    </>
  );
};
