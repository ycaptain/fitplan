# Frontend

Next.js 15 (App Router) with TypeScript and Tailwind.

Package manager: **pnpm 11** (pinned via `packageManager` in `package.json`).
Install once: `npm install -g pnpm@11` or `corepack enable`.

## Dev

```bash
make setup-frontend       # pnpm install
make frontend             # http://localhost:3000
```

`/api/*` is proxied to `http://localhost:8000` via `next.config.js`, so
run `make backend` and `make frontend` in two terminals.

## Layout

```
app/
├─ layout.tsx              root layout
├─ page.tsx                landing
├─ onboarding/page.tsx     onboarding wizard
├─ plan/page.tsx           main panel (calendar + replan flow)
├─ history/page.tsx        plan history
└─ settings/page.tsx       preferences

components/
└─ Calendar/               drag-to-create weekly grid

lib/
├─ types.ts                mirrors backend Pydantic models
└─ api.ts                  typed REST client
```
