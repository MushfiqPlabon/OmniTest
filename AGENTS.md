# OmniTest Frontend Engineering Guide (`frontend` Branch)

## 1. Overview & Branch Scope

- **Purpose:** Single-page web client for **OmniTest** (AI-assisted GED & Digital SAT exam preparation: AI Tutor chat with RAG citations, practice quizzes, rubric-graded essays, study library with LaTeX rendering, and score analytics).
- **Frontend-Only Branch:** The `frontend` branch contains only the SPA client. The FastAPI backend lives on `main` and is deployed at `https://omnitest-6fed.onrender.com`. Keep `LICENSE` (`AGPL-3.0-only`) and `NOTICE` intact.
- **Agent Tooling:** `AGENTS.md` and `skills-lock.json` are tracked in Git as shared context and pinned skill metadata; local IDE/agent install folders (`.agents/`, `.claude/`, `.kiro/`, `.cursor/`, `.codex/`, `.gemini/`, `.windsurf/`, `.opencode/`, `.roo/`) are gitignored.

## 2. Tech Stack, Commands & Environment

- **Runtime & Build:** Bun (`^1.4`), Vite (`^8.3.8`), TypeScript (`^5.9.0`, strict mode), Tailwind CSS v4 (`@tailwindcss/vite`).
- **UI & Libraries:** `solid-js@^2.0.3`, `@solidjs/web@^2.0.3`, `@solidjs/router@^2.0.1`, `@lucide/solid`, `openapi-fetch`, `openapi-typescript`, `chart.js`, `marked`, `marked-katex-extension`, `katex`, `dompurify`, `@formkit/auto-animate`.
- **Scripts (`package.json`):**
  - `bun install` — install dependencies
  - `bun run dev` — start Vite dev server on `http://localhost:5173` (proxies `/api/*`)
  - `bun run typecheck` — run `tsc --noEmit` across `src/` and `vite.config.ts`
  - `bun run build` — build production bundle into `dist/`
  - `bun run preview` — preview built `dist/` locally
  - `bun run api:types` — regenerate `src/api/schema.d.ts` from `https://omnitest-6fed.onrender.com/openapi.json`
- **Environment Variables (`.env` / `.env.example`):**
  - `VITE_API_BASE_URL` — leave empty in local dev so Vite proxies `/api/*` cleanly; set to `https://omnitest-6fed.onrender.com/api/v1` on Cloudflare Pages / Vercel static builds.
  - `VITE_SHOW_DEMO_LOGIN` — `"true"` enables 1-click Demo Student / Demo Admin sign-in controls; `"false"` hides them.
  - `VITE_DEV_PROXY_TARGET` — optional `vite.config.ts` (`loadEnv`) override for `/api` proxy target during local/mock dev testing (defaults to `https://omnitest-6fed.onrender.com`).

## 3. Repository & Source Layout

- Root config: `index.html` (zero-FOUC color-scheme inline sync, inline SVG favicon, Google Fonts), `vite.config.ts`, `tsconfig.json`, `.env.example`, `skills-lock.json`.
- `src/index.tsx` — mounts `App` via `@solidjs/web` `render()`, initializes `initThemeSync()`, wraps `ToastProvider` -> `AuthProvider`, gates routes inside `<Errored><Loading><Show when={auth.user()}>` with `createRouter` + `defineRoutes`.
- `src/api/` — `client.ts` (`openapi-fetch` client, `API_ORIGIN` normalization, auth bearer injection, `unwrap`, `uploadMaterialFile`) and generated `schema.d.ts` (never edit manually).
- `src/state/` — `auth.tsx` (JWT persistence & async `user` memo), `theme.ts` (`schemePref`, `resolvedScheme`, `cycleColorScheme`, `initThemeSync`), `filters.ts` (`usePagedFilters` URL search-param hook), `toast.tsx` (transient notifications).
- `src/styles/` — `tokens.css` (OKLCH light/dark palette & `@theme inline` tokens) and `glass.css` (`.glass-surface`, `.reading-surface`, `.glass-btn`, `.card-hover`, `.glass-dialog`, `.tabular-nums`, reduced-motion/transparency rules).
- `src/components/`:
  - Shared: `AppShell.tsx`, `NavLinks.tsx`, `ThemeToggle.tsx`, `GlassDialog.tsx`, `MarkdownView.tsx`, `FilterBar.tsx`, `Pagination.tsx`, `ScoreChart.tsx`, `States.tsx`, `ToastHost.tsx`.
  - Feature subfolders: `admin/{AdminBanner,AdminMaterialsTable,AdminPromptsTable,AdminQuizzesPanel,AdminTabs,QuizAttemptsDialog,QuizEditDialog}.tsx`, `analytics/{chartConfigs.ts,RecentActivity.tsx}`, `auth/AuthHero.tsx`, `chat/ChatMessageList.tsx`, `quizzes/{QuizRunner,QuizResults,QuizAdminDialog}.tsx`, `essays/{EssayPromptCard,EssayWorkspace,EssayFeedback,EssayHistoryList,EssayRubricFields,EssayAdminDialog}.tsx`, `materials/{MaterialReader,MaterialCard,MaterialForm,MaterialAdminActions,MaterialAdminDialog,materialSave.ts}`.
- `src/pages/` — `AuthPage.tsx`, `AdminPage.tsx`, `ChatPage.tsx`, `QuizzesPage.tsx`, `EssaysPage.tsx`, `MaterialsPage.tsx`, `AnalyticsPage.tsx`.

## 4. SolidJS 2.0.3 Patterns & Dev-Mode Invariants

