// Build alternativo che produce un singolo index.html autonomo
// (JS e CSS inline), usato per il deploy via import su Vercel.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir: "dist-single",
  },
});
