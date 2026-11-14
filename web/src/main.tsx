import "maplibre-gl/dist/maplibre-gl.css";
import "./app.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { PreflightApp } from "./app/preflight_app";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <PreflightApp />
  </StrictMode>,
);
