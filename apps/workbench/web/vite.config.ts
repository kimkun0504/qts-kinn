/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  plugins: [react(), tailwindcss()],
  server: { proxy: { "/api": "http://127.0.0.1:8321" } },
  test: { environment: "jsdom", globals: true },
});
