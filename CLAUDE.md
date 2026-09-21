# bible-studies

Polished Bible study notes, and the tooling that feeds them.

## The pipeline

Notes are built in three passes. Only pass 1 exists today.

1. **Pull and cache** - scripture comes out of BibleGateway as structured JSON,
   one file per chapter. This is `tools/bg`, driven by the `bible-gateway` skill.
2. **Consolidate** - study content is assembled into a single JSON document that
   references cached verses. Not built yet.
3. **Render** - the notes document is produced from that JSON. Not built yet.

Keep the passes separate. Pass 1 returns data, never prose: anything that
decides how a note *reads* belongs in pass 3.

## Layout

| Path | What |
|---|---|
| `notes/` | The study notes themselves |
| `tools/bg/` | BibleGateway fetch/parse/cache CLI |
| `cache/` | Chapter JSON, `cache/<VERSION>/<Book>/<NNN>.json`. **Gitignored** |
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

- **Never commit scripture text.** The cache is gitignored because most
  translations are copyrighted. Test fixtures stay minimal for the same reason -
  the ESV fixture is a three-verse excerpt, not a chapter.
- **Scraping is paced.** BibleGateway asks for a 15 second crawl delay and the
  fetcher enforces it across processes. Cache hits are free; every uncached
  chapter costs ~15s. Say so before a multi-chapter pull.
- **Read cached JSON directly** when building notes. Do not shell out to `bg`
  for a chapter already on disk.
- **Source files stay ASCII.** Windows tooling here has mangled UTF-8 source
  before; put non-ASCII in data, not in code.

For how to actually drive the CLI, see the `bible-gateway` skill.
