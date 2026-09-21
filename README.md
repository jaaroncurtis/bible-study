# bible-studies

Study notes, and the tooling that feeds them.

## Layout

| Path | What |
|---|---|
| `notes/` | The study notes themselves |
| `tools/bg/` | BibleGateway fetch/parse/cache CLI (`python -m bg`) |
| `cache/` | Chapter JSON, plus cached catalogues and searches. **Gitignored.** |
| `.claude/skills/` | Repo-local skills |

## Setup

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

## Usage

```bash
python -m bg fetch "Romans 8:28-30"        # defaults to ESV
python -m bg chapter Romans 8
python -m bg search "faith without works"
python -m bg versions --audio              # translations with a recording
python -m bg reading-plans
python -m bg cache-status
```

Scripture text is retrieved from [BibleGateway](https://www.biblegateway.com) and
remains under the copyright of the respective translation publishers. Each cached
chapter carries its translation's copyright notice.
