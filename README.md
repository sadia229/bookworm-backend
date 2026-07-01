# Book-Worm API (FastAPI + Supabase)

REST backend for the **Book-Worm** reading-tracker app. Implements the full
contract in the Flutter project's `api-doc.md`: auth, profiles, books, reading
progress, reviews, the "World Comes to Life" forest, bookmarks, leaderboard,
stats/dashboard, and Firebase push notifications with a Supabase-backed history.

- **Framework:** FastAPI (Python 3.12)
- **Database + storage:** Supabase (Postgres via PostgREST, Storage buckets)
- **Auth:** the API issues its own JWT access/refresh tokens (rotation + reuse
  detection). Independent of Supabase Auth.
- **Push:** Firebase Cloud Messaging; device tokens and notification history
  are stored in Supabase.
- **Hosting:** Vercel (Python serverless).
- **CI/CD:** GitHub Actions (lint + test, then deploy to Vercel).

## Layout

```
app/
  config.py            settings (env-driven)
  main.py              FastAPI app, routing, error handlers
  deps.py              auth dependency (Bearer JWT)
  core/                security (JWT/bcrypt), envelope, exceptions, rate limit
  db/                  supabase client, repository interfaces + two impls
                       (supabase_repository, memory_repository), DI container
  models/              Pydantic request models per domain
  routers/             one router per api-doc.md section
  services/            business logic (auth, books, progress, world, push, ...)
supabase/schema.sql    tables, RLS, views, and the atomic RPC functions
api/index.py           Vercel entrypoint
tests/                 pytest suite running the app against in-memory repos
```

The data layer is behind repository interfaces (`app/db/repository.py`). The
production implementation talks to Supabase; the test implementation is a set of
in-memory fakes that enforce the same business rules, so the whole suite runs in
CI with **no live database**.

## Setup

1. **Create the database schema.** In the Supabase dashboard → SQL Editor, run
   [`supabase/schema.sql`](supabase/schema.sql). This creates all tables, RLS,
   the leaderboard views, and the `fn_finish_book` / `fn_log_progress` RPCs used
   for atomic progression.

2. **Environment.** Copy `.env.example` to `.env` and fill in values:
   ```bash
   cp .env.example .env
   # generate a strong secret:
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```
   - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` — from
     Supabase → Project Settings → API. The backend uses the **service role**
     key server-side (it bypasses RLS; never expose it to a client).
   - `JWT_SECRET_KEY` — signs this API's tokens.
   - `FIREBASE_CREDENTIALS_JSON` — the Firebase service-account JSON as a single
     line. Optional: if unset, push sends are skipped with a warning and the
     token/history endpoints still work.

3. **Install & run locally.**
   ```bash
   python3.12 -m venv .venv && source .venv/bin/activate
   pip install -r requirements-dev.txt
   uvicorn app.main:app --reload
   ```
   Interactive docs: http://localhost:8000/docs

## Tests & lint

```bash
pytest -q          # runs against in-memory repositories, no DB needed
ruff check .
```

## Push-notification integration

`app/services/notification_service.notify_and_push()` is the single path that
(1) writes a row into the Supabase `notifications` table and (2) attempts an FCM
push to the user's registered device tokens. It's wired into book-finish so that
crossing a world-stage threshold notifies the reader ("Your forest grew!").
Because history is always persisted first, `GET /api/v1/notifications` remains a
reliable source of truth even if FCM delivery fails or Firebase isn't
configured.

Endpoints (all under `/api/v1`):
- `POST /notifications/token` · `DELETE /notifications/token` — register/remove FCM tokens
- `GET /notifications` — stored history (newest first, `unread_count`)
- `PATCH /notifications/{id}/read` · `POST /notifications/read-all`
- `DELETE /notifications/{id}` — dismiss

## Deploying to Vercel

The repo is Vercel-ready ([`vercel.json`](vercel.json), [`api/index.py`](api/index.py)).

1. Import the repo in Vercel (or `vercel` CLI).
2. Add every variable from `.env` to Vercel → Project → Settings → Environment
   Variables (Production).
3. Deploy. All routes are served by the single `api/index.py` function; the app
   is reachable at `https://<project>.vercel.app/api/v1/...`.

### CI/CD

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs ruff + pytest on
every push/PR. On push to `main`, if the `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and
`VERCEL_PROJECT_ID` repository secrets are set, it builds and deploys to Vercel
production; otherwise the deploy step is skipped and the pipeline stays green.

## Notes

- **Response envelope.** Every endpoint returns `{ success, message, data }`;
  lists wrap `{ items, page, size, total, total_pages }` under `data` — matching
  `api-doc.md`.
- **Rate limiting** on auth endpoints is in-process (resets on cold start);
  swap for a shared store if you run many concurrent serverless instances.
- **World-stage thresholds** (`0/5/15/30/50/100 → 0..5`) live in exactly two
  places kept in sync: `supabase/schema.sql` (`fn_world_stage`) and
  `app/services/world_service.py` / `app/db/memory_repository.py`.
