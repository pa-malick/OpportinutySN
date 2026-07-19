import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// Config Vite minimale : le plugin Vue suffit, Tailwind passe par PostCSS.
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    open: true,
  },
});
