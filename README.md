# OmniTest Frontend

AI-assisted exam preparation SPA for GED and Digital SAT learners, built with **SolidJS 2.0.3**, **Vite 8**, **Tailwind CSS v4**, and **Bun**. Connects directly to the deployed FastAPI backend at `https://omnitest-6fed.onrender.com` without duplicating grading, filtering, pagination, rubric clamping, or authorization on the client.

## Stack

- **Framework & Routing:** `solid-js@^2.0.3`, `@solidjs/web@^2.0.3`, `@solidjs/router@^2.0.1`
- **Styling:** Tailwind CSS v4 (`@tailwindcss/vite`, `@theme inline`), Liquid Glass navigation/modals, solid readable study panels, `:has(> head > meta[name="color-scheme"])` zero-FOUC light/dark/system theme switching
- **API & Types:** `openapi-fetch` + generated OpenAPI types in `src/api/schema.d.ts` (`openapi-typescript`)
- **UI & Visualization:** `@lucide/solid`, `chart.js`, `@formkit/auto-animate`, `marked` + `marked-katex-extension` + native `Element.setHTML()` with lazy `dompurify` fallback

## Local Development

```bash
cp .env.example .env
bun install
bun run dev
```

Vite serves on `http://localhost:5173` and proxies `/api/*` directly to `https://omnitest-6fed.onrender.com` so local dev works with an empty `VITE_API_BASE_URL` and no CORS issues.

## Scripts

- `bun run dev` — Start Vite dev server with Render API proxy
- `bun run typecheck` — Run `tsc --noEmit`
- `bun run build` — Production build to `dist/`
- `bun run preview` — Preview production bundle locally
- `bun run api:types` — Regenerate `src/api/schema.d.ts` from `https://omnitest-6fed.onrender.com/openapi.json`

## Static Deployment (Cloudflare Pages / Vercel)

1. Build command: `bun run build` (output directory: `dist`)
2. Set environment variables:
   - `VITE_API_BASE_URL=https://omnitest-6fed.onrender.com/api/v1`
   - `VITE_SHOW_DEMO_LOGIN=true` (or `false` to hide 1-click demo buttons)
3. Ensure your deployed origin URL is included in the backend `CORS_ORIGINS` setting on Render, and configure SPA fallback routing (`/* -> /index.html`).
