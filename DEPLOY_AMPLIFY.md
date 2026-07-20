# Deploy to AWS Amplify (frontend-only mock)

This repo is set up to deploy as a **static, frontend-only demo** on AWS Amplify
Hosting. There is no backend: every `/api/*` call is intercepted in the browser
by `frontend/mock-api.js` and served from seeded data persisted in
localStorage. MongoDB, FastAPI and Docker are NOT needed for this mode.

## One-time setup

1. Amplify Console -> Host web app -> connect this GitHub repo and branch.
2. Amplify auto-detects `amplify.yml` at the repo root. No overrides needed.
3. Deploy. Done - no environment variables, no secrets.

The build does two things (see `amplify.yml` + `scripts/assemble-static.sh`):

- `frontend-vue` is built with Vite (base path `/studio/`).
- Everything is assembled into `dist/`:
  - `/` demo hub (role shortcuts, page index, reset button)
  - `/login.html`, `/user-store.html`, `/order-history.html`,
    `/user-profile.html`, `/provider-panel.html`, `/admin-dashboard.html`
  - `/studio/` the Vue admin studio
  - `/frontend-assets/` shared scripts (`i18n.js`, `mock-api.js`)

## Demo accounts

Password for all: `demo1234`

| Email | Role | Lands on |
|---|---|---|
| `user@demo.io` | shopper | `/user-store.html` |
| `provider@demo.io` | provider | `/provider-panel.html` |
| `admin@demo.io` | admin | `/studio/` |

Registering a new account also works (stored in the browser only).
The hub page at `/` has one-click role shortcuts that skip the login form.

## How the mock works

- `frontend/mock-api.js` patches `window.fetch`. Requests whose path starts
  with `/api/` are routed to in-browser handlers; everything else passes
  through untouched.
- State (products, orders, shops, staff, settings) lives in
  `localStorage["md_mock_db_v1"]`, seeded on first visit. Each visitor gets
  their own isolated data.
- Flows that actually work end to end: login/register, browse + filter
  products, cart + discount code `WELCOME10`, checkout preview, order
  creation with stock checks, slip upload -> admin approve/reject -> paid,
  provider restock/product CRUD/order actions, studio CRUD + checkout.
- "Reset demo data" on the hub page reseeds everything.

## Local check

```bash
cd frontend-vue && npm ci && npm run build && cd ..
bash scripts/assemble-static.sh
cd dist && python3 -m http.server 8123
# open http://localhost:8123
```

## Reverting to the real backend

Remove the `<script src="/frontend-assets/mock-api.js"></script>` tag from the
six HTML pages in `frontend/` and from `frontend-vue/index.html`, then serve
the pages behind the FastAPI app as before. The mock never runs for pages that
do not include that tag.
