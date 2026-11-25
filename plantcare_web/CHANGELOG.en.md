# English changelog

User-facing English notes for GitHub releases. The script `scripts/release_notes.py`
uses the section that matches the add-on version; when a version is missing here it
falls back to the Italian entry in [`CHANGELOG.md`](CHANGELOG.md).

# 1.1.3 — adjustable text size

- **Appearance**: **Settings → Appearance → Text size** offers five levels from 90% to 150%, a preview, immediate application and a reset to normal size.
- **Local preference**: the choice is saved only in the device's browser; when storage is blocked it still works for the session. The archive and preferences on other devices are unchanged.
- **Desktop and phone**: the shared scale includes chart text. Photos and icons are not enlarged; printed label sizes stay independent of the reading preference, and phone form controls stay at least 16 px.
- **Responsive layout**: larger text reflows plant actions into several rows, reduces summary columns, allows the weekly calendar to scroll and wraps dialog and product text. Bottom navigation gives longer labels more room without reducing the font.
- **Checks**: 289 backend tests, 60 browser tests, 1,245 aligned i18n keys and frontend build. Visual Chromium checks at 320, 360, 375, 390 and 1280 px; this is not a physical iPhone or Home Assistant rehearsal.
- **Reversibility**: annotated `checkpoint/before-font-scaling` tag on the previous state and dedicated implementation commits. No data migration.

# 1.1.2 — bidirectional learning and grower guardrails

- **Postponements and early watering**: Verdant learning uses honoured postponements across multiple cycles to lengthen intervals and repeated early waterings to shorten them, with 1–4 day steps according to experience. Several postponements within one cycle and duplicate same-day entries do not multiply evidence; conflicting signals do not accelerate learning.
- **Historical due dates**: new waterings preserve the due date before the intervention. Early care in older history without saved deadlines is labelled inferred; editing the date, kind or status invalidates the old comparison.
- **AI and experience**: the fixed ±25% daily-analysis bound becomes ±15% for beginners, ±25% intermediate, ±35% expert and ±50% professional. Prompts and output validation share the same limits; botanical safety minimums always take priority. Profile limits are rechecked before applying proposals.
- **Explicit evidence**: AI context distinguishes completed care, postponements and early watering, includes notes and distinct cycles, and requests reasons for changing or maintaining intervals. Clamped AI values show the requested value, accepted value and limit. Removed a check that rejected valid Italian reasons merely for mentioning current intervals.
- **Safety**: learning respects species watering minimums and realigns feeding to at least two watering cycles. In AI mode, evidence feeds proposals without introducing new automatic application; the plant-card assistant remains separate from daily analysis.
- Checks: 289 backend tests, 25 browser tests, 1,234 aligned i18n keys and frontend build. A health-score test no longer depends on the current date.

# 1.1.1 — safer feeding intervals and clearer errors

- **Combined care**: feeding is preselected when available alongside watering, with an opt-out checkbox.
- **Feeding frequency**: feeding intervals must span at least two watering intervals, including adaptive plans and AI suggestions. Overly frequent manual intervals are corrected on save.
- **AI**: both prompts explicitly state the constraint; response schemas and output normalization enforce it. Previously cached advice is invalidated.
- **Clearer errors**: empty or HTML server responses, expired sessions and connection failures no longer appear as “Check the data and try again”. Validation errors retain their field and reason, including structured details and English UI messages; errors outside forms remain visible.
- Checks: 267 backend tests, 25 browser tests, 1,234 aligned i18n keys and frontend build.

# 1.1.0 — indexed history and a more accessible interface

- **Faster history**: the collection history uses an SQLite index derived from the archive, created on first start, updated in the same transaction as care changes and rebuilt during restore. With 200,000 synthetic events p95 falls from **798 to 26 ms** unfiltered and from **501 to 21 ms** filtered, measured on Home Assistant OS in an isolated VM. The JSON archive, backups and photos are unchanged and the index can be rebuilt.
- **Accessibility**: skip to content, active-view indication, accessible dialog names, focus restoration on close, improved secondary-text contrast and calendar day names.
- **Browser tests**: Playwright and axe in Chromium against a temporary archive, also run in CI after the build. The 15 tests cover keyboard navigation, the plant editor, language persistence, web restore, canceling and completing care, plant cards on desktop, the mobile growth diary and the 320/360/375/390 px layouts.
- **Step 8 closeout**: documented iPhone and Home Assistant checks, the isolated restore and the stress-test limits. NFC testing is out of scope, and the 500,000-event test is not a home-use requirement.
- Checks: 234 backend tests (4 new), 15 browser tests, 1,234 aligned i18n keys, frontend build.

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
