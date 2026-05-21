# Frontend

Next.js 15 (App Router) with TypeScript and Tailwind.

## Dev

```bash
make setup-frontend
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
├─ plan/page.tsx           main panel (calendar + score card)
├─ history/page.tsx        plan history
└─ settings/page.tsx       preferences

components/
├─ Calendar/               week grid
├─ ScoreCard/              score visualization
├─ ReplanDrawer/           replan controls + diff
├─ DiffView/               old vs new plan diff
└─ ExplainDrawer/          constraint hits + score breakdown

lib/
├─ types.ts                mirrors backend Pydantic models
└─ api.ts                  typed REST client
```
