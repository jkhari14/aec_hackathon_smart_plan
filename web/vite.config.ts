import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// /api goes to the FastAPI server; with it down, src/api/client.ts falls back to ../contracts/fixtures.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // MapLibre 6 loads its worker relative to its own module; pre-bundling moves the module and breaks it.
  optimizeDeps: { exclude: ["maplibre-gl"] },
  server: {
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
    fs: { allow: [".."] },
  },
});
