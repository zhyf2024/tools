# AGENTS.md

## Repository layout

This root repo (`D:\code\tools`) vendors three independent projects. There is no root build/test; run commands inside the project you change.

| Path | What it is |
| --- | --- |
| `crawler/FastapiAdmin/` | FastAPI + Vue3 admin platform. **Nested git repo** (own `.git`, upstream `fastapiadmin/FastapiAdmin`, branch `master`). |
| `website-downloader/` | Standalone Python CLI for offline site mirrors. |
| `agency-agents/` | Markdown-only catalog of AI agent prompts. |

- `crawler/FastapiAdmin` is a nested repo, so the root repo sees it as one untracked directory. Commit FastapiAdmin changes from inside `crawler/FastapiAdmin`, not from the root.
- `crawler/doc/` is an untracked snapshot: most files are byte-identical copies of `FastapiAdmin/*.md` or `agency-agents/engineering/*.md` (with renamed files such as `README.backend.md`). Edit the originals, not the copies.
- FastapiAdmin's working tree has intentional uncommitted local work (Joom scraper plugin, `sys_role_menus` seeding, localhost docker/nginx config, `.env` edits). Do not `git checkout .` or `git clean` there.

## FastapiAdmin

Run from `crawler/FastapiAdmin/backend` (Python 3.12, `uv`):

```bash
uv sync --extra sqlite --extra mysql     # CI baseline; add --extra postgres as needed
uv run main.py run --env=dev             # serves on 8001, /docs
uv run pytest                            # tests use sqlite + mocked Redis, no services needed
uv run pytest tests/test_joom_scraper.py -q   # single file
uv run ruff check
```

- Env comes from `backend/env/.env.<ENVIRONMENT>`; copy `.env.example` to `.env.dev` (gitignored, absent on a clean checkout). Set `SECRET_KEY`. Seed accounts: `super` / `admin` / `user`, password `123456`.
- Deeper conventions (KeepAlive caching, code generator, dist deployment) are in `crawler/FastapiAdmin/SKILL.md`; its "three dist copies" section is historical — no `dist/` directories are currently checked in.
- `backend/app/alembic/versions/` intentionally contains only `__init__.py`; this fork does not commit migration history. Startup applies migrations, and in dev auto-generates + applies them when models change. Don't hand-create migrations unless asked; `tests/test_migrations.py` guards drift.
- Seed data in `backend/sql/*.json` is imported only when the table is empty. Editing a seed file does not update an existing DB.
- Modules live in `app/modules/<domain>/<feature>/` (`controller/service/crud/model/schema.py`). Plugins live in `app/plugin/module_*` and are auto-discovered at startup; `module_x` maps to URL prefix `/x`. Import errors or route conflicts abort startup, and discovery runs only at startup, so restart after adding/moving a plugin.
- Local-only plugin: `app/plugin/module_joom_scraper` (routes under `/joom_scraper/joom`). Needs `uv sync --extra scraper` plus `playwright install chromium`; images go to `static/upload/joom_images`. It is covered by `tests/test_joom_scraper.py`.

Frontend (`crawler/FastapiAdmin/frontend/web`, Node >= 20.19, pnpm 9):

```bash
pnpm install
pnpm dev                 # port 5180, proxies /api/v1 -> 127.0.0.1:8001
pnpm build:prod          # generates src/types/{auto-imports,components}.d.ts
pnpm type-check          # run build:prod first on a clean checkout, otherwise vue-tsc fails
pnpm test                # vitest, tests in src/__tests__
pnpm lint                # eslint + prettier + stylelint
```

- `src/types/auto-imports.d.ts` and `components.d.ts` are generated and gitignored; CI builds before type-checking for this reason.
- API/view folders are `src/api/module_*` and `src/views/module_*`. Menu-driven routes require `component_path` to match the view path, and `defineOptions({ name })` must equal the menu `route_name` or KeepAlive breaks.
- Reuse existing CRUD hooks/components (`useTable`, `useCrudDialog`, `FaTable`) and `v-hasPerm`; backend permission strings are `module:resource:action`.
- Other frontends: `frontend/app` is uni-app (`pnpm dev:mp-weixin`, `pnpm type-check`); `frontend/docs` is VitePress (`pnpm dev`, `pnpm build`).

Docker/deploy:

- `docker/docker-compose.yaml` is locally modified for dev (`ENVIRONMENT: "dev"`, named volumes, `localhost` nginx certs). Don't assume it matches upstream docs or production defaults.
- `./deploy.sh` only builds/starts backend images; it does not build the frontend (the `--build-frontend` flag documented in `docker/README.md` no longer exists). Use `deploy-artifacts.sh` or build manually.
- `deploy-artifacts.sh` deploys to a hardcoded remote host over SSH. Do not run it unless explicitly asked.

## website-downloader

Run from `website-downloader/` (Python 3.10+):

```bash
pip install -e ".[dev]"
pytest                       # uses a local HTTP fixture server; no network needed
pytest tests/test_crawler.py::test_name -q
ruff check . && black . --check && isort . --check-only
```

- Entrypoints: `website-downloader` console script, `python -m website_downloader`, or `website-downloader.py`.
- Style: black/isort/ruff line length 100; `.flake8` allows 200. `web_scraper.log` and `*.egg-info/` are ignored local artifacts.

## agency-agents

- Content-only project: agents are Markdown files in division directories; there is no Python/JS build.
- `divisions.json` and `tools.json` are the sources of truth for divisions and supported tools. Generated integration outputs are gitignored; only `integrations/*/README.md` and `scripts/` are committed.
- Validation scripts require Bash (Git Bash/WSL on Windows). For agent edits run `./scripts/lint-agents.sh <file>`, `./scripts/check-divisions.sh`, and `./scripts/test-convert-outputs.sh` as applicable.
