# English changelog

User-facing English notes for GitHub releases. The script `scripts/release_notes.py`
uses the section that matches the add-on version; when a version is missing here it
falls back to the Italian entry in [`CHANGELOG.md`](CHANGELOG.md).

# 1.0.0 — first stable release

- **Home Assistant store**: icon and logo taken from the native app artwork, an add-on
  introduction page, and translated option names and descriptions in English and Italian. The
  add-on page no longer shows raw keys.
- **Panel for everyone**: `panel_admin: false`, so the sidebar panel is visible to non-admin
  users of the household; `stage: stable` is set explicitly.
- **README and screenshots**: the repository page is rebuilt around a one-click install badge,
  real English screenshots at 390×844 and 1440×900, an FAQ, privacy and status; the Italian
  version mirrors it.
- **Bilingual release notes**: English first, Italian below, with the repository install as the
  first step and the correct add-on name.
- **Language fixes**: the "cares" plural in the day summary, the desktop detail captions
  ("YOUR PLANT") and the plan name in the English UI.
- **Prebuilt images**: a workflow that publishes the aarch64 and amd64 images to GHCR tagged
  with the add-on version.
- 225 backend tests, 1024 i18n keys, frontend build.

# 0.11.28 — the trash is reachable from the phone again

- On phones the **Trash** command lived in the Plants page header, which the mobile layout
  hides: after deleting with a swipe there was no way to open the trash and restore a plant.
  Next to the collection title there is now a round button with the trash icon and the
  accessible label "Trash".
- Desktop is unchanged: the command stays in the collection header, next to the leaf icon.
- Verified at 320 and 375 px without horizontal scrolling, and at 813 px with the mobile
  button hidden; 225 backend tests, 1021 i18n keys, frontend build.
