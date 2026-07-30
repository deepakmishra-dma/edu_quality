import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig(async ({ command }) => {
  // The dev proxy reads the bench's sites/common_site_config.json, which only
  // exists inside a bench. Importing it lazily — and only when serving — keeps
  // `vite build` working in a clean checkout such as CI.
  const proxy =
    command === "serve" ? (await import("./proxyOptions")).default : undefined;

  return {
    plugins: [react()],
    server: {
      port: 8080,
      proxy,
    },
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "src"),
      },
    },
    build: {
      outDir: "../edu_quality/public/ui",
      emptyOutDir: true,
      target: "es2015",
    },
  };
});
