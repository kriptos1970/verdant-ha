# English changelog

User-facing English notes for GitHub releases. The script `scripts/release_notes.py`
uses the section that matches the add-on version; when a version is missing here it
falls back to the Italian entry in [`CHANGELOG.md`](CHANGELOG.md).

# 0.11.28 — the trash is reachable from the phone again

- On phones the **Trash** command lived in the Plants page header, which the mobile layout
  hides: after deleting with a swipe there was no way to open the trash and restore a plant.
  Next to the collection title there is now a round button with the trash icon and the
  accessible label "Trash".
- Desktop is unchanged: the command stays in the collection header, next to the leaf icon.
- Verified at 320 and 375 px without horizontal scrolling, and at 813 px with the mobile
  button hidden; 225 backend tests, 1021 i18n keys, frontend build.
