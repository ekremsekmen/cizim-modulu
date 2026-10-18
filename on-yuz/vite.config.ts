import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

/*  ÖN YÜZ — programın kökünde ( / ).
    Geliştirme:  npm run dev  →  http://localhost:5174/  ( /api istekleri ve
    çizim yazı tipi /yazi FastAPI'ye, 8790 — .claude/launch.json "program" ).
    Yayın:  npm run build  →  dist/  ;  FastAPI kökte sunar ( hesap/main.py ).
    Hesap ve çizim Python'da;  burada yalnız kabuk.                            */
export default defineConfig({
  base: "/",
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "src") } },
  server: { proxy: { "/api": "http://localhost:8790", "/yazi": "http://localhost:8790" } },
  build: { outDir: "dist", emptyOutDir: true },
});
