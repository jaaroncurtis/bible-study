# Notes and Studies: Repo Design

**Date:** 2026-09-21
**Status:** Approved in design; not yet implemented.

Studies render from one markdown source to both a PDF and an interactive site.
Scripture appears only as links out to BibleGateway, never as embedded text.
Journal entries write to the browser first and sync to Firebase when signed in.

---

## 1. Decisions

| Decision | Choice | What it rules out |
|---|---|---|
| Notes vs studies | Separate trees. `notes/` is a human-read thinking library; `studies/<name>/` holds one study | No transclusion machinery, no note-id references, no drift checking |
| Study structure | An ordered list of sections. A "section" is whatever that study needs — a WCF chapter, a passage of Romans, a topic | No fixed lesson/session schema, no participant/leader split |
| Scripture in the rendered site | Reference text is linkified to BibleGateway. Hover shows the canonical reference; click opens BibleGateway | No embedded verse text anywhere in published output |
| ESV source | Keep the existing scraper for private study | No `api.esv.org` integration (it becomes unnecessary once nothing is published) |
| PDF + HTML | One render, two stylesheets. WeasyPrint turns the same HTML into PDF | No second pipeline, no LaTeX, no Quarto/Pandoc dependency |
| Journaling | IndexedDB is the write path; Firebase Auth + Firestore sync when signed in | No Google Drive storage, no refresh token in the browser |
| Hosting | Static site on GitHub Pages, built into `docs/` and committed on `main` | No CI build step, no Firebase Hosting |

### Why these are not obvious

**Notes stay uncoupled.** Referencing a note from a study and rendering it inline
would mean editing a note silently rewrites a study already taught. The pinned-excerpt
variant solves that but adds machinery for a problem we have not had yet. Notes are
read by a human, and study prose is written by hand.

**Section structure is deliberately undefined.** Studies will be outlined by topic,
by passage, or by both. Any schema imposed now would be wrong for the second study.

---

## 2. Repository shape

```
notes/                      thinking library, plain markdown, zero coupling to studies
  context/                  existing; theological framework documents

studies/<study-name>/
  study.toml                title, default translation, ordered section list
  sections/*.md             one file per section; "section" means whatever this study needs
  assets/                   study-specific images

site/
  templates/                Jinja templates shared by every study
  static/
    screen.css              interactive site
    print.css               PDF
    journal.js              IndexedDB write path + Firebase sync
    refs.js                 reference link behaviour

docs/                       BUILD OUTPUT. GitHub Pages serves this. Committed on main.

tools/bg/                   existing: BibleGateway fetch/parse/cache
tools/study/                new: the renderer
```

`site/` is authored; `docs/` is generated. Never hand-edit `docs/`.

One origin (`https://jaaroncurtis.github.io/bible-study/`) serves every study, so
shared assets are shared for free and browser storage is naturally scoped across
all studies.

---

## 3. Scripture references, and the ESV terms

### What the renderer does

A reference in study prose — `Rom. 10:14`, `Jas. 2:19`, `Matt. 7:21-23` — is
detected, canonicalised, and turned into a link to BibleGateway.

- **Detection and canonicalisation reuse `bg.refs`.** The 66-book alias table already
  resolves every abbreviation style in the existing notes. No second parser.
- **Hover** shows the canonical reference (`Romans 10:14 (ESV)`). A reference is a
  citation, not copyrightable expression.
- **Click** opens BibleGateway, which presents the verse in its surrounding context —
  better for study than a popover fragment.
- **The renderer does not read the verse cache.** Its only dependency on pass 1 is the
  alias table and the reference grammar.

### Why nothing is embedded

Embedding ESV text in a public site is republication. The terms below were researched
from Crossway directly and are recorded here so the constraint cannot erode quietly —
if anyone later proposes embedding verse text, this section is the reason not to.

### ESV terms, as published by Crossway

