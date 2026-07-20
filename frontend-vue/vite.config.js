import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  // Served under /studio/ in the assembled static bundle (see scripts/assemble-static.sh)
  base: "/studio/",
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 5173
  }
});
