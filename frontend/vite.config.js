import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendTarget = env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8005";
  const port = Number(env.VITE_DEV_PORT || 5173);

  return {
    plugins: [react()],
    server: {
      port,
      proxy: {
        "/rag": {
          target: backendTarget,
          changeOrigin: true
        },
        "/auth": {
          target: backendTarget,
          changeOrigin: true
        },
        "/chats": {
          target: backendTarget,
          changeOrigin: true
        }
      }
    }
  };
});