Sourced from <https://www.crossway.org/permissions/> and <https://api.esv.org/>,
retrieved 2026-09-21.

| Limit | Value |
|---|---|
| Verses quotable without written permission | **500** |
| Share of any single Bible book | **under 50%**, measured in bytes |
| Share of the total text of the work quoting it | **under 25%** |
| A complete book of the Bible | **Never**, regardless of other limits |
| Publication under a Creative Commons licence | **Prohibited outright** |

Two clauses matter more than the numbers:

1. **Commentary and biblical reference works require written permission even within
   the standard limits.** A Bible study with exposition is plausibly a commentary.
   Staying under 500 verses would not by itself settle the question. This is the
   decisive reason the published site embeds no scripture.
2. **The ESV text may not be quoted in any publication made available to the public
   under a Creative Commons licence.** Do not apply a CC licence to this repository.
   A permissive code licence on `tools/` is unaffected.

Required notice, verbatim, wherever ESV text is quoted:

> Scripture quotations are from the ESV® Bible (The Holy Bible, English Standard
> Version®), © 2001 by Crossway, a publishing ministry of Good News Publishers.
> ESV Text Edition: 2025. The ESV text may not be quoted in any publication made
> available to the public by a Creative Commons license. The ESV may not be
> translated in whole or in part into any other language. Used by permission.
> All rights reserved.

### The official API, and why we are not using it

`api.esv.org` is free for non-commercial use, requires an API key, and requires
affirming Crossway's statement of faith. Its terms cap local caching at **500 verses**
and display at 500 verses or half a book per page, and require attribution linking to
esv.org on every page using the text.

It is the licensed route for *publishing* ESV text. Since the site publishes none, it
buys nothing. Recorded here because it is the correct answer if that decision reverses.

### What still needs judgement

The study's own prose may quote scripture directly — "as Paul writes, '…'". That is
ordinary citation and is the author's call. No mechanical check is proposed, because
with zero systematic embedding there is no limit for a checker to enforce. If prose
quotation ever becomes heavy, revisit this section first.

---

## 4. The renderer

`tools/study/`, Python, consistent with the rest of the repo.

```
study.toml + sections/*.md
        |
        v
  markdown -> HTML          markdown-it-py
        |
        v
  reference linkifier       reuses bg.refs alias table + grammar
        |
        v
  Jinja templates           site/templates/
        |
        +---------------------------+
        |                           |
        v                           v
  docs/<study>/index.html     WeasyPrint -> docs/<study>/<study>.pdf
  (screen.css: hover,         (print.css: references become
   BibleGateway links,         footnotes with their URL;
   journaling)                 journaling UI suppressed)
```

One render, two stylesheets. The PDF is the same HTML under print CSS, so the two
outputs cannot drift apart.

**Why WeasyPrint:** pip-installable, no LaTeX toolchain, and it consumes the HTML and
CSS we already have to write. Quarto and Pandoc both solve this, but each adds a
non-Python toolchain for an output we can already produce.

**Testing:** the linkifier is pure text-to-text and gets unit tests against the existing
note as a fixture — it is dense with real-world abbreviation styles. Template rendering
gets a golden-file test per study. PDF generation gets a smoke test that the file is
produced and is non-trivial in size; the PDF's appearance is not asserted.

---

## 5. Journaling

Some study questions need careful thought, so the journal has to be a comfortable
place to write. That drives the design more than durability does.

### Why not Google Drive

Google does not issue refresh tokens to browser clients — they require a client secret,
which a static site cannot hold. From Google's own documentation of the browser token
model:

> "In the token based authorization model, there is no need to store per-user refresh
> tokens on your backend server." … "By design, access tokens have a short lifetime." …
> "If the access token expires prior to the end of the user's session, obtain a new
> token by calling `requestAccessToken()` from a user-driven event such as a button
> press."

Renewal requires a *user gesture*, not silent background refresh. A Drive-backed journal
on a static host would interrupt continuous autosave with a re-authorisation click
roughly hourly. That is the worst possible place for that friction.

