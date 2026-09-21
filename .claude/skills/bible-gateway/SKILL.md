---
name: bible-gateway
description: Use when pulling anything from BibleGateway for these study notes - looking up a passage, searching for a phrase, checking which translations exist or have audio, listing reading plans, seeing what is cached, or diagnosing a failed lookup. Covers the `python -m bg` CLI, the JSON cache, citation and copyright rules, and what to do when BibleGateway changes its markup.
---

# Pulling from BibleGateway

BibleGateway has no public API, so this repo scrapes it. The `bg` CLI is the
only thing that should talk to the site: it paces requests, caches everything it
pulls, and returns structured JSON.

## Running it

Always use the repo's virtualenv:

```bash
.venv/Scripts/python -m bg fetch "Romans 8:28-30"
```

| Command | Does |
|---|---|
| `bg fetch "<reference>"` | Verses of a reference |
| `bg chapter <book> <n>` | One whole chapter document |
| `bg search "<phrase>"` | Keyword search, 25 hits per page |
| `bg versions` | Every translation, with audio availability |
| `bg reading-plans` | BibleGateway's reading plans |
| `bg cache-status` | How many chapters are cached, and in which translations |

Common flags: `--version ESV` (default ESV), `--refresh` (refetch even if
cached). `versions` also takes `--filter TEXT` (matches name or code),
`--language en`, `--audio`. `search` takes `--start N` for later pages.

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

`search` returns `{query, version, total, results[], next_start}`. `total` is the
full hit count; `results` is one page of 25. Each hit has `reference`, `osis`
(machine-readable, e.g. `Num.12.7`) and `text`. Page on with
`--start <next_start>` - **each page is another 15s request**, so pull pages
only when the hits you have are not enough.

## Audio is a version attribute, not a listing

BibleGateway publishes no machine-readable audio index - `/resources/audio/` is
a marketing page about devotionals. The versions table is the only structured
statement of which translations have a recording, so audio appears as
`"audio": true` on a version. `bg versions --audio` lists them (34 of 240).

## The cache is the point

```
cache/bible/<VERSION>/<Book>/<NNN>.json   chapters
cache/catalog/versions.json               translation list
cache/catalog/reading-plans.json          reading plans
cache/search/<VERSION>/<query>-<page>.json  search results
```

All gitignored. A chapter is fetched at most once, because BibleGateway returns
the whole chapter however narrow the reference. So:

- A second lookup inside a cached chapter is instant and silent.
- **Reading a cached chapter file directly is fine and preferred** when building
  note content - that is what the JSON is for. Do not shell out to `bg` to
  re-read something already on disk.
- `--refresh` only when you suspect the cached copy is wrong. The catalogues
  never expire on their own; refresh them if a translation looks missing.

## Pacing - plan around it

BibleGateway's robots.txt asks for a 15 second crawl delay, and the fetcher
enforces it across processes. Cache hits are free; **every uncached request
costs ~15s**.

Before a multi-chapter pull or a multi-page search, say so up front: "Romans
8-12 is 5 uncached chapters, about 75 seconds." Never fire off a book-sized pull
without flagging the wait first.

## Copyright

Most translations (ESV, NIV, NASB, MSG) are copyrighted; the KJV and ASV are
public domain.

- The cache is gitignored on purpose. Do not commit scripture text into the repo,
  and do not paste whole chapters of a copyrighted translation into files that
  will be committed.
- Every cached chapter carries its `copyright` string. Notes that quote a
  translation must carry its attribution.
- Quote what the study needs. Do not bulk-pull whole books.

## When something fails

| Symptom | Meaning |
|---|---|
| `Unknown book 'X'. Did you mean ...?` | Alias missing - add it to `tools/bg/books.py` |
| `... is not a reference` | Reference didn't match the grammar; check the shape |
| `Romans 8 has verses 1-39, not 99-99` | Reference runs past the chapter |
| `page contains no passage content` / `no verses` | Bad version code, or BibleGateway changed its markup |
| `search` returns 0 results but the site shows some | Result markup moved; see below |

Markup drift is the failure that matters. The parsers read:

- verses from `span.text` classes (`Rom-8-1`), notes from `div.footnotes` /
  `div.crossrefs`
- search hits from `div.search-result-list li.bible-item`, the total from
  `.showing-results`
- translations from `td.translation-name`, audio from `td.translation-types`
- plans from `div.plan-item`

To fix drift:

1. Save the live HTML and compare it against `tests/fixtures/`.
2. Update the parser in `tools/bg/`, and the fixtures if the structure moved.
3. Run `pytest` (offline, fast), then `pytest -m live` to confirm against the site.

Fixtures are deliberately small where they can be: the ESV one is a three-verse
excerpt because it is the only fixture carrying headings, footnotes and
cross-references, and committing a whole copyrighted chapter would contradict
gitignoring the cache.
