---
name: bible-gateway
description: Use when pulling scripture from BibleGateway for these study notes - looking up a passage, caching a chapter, checking what is already cached, or diagnosing a failed lookup. Covers the `python -m bg` CLI, the chapter-JSON cache, citation and copyright rules, and what to do when BibleGateway changes its markup.
---

# Pulling scripture from BibleGateway

BibleGateway has no public API, so this repo scrapes `/passage/`. The `bg` CLI
is the only thing that should talk to the site: it paces requests, caches every
chapter it pulls, and returns structured JSON.

## Running it

Always use the repo's virtualenv:

```bash
.venv/Scripts/python -m bg fetch "Romans 8:28-30"
```

| Command | Does |
|---|---|
| `bg fetch "<reference>"` | Verses of a reference, as JSON |
| `bg chapter <book> <n>` | One whole chapter document |
| `bg cache-status` | How many chapters are cached, and in which translations |

Flags: `--version ESV` (default ESV), `--refresh` (refetch even if cached).

References are forgiving: `Rom 8`, `rom 8:28-30`, `1cor 13`, `I Corinthians 13`,
`Ps 23`, `Romans 8:28-9:2` all work.

## What comes back

`fetch` returns `{reference, book, version, verses[], headings[], copyright[]}`.
Each verse carries `chapter`, `num`, `text`, `footnotes[]` and `crossrefs[]`.

Cross-references have both forms. Use `refs` when you need something
resolvable, never `display`:

```json
{ "marker": "BB",
  "refs": ["Romans 9:24", "1 Corinthians 7:15", "1 Corinthians 7:17"],
  "display": "ch. 9:24; 1 Cor. 1:9; 7:15, 17" }
```

`display` abbreviates against running context, so its later parts ("7:17")
cannot be resolved on their own. It is for showing, not for following.

## The cache is the point

Chapters land in `cache/<VERSION>/<Book>/<NNN>.json`, gitignored. A chapter is
fetched at most once, because BibleGateway returns the whole chapter however
narrow the reference. So:

- A second lookup inside a cached chapter is instant and silent.
- **Reading a cached chapter file directly is fine and preferred** when building
  note content - that is what the JSON is for. Do not shell out to `bg` to
  re-read something already on disk.
- `--refresh` only when you suspect the cached copy is wrong.

## Pacing - plan around it

BibleGateway's robots.txt asks for a 15 second crawl delay, and the fetcher
enforces it across processes. Cache hits are free; **each uncached chapter costs
~15s**.

Before a multi-chapter pull, say so up front: "Romans 8-12 is 5 uncached
chapters, about 75 seconds." Never fire off a book-sized pull without flagging
the wait first.

## Copyright

Most translations (ESV, NIV, NASB, MSG) are copyrighted; the KJV and ASV are
public domain.

- The cache is gitignored on purpose. Do not commit scripture text into the repo,
  and do not paste whole chapters of a copyrighted translation into files that
  will be committed.
- Every cached chapter carries its `copyright` string. Notes that quote a
  translation must carry its attribution.
- Quote what the study needs. Do not bulk-pull whole books.

## When a lookup fails

| Symptom | Meaning |
|---|---|
| `Unknown book 'X'. Did you mean ...?` | Alias missing - add it to `tools/bg/books.py` |
| `... is not a reference` | Reference didn't match the grammar; check the shape |
| `Romans 8 has verses 1-39, not 99-99` | Reference runs past the chapter |
| `page contains no passage content` / `no verses` | Bad version code, or BibleGateway changed its markup |

That last one is the one that matters. The parser reads verse addresses from
`span.text` classes (`Rom-8-1`) and note bodies from `div.footnotes` /
`div.crossrefs`. If BibleGateway restructures those, the parser stops finding
verses. To fix:

1. Save the live HTML and compare it against `tests/fixtures/`.
2. Update `tools/bg/parse.py`, and the fixtures if the structure genuinely moved.
3. Run `pytest` (offline, fast), then `pytest -m live` to confirm against the site.

Fixtures are deliberately small: the ESV one is a three-verse excerpt because it
is the only fixture carrying headings, footnotes and cross-references, and
committing a whole copyrighted chapter would contradict gitignoring the cache.
