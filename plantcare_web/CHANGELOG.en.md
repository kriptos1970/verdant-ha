# English changelog

User-facing English notes for GitHub releases. The script `scripts/release_notes.py`
uses the section that matches the add-on version; when a version is missing here it
falls back to the Italian entry in [`CHANGELOG.md`](CHANGELOG.md).

# 1.0.3 — restoring backups over the current archive

- **In-place restore**: a web backup (ZIP or JSON) can now be restored over the current archive
  without emptying it first. The preview shows both the backup contents and the data that would be
  replaced, and the restore asks for a second confirmation.
- **Safety**: replacement runs in a single transaction: if a check or a write fails, the previous
  archive stays intact. The starting database is copied to `restore-snapshot.sqlite` and overwritten
  by the next restore; photos are never deleted, unlinked files stay in the folder and can be
  removed with **Photo cleanup**. Native backups still require an empty archive.
- **Interface**: the **Archive and backup** panel is translated into Italian and English, plurals
  included, and shows the current archive counts before a restore.
- **Documentation**: backup scheduling now names a partial add-on backup together with the `/share`
  folder, and the guide explains preview, confirmation and the safety copy.
- Checks: 230 backend tests, 1,231 aligned i18n keys, frontend build; full browser flow at
  320/360/375/390 and 1440 px, with a plant added after the backup removed by the restore.

# 1.0.2 — full-size diary photos and lighter rendering

- **Growth diary photos**: on the plant page thumbnails open a modal with the original instead of
  a new tab that stayed blank on phones; a message appears when the original fails to load. The
  control is a real button with an accessible label, and the thumbnail is decorative for screen
  readers.
- **Rendering**: `Intl` formatters are cached per language and option shape. Every calendar cell,
  chart point and one of the twelve guide months used to build its own `Intl.DateTimeFormat`:
  about 0.95 ms per calendar render, now 0.01 ms (development Mac, 35 cells).
- **Checks**: `check_i18n.mjs` also verifies the plural keys built at runtime
  (`plural("x")` → `x.one`/`x.other`), which TypeScript cannot see through the category cast.
  24 plural bases checked.
- Checks: 225 backend tests, 1,195 aligned i18n keys, frontend build.

# 1.0.1 — a more responsive phone and a complete English UI

- **Touch feedback**: tap highlight, `touch-action: manipulation` and a pressed state on buttons,
  tabs and cards.
- **Products**: the second "Category" select under the list is gone; the desktop filter was not
  hidden because `.collection-toolbar>select` did not match a select nested in a label.
- **Plant detail**: the two round buttons are 44 px instead of 40, the "At a glance" grid is no
  longer a clickable div, and opening an editor on a phone no longer raises the keyboard.
- **Scrolling**: modals and the product overlay contain their scroll
  (`overscroll-behavior: contain`), so the page behind stays put.
- **English UI**: health album, QR/NFC labels, botanical library, Pl@ntNet identification, species
  library, AI assistant and model catalog now use the message catalog (85 new keys, 1,193 total).
  Dates, numbers and doses follow the active language; the helper that returned the Italian
  "Tra 2 giorni" is gone.
- **Looks**: `color-scheme: light` aligns native selects and scrollbars; search placeholders end
  with an ellipsis.
- Checks: 225 backend tests, 1,193 aligned i18n keys, frontend build, dose parity against the
  Swift function on 40 cases, visual checks at 320/360/375/390 px in Italian and English.

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
