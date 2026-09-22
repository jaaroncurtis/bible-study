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

**A study is written for one person working alone.** Read, think, sit with it,
journal. The reflection questions are where the study actually happens. Groups may
meet afterwards to compare notes, but the lesson never assumes a room: no "say this
out loud", no "let the group notice", no second-person-plural. Anything that only
makes sense with other people present belongs in teacher notes.

There is deliberately **no coupling between them**. A study does not reference or
transclude a note; study prose is written by hand. Do not add a note-id
reference system without a reason that has actually come up.

**Every study stands alone.** Notes are where doctrine is worked out; a study is
where it is *presented*, at whatever depth that study needs. So a study never
mentions the notes at all - no "the context note says", no "as the saving-faith
note argues", no pointer into `notes/`. If a study needs an idea from a note, it
states the idea in full, in its own words, as though the note did not exist. This
applies to lessons, overviews and teacher notes alike, in every study.

**"The study" means exactly the files `study.json` references** - the study
overview, section overviews, lessons and teacher notes. Anything else in a study
folder is meta-study: design aids such as `outline.md` that direct how the study is
built. Meta-study files are working documents and are exempt from the study rules;
they may cite notes freely. The test suite applies the rules to the referenced files
only.

**Instructions stay, addressed to the reader.** "Read these slowly", "write the
question down and come back to it", "stop here before going on" are all good.
What goes is the room: an instruction that only makes sense with other people
present moves to teacher notes.

**Position on national Israel (author's stance, not study text).** A "leaky
Reformed" view: the church inherits most of the promises, but God still has a plan
for national Israel. Romans 11:26 is read as a future turning of ethnic Israel as a
people, after the fullness of the Gentiles. 11:28-29 is said of the nation, and it
stands as an *example* of perseverance, never its proof-text (8:29-30 teaches it).
Write studies consistent with this; do not name or label the view inside a study.

A study is an ordered list of sections. A "section" is whatever that study needs -
a chapter of the Westminster Confession, a passage of Romans, a topic. There is
no fixed schema, on purpose.

## Where things are

| Path | What |
|---|---|
| `notes/context/research/` | Investigations: evidence weighed, scholars cited |
| `notes/context/doctrine/` | Settled positions, organised for use |
| `studies/<name>/` | One study: `study.json`, `overview.md`, `sections/`, `assets/` |
| `studies/<name>/sections/NN-<key>/` | One section: its own `overview.md` plus `NN-<key>.md` lessons |
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

## How a study is laid out

`study.json` holds the ordering and the identity of everything. The markdown holds
the prose. The long-term direction is that the JSON becomes the source and the
markdown becomes generated output, so **the markdown must stay deterministically
parseable** - `tools/study/lesson.py` enforces the grammar and every lesson in the
repo is checked against it by the test suite.

A lesson file, exactly:

```markdown
# <Title>

**<Reference>**

## Aim

<prose>

## Content

### <optional subheading>

- bullets, or prose, or both

## Cross-references          (optional section)

- **<Reference>** - <what it is there to do>
- **<Ref A>** and **<Ref B>** - one note may cover several references

## Reflection

- questions
```

`## Aim`, `## Content` and `## Reflection` are required and must appear in that
order; `## Cross-references` is optional and sits before Reflection. No other `##`
headings. `###` opens a group inside a section. Nothing sits outside a section.

**Teacher notes never go in a lesson file.** The study is published for
self-directed use, so anything meant only for whoever is preparing - objections to
expect, debates to sidestep, background that should not be taught as the lesson -
lives in a sibling `NN-<key>.teacher.md`, recorded as the lesson's `teacher` field
in `study.json`. That file uses a title, a reference, then `###` groups. Keeping
them in separate files makes the segregation structural: the learner build never
opens a teacher file, so no rendering mistake can leak one. `parse_lesson` rejects
a lesson that tries to carry a `## Teacher notes` section, and the suite checks
every lesson in the repo.

**Identity is the surrogate `id` in `study.json`, and it never changes.** Order
lives in the JSON; sequence lives in the names on disk - `NN-<key>/` for sections,
`NN-<key>.md` for lessons - mirrored by the `dir` and `file` fields. Renumbering
therefore touches only those names and their `dir`/`file` values; no
cross-reference moves, because references are by `id`. Ids are never reused;
`nextId` is the counter.

Lesson-to-lesson links are written in prose as `[Some Title](lesson:23)`. The
title is display only; the id carries the reference.

## Rules that are easy to get wrong

- **Specs and plans are markdown files in this repo**, under `docs/specs/`. Do not
  publish them as hosted artifacts. This overrides the global preference for
  artifacts.
- **Never commit scripture in bulk.** The cache is gitignored because most
  translations are copyrighted. Test fixtures stay minimal for the same reason -
  the ESV fixture is a three-verse excerpt, not a chapter. Short phrases quoted
  inside study prose are ordinary citation and are the author's call; whole
  verses, passages or systematic verse text are not.
- **The published site embeds no scripture.** The renderer never pulls verse text
  into rendered output; references link out to BibleGateway instead. Crossway
  requires written permission for commentary and biblical reference works even
  under its 500-verse limit, and a study with exposition is plausibly commentary.
  See `docs/specs/2026-09-21-notes-and-studies-design.md` before proposing
  systematic embedded verse text. This governs *generated* text - it does not stop
  the author quoting a phrase in their own prose.
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
