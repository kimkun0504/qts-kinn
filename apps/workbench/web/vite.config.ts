/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss()],
  server: { proxy: { "/api": "http://127.0.0.1:8321" } },
  build: {
    rollupOptions: {
      output: {
        // The Lab's code editor in a file of its own, loaded only when the Lab opens.
        manualChunks: (id) => (/node_modules\/(@codemirror|@lezer|codemirror|crelt|style-mod|w3c-keyname)/.test(id) ? "editor" : undefined),
      },
    },
  },
  test: { environment: "jsdom", globals: true },
});
