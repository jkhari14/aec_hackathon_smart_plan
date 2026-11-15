import "maplibre-gl/dist/maplibre-gl.css";
import "../../app.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { CityMap } from "../city_map/CityMap";
import { WarningsPanel } from "./WarningsPanel";

const params = new URLSearchParams(window.location.search);
const bbl = params.get("bbl") ?? "3052110074";
const asOf = params.get("as_of") ?? undefined;

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <main className="relative h-full overflow-hidden">
      <CityMap features={[]} />
      <div className="absolute right-4 top-4">
        <WarningsPanel bbl={bbl} asOf={asOf} />
      </div>
    </main>
  </StrictMode>,
);
