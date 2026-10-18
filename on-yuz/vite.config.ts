import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

/*  YENİ ÖN YÜZ — /yeni altında.
    Geliştirme:  npm run dev  →  http://localhost:5174/yeni/  ( /api istekleri
    FastAPI'ye, 8790 — .claude/launch.json "program" ).
    Yayın:  npm run build  →  dist/  ;  FastAPI /yeni altında sunar ( hesap/main.py ).
    Hesap ve çizim Python'da;  burada yalnız kabuk.                            */
export default defineConfig({
  base: "/yeni/",
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "src") } },
  server: { proxy: { "/api": "http://localhost:8790" } },
  build: { outDir: "dist", emptyOutDir: true },
});
