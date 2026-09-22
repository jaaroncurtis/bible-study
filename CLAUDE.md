# bible-studies

Bible studies, the notes they draw on, and the tooling that feeds both.

## Notes and studies are different things

- **`notes/`** is a thinking library: plain markdown on theology, read by a human
  and drawn on when designing a study. Nothing reads it mechanically. It is split
  by what kind of document each note is:
  - `notes/context/research/` - investigations. Survey evidence, weigh scholars,
    show their reasoning, carry citations.
  - `notes/context/doctrine/` - settled positions. Assert and organise a
    conclusion for later use rather than investigating it.
- **`studies/<study-name>/`** is one study, rendered to a PDF and to an
  interactive page on GitHub Pages.

There is deliberately **no coupling between them**. A study does not reference or
transclude a note; study prose is written by hand. Do not add a note-id
reference system without a reason that has actually come up.

A study is an ordered list of sections. A "section" is whatever that study needs -
a chapter of the Westminster Confession, a passage of Romans, a topic. There is
no fixed schema, on purpose.

## Where things are

| Path | What |
|---|---|
| `notes/context/research/` | Investigations: evidence weighed, scholars cited |
| `notes/context/doctrine/` | Settled positions, organised for use |
| `studies/<name>/` | One study: `study.toml`, `sections/*.md`, `assets/` |
| `site/` | Authored templates, CSS and JS shared by every study |
| `docs/` | **Build output.** GitHub Pages serves it. Never hand-edit |
| `docs/specs/` | Design specs |
| `tools/bg/` | BibleGateway fetch/parse/cache CLI |
| `tools/study/` | The study renderer. Not built yet |
| `cache/` | `bible/<VERSION>/<Book>/<NNN>.json`, plus `catalog/` and `search/`. **Gitignored** |
| `tests/` | Offline tests plus one live check behind `-m live` |
| `.claude/skills/` | Repo-local skills |

## Working here

Use the repo virtualenv for everything:

```bash
.venv/Scripts/python -m pytest          # offline, fast
.venv/Scripts/python -m pytest -m live  # one real request; run after parser changes
.venv/Scripts/python -m bg fetch "Romans 8:28-30"
```

Setup from a fresh clone: `python -m venv .venv` then
`.venv/Scripts/python -m pip install -r requirements.txt -e .`

## Rules that are easy to get wrong

- **Specs and plans are markdown files in this repo**, under `docs/specs/`. Do not
  publish them as hosted artifacts. This overrides the global preference for
  artifacts.
- **Never commit scripture text.** The cache is gitignored because most
  translations are copyrighted. Test fixtures stay minimal for the same reason -
  the ESV fixture is a three-verse excerpt, not a chapter.
- **The published site embeds no scripture.** References link out to BibleGateway
  instead. Crossway requires written permission for commentary and biblical
  reference works even under its 500-verse limit, and a study with exposition is
  plausibly commentary. See `docs/specs/2026-09-21-notes-and-studies-design.md`
  before proposing embedded verse text.
- **Never license this repo under Creative Commons.** Crossway's terms prohibit
  quoting ESV text in any CC-licensed publication.
- **Scraping is paced.** BibleGateway asks for a 15 second crawl delay and the
  fetcher enforces it across processes. Cache hits are free; every uncached
  chapter costs ~15s. Say so before a multi-chapter pull.
- **Read cached JSON directly** when studying. Do not shell out to `bg` for a
  chapter already on disk.
- **Journals are never committed.** This repository is public. Journals live in
  the browser (IndexedDB), and later in Firestore.
- **Source files stay ASCII.** Windows tooling here has mangled UTF-8 source
  before; put non-ASCII in data, not in code.
- **Note filenames are kebab-case and name the argument, not the title.** A note's
  own heading is often vague ("a comprehensive framework") or names only one
  subsection. Name the file so someone browsing the folder knows what it claims
  without opening it.

For how to drive the BibleGateway CLI, see the `bible-gateway` skill.
Current design: `docs/specs/2026-09-21-notes-and-studies-design.md`.
