# Contributing to Verdant HA

Thanks for your interest in the project. Verdant HA is maintained in spare time, so small and focused pull requests are the easiest to review.

## Before you start

- Open an issue for non-trivial changes, so the approach can be discussed first.
- For security problems **do not open a public issue**: follow [SECURITY.md](SECURITY.md).
- Never commit credentials, personal archives or photos from a real collection.

## Development setup

Requirements: Python 3.13, Node.js 22, npm.

```sh
python3 -m venv .venv
.venv/bin/pip install -r plantcare_web/backend/requirements.lock pytest
npm ci --prefix plantcare_web/frontend
npm run build --prefix plantcare_web/frontend
PLANTCARE_DATA=.data .venv/bin/uvicorn plantcare_web.backend.main:app --host 127.0.0.1 --port 8099 --no-proxy-headers
```

Open `http://127.0.0.1:8099/`. For frontend hot reload, run `npm run dev --prefix plantcare_web/frontend` while the backend listens on port 8099.

## Tests

```sh
.venv/bin/python -m pytest plantcare_web/tests -q
npm run build --prefix plantcare_web/frontend
```

CI runs the same checks on every push and pull request. A change is ready when both are green.

## Pull requests

- Keep one topic per pull request and link the related issue.
- Add or update tests when behavior changes.
- Update `plantcare_web/CHANGELOG.md` for user-visible changes and the relevant document in `docs/` when verification details change.
- Do not include `.venv`, `node_modules`, `releases/`, local databases or personal photos.
- UI text is currently in Italian. Localization is planned: keep user-facing strings consistent with the existing wording and avoid duplicating the same message in several places.

## Code style

- Python: follow the existing compact style in `plantcare_web/backend/`; avoid new dependencies unless necessary.
- TypeScript/React: strict TypeScript, components in `plantcare_web/frontend/src/`.
- SQLite schema changes need a migration path and tests; never rewrite a user's archive in place.
- Feeds, providers and AI calls must be mockable in tests; no real credentials or paid calls in the test suite.

## Releases

Releases are created from a tag. The workflow runs the tests, builds the source package and publishes the ZIP with its SHA256. See `.github/workflows/release.yml`.

## Commit messages

Use a short imperative subject, for example:

```
Add English README
Fix grouped fertilizer deadline
```