### What Firebase does and does not solve

Firebase is **identity plus a per-user store**. It does not grant durable Drive access.

| Firebase gives | Firebase does not give |
|---|---|
| A stable `uid` | A durable Google API token |
| Its own ID + refresh token, auto-refreshed by the SDK, so the app session persists | Any Google OAuth refresh token — Firebase discards it |
| Firestore, scoped per user by security rules | Access to Drive, Gmail, Calendar or any other Google API beyond the sign-in moment |

Signing in with `GoogleAuthProvider` and extra scopes does return a Google access token
as `credential.accessToken`, usable against Drive. But Firebase keeps no Google refresh
token, so that token expires in about an hour and the only way to mint another is
`reauthenticateWithPopup` — the same user gesture as raw OAuth.

So Firebase's durable session covers **its own backend only**. Choosing Firebase is
choosing Firestore as the store; it is not a route to Drive.

### Drive remains available later, in one specific form

The blocker was never Drive itself — it was *continuous* autosave needing hourly
re-authorisation. Because the journal is local-first, autosave never touches the
network, so Drive would only need a token at the moment the reader presses a
"Back up to Drive" button. A button press **is** the gesture Google requires.

If a portable, user-owned copy becomes wanted, add that button with `drive.file` scope
(which limits the app to files it created). It is additive and does not disturb
anything below.

### The design

1. **IndexedDB is the write path.** Every keystroke is saved locally. No login required,
   works offline, instant.
2. **Firebase Auth + Firestore sync when signed in.** One Firebase project across all
   studies; one origin means one grant covers every study page.
3. **Firestore security rules scope each journal to `request.auth.uid`.** Journal entries
   are personal spiritual reflection — they are private by rule, not by convention.
4. **Journals are never committed to the repository.**

Sign-in is an enhancement, never a gate. If you never sign in, journaling still works —
it is simply confined to that browser.

**Hosting and backend are independent.** The site stays on GitHub Pages; Firebase is
used only as a JS-SDK backend. There is no reason to move hosting.

### Sources

- Google browser token model, on refresh tokens and gesture-bound renewal:
  <https://developers.google.com/identity/oauth2/web/guides/use-token-model>
- Firebase Google sign-in, on the returned `credential.accessToken`:
  <https://firebase.google.com/docs/auth/web/google-signin>
- Firebase discarding the Google OAuth refresh token (open feature request):
  <https://github.com/firebase/firebase-js-sdk/issues/2532>

---

## 6. Deployment and build order

The renderer writes to `docs/`, which is committed on `main` and served by GitHub Pages.
No CI. Build output in git history is the accepted cost of a build that anyone can run
and inspect without a toolchain in CI.

Suggested order, each step independently useful:

1. `study.toml` schema and section loading — smallest thing that proves the shape.
2. The reference linkifier, tested against `notes/context/…saving_faith…md`.
3. Jinja templates and `screen.css`; a study renders to a readable page with working
   BibleGateway links.
4. `print.css` and WeasyPrint; the same study renders to PDF.
5. Journaling against IndexedDB only.
6. Firebase Auth + Firestore sync.
7. Publish `docs/` and enable Pages.

Steps 1–4 deliver a usable study. Steps 5–6 are separable and should wait until a real
study exists to write in.

---

## 7. Open questions

- **Is the GitHub repository public?** Pages on a private repository requires GitHub Pro.
  Nothing in this design depends on the answer, but it gates step 7.
- **What does `study.toml` actually contain?** Deferred deliberately. It will be written
  against the first real study rather than guessed at now.
- **Does the PDF need its own cover and table of contents?** Unknown until a study is
  long enough to need one.
- **Cross-reference chains.** Click-through to BibleGateway covers the immediate need.
  Whether following a reference's own cross-references is useful is unknown until the
  first study is in use.
