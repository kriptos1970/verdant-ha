# Agent notes

This file is loaded in every OpenCode session opened on this repository. Read it before improvising a release or deployment workflow.

## Releases are automatic — never say they cannot be published

Pushing a `v*` tag starts `.github/workflows/release.yml`. That workflow runs the backend tests, builds the frontend, creates `releases/plantcare-web-<version>.zip` and its `.sha256`, and publishes the GitHub Release with `softprops/action-gh-release`.

- `gh` is **not** installed on the maintainer's Mac, and it is **not** needed.
- No local GitHub token is needed: the workflow uses its own `permissions: contents: write`.
- Do **not** run `gh release create` and do **not** ask the user for a token to publish a release.

### Release checklist

1. Bump the version in `plantcare_web/config.yaml`, `plantcare_web/backend/__init__.py`, `plantcare_web/frontend/package.json` and both `version` fields in `plantcare_web/frontend/package-lock.json`.
2. Update `plantcare_web/CHANGELOG.md`, `docs/STATUS.md`, `docs/en/STATUS.md`, `README.md`, `README.it.md` and `ROADMAP.md`.
3. Run the checks (backend tests, i18n, frontend build).
4. Commit, push `main`, create an annotated tag `vX.Y.Z`, push the tag. The tag must match the version in `plantcare_web/config.yaml`; the workflow stops otherwise.
5. Wait for both **CI** and **Release** on the tagged commit to be green. `releases/` is gitignored: the ZIP published on GitHub is built by the workflow, not uploaded from the Mac.
6. Run `python3 scripts/verify_release.py vX.Y.Z`; it retries while the workflow is still running and exits non-zero if the release or its assets are missing.
7. Only after the release is verified, update the add-on.

A 404 from the GitHub API immediately after the push just means the workflow has not published yet, not that publishing is impossible.

## Home Assistant add-on

The add-on is installed from the repository `kriptos1970/verdant-ha` as `309d34f7_plantcare_web`.

- `ha` exists on the Home Assistant host, not on the Mac: `ssh root@homeassistant '...'`.
- Update: `ha store reload`, then `ha apps update 309d34f7_plantcare_web`.
- Verify: `ha apps info 309d34f7_plantcare_web` (version, `state: started`) and the raw JSON for the options.
- Never modify `/data` or the archive directly. Confirm that `photo_directory` and `care_engine_mode` survive the update.
- A restart reloads `/data/options.json`; if an add-on option changed, restart the add-on before judging the web UI value.

## Verification

```sh
node scripts/check_i18n.mjs
.venv/bin/python -m pytest plantcare_web/tests -q
npm run build --prefix plantcare_web/frontend
npm test --prefix plantcare_web/frontend
```

Before the first browser test run, install Chromium with `npm exec --prefix plantcare_web/frontend -- playwright install chromium --only-shell`. The tests start `scripts/preview_ios.py` with a temporary archive on port 8771 and use the built frontend; stop any process already using that port or run the tests later.

For phone layouts, use `scripts/preview_ios.py` with the browser at 320/360/375/390 px; do not claim a visual check without looking at the rendered page.

## Conventions

- The add-on version is `0.11.x`; `plantcare_web/config.yaml` is the source of truth for the tag.
- `plantcare_web/CHANGELOG.md` and `docs/STATUS.md` are in Italian; `docs/en/STATUS.md` and `README.md` are in English.
- Never commit credentials, personal archives, photos, `.venv`, `node_modules` or `releases/`.