Solid 2.0's dev runtime strictly enforces reactive invariants (reference `node_modules/solid-js/skills/reactivity-diagnostics/SKILL.md` for `[CODE]` troubleshooting):

- **Package Imports:** Import core primitives (`createSignal`, `createMemo`, `createEffect`, `onSettled`, `refresh`, `Show`, `For`, `Loading`, `Errored`) from `"solid-js"`, JSX/render (`render`, `type JSX`) from `"@solidjs/web"`, routing from `"@solidjs/router"`, and icons from `"@lucide/solid"` (never `"solid-js/web"` or `"lucide-solid"`).
- **Forbidden Solid 1.x Patterns:** Never use `createResource`, `batch`, `classList`, `on:` / `use:` directives, single-argument `createEffect`, or prop destructuring (`function Comp({ x })`).
- **No Reactive Writes in Owned Scopes (`[REACTIVE_WRITE_IN_OWNED_SCOPE]`):** Never write signals/stores or call `refresh()` synchronously in component bodies, `createMemo`, or startup helpers called during render. Wrap mount-time DOM listeners/timers in `onSettled(() => { ... return () => cleanup(); })`.
- **Keep Prop Reads Tracked (`[STRICT_READ_UNTRACKED]`):** Always access `props.foo` inside JSX, memos, event handlers, or effects — never read or assign `const X = props.icon` in the component body. Pass renderable icons as `JSX.Element` props.
- **Avoid Relay/Loop Effects (`[EFFECT_RELAY_TEAR]`, `[EFFECT_WRITES_OWN_SOURCE]`):** Derive computed values with `createMemo` instead of `createEffect`; initialize resettable form fields via conditional mount (`<Show when={props.open}>`) + writable derived signals (`createSignal(() => props.editing?.title ?? "")`). Reserve 2-arg `createEffect(compute, apply)` strictly for imperative DOM/library sync (`<dialog>`, Chart.js, `setHTML`).
- **Async Memos:** Put `createMemo(async () => ...)` consumers inside `<Errored>` + `<Loading>` boundaries and read all reactive inputs synchronously **before** the first `await`.
- **DOM Attributes:** Use lowercase HTML attributes (`minlength`, `tabindex`), explicit `"true"` / `"false"` strings for boolean ARIA attributes (`aria-pressed`, `aria-selected`), and plain `string` `class` on `@lucide/solid` icons (`LucideProps['class']` does not accept `string[]`).

## 5. Styling, Liquid Glass & Web Platform Standards

- **Theme Tokens (`src/styles/tokens.css`):** Use the `@theme inline` classes only: `bg-canvas`, `bg-surface`, `bg-brand`, `text-brand`, `text-brand-ink`, `bg-accent`, `text-accent`, `text-ink`, `text-muted`, `border-edge`, `text-ok`, `bg-ok`, `text-danger`, `bg-danger` (with opacity modifiers like `bg-brand/15` when needed). Do not invent unconfigured utility classes (`glass-card`, `glass-input`, etc.).
- **Surface Hierarchy (`src/styles/glass.css`):** Use `.glass-surface` ONLY for floating chrome (header bar, modal dialogs, toast notifications, quiz results banner) and `.reading-surface` for solid content cards, chat messages, and study prose (`max-w-[74ch]`). Never nest glass inside glass.
- **Modern Web Standards:**
  - Dual-mode `:has(> head > meta[name="color-scheme"])` + `light-dark()` CSS for zero-FOUC light/dark/system switching.
  - Native `<dialog closedby="any">` in `GlassDialog.tsx` with `closedBy` feature-detection fallback, `@starting-style` + separate `transition-behavior: allow-discrete`.
  - `document.startViewTransition()` in `AppShell.tsx` restoring focus to `#page-heading` while catching `.ready`, `.updateCallbackDone`, and `.finished` (`AbortError` on rapid navigation).
  - Native `Element.prototype.setHTML()` in `MarkdownView.tsx` with lazy dynamic `import("dompurify")` fallback (`ALLOW_ARIA_ATTR: false`, `ALLOW_DATA_ATTR: false`, `KEEP_CONTENT: false`).

## 6. API Boundary & Engineering Rules

- **Strict DRY / KISS / YAGNI:** Never duplicate server responsibilities on the client — no client-side quiz grading, rubric clamping, keyword filtering/sorting of paged lists, client-side RAG chunking, or role spoofing.
- **URL Search-Param Patching (`src/state/filters.ts`):** When updating query filters, patch only changed keys + `page: undefined` so combining search, subject, and difficulty preserves active filters.
- **OpenAPI Paths:** `src/api/schema.d.ts` keys include `/api/v1/...`, while `API_ORIGIN` strips any trailing `/api/v1`. Always pass full OpenAPI paths (`"/api/v1/quizzes"`, `"/api/v1/essays/prompts/{prompt_id}/submit"`, etc.) to `api.GET/POST/PATCH/DELETE`.
- **File Modularity:** Keep every handcrafted file under `src/` concise and `<= 150` lines (extract subcomponents or chart/config helpers rather than growing monolithic files).

## 7. Verification Checklist Before Committing

1. Line-limit audit: verify all handcrafted `src/` files (excluding `src/api/schema.d.ts`) are `<= 150` lines.
2. Lint & format (`biome.json`): `bunx @biomejs/biome check .` exits `0` with zero warnings or errors.
3. Static check & bundle: `bun run typecheck` and `bun run build` both exit `0`.
4. Dev-mode verification: test interactively under `bun run dev` (Solid dev runtime) rather than relying solely on `dist/` — confirm zero console errors, zero uncaught promise rejections, and zero Solid 2 dev diagnostic warnings (`[CODE]`).
