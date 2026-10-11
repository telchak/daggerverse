# Vendored okf-skills

The `okf`, `validate`, `visualize` and `backfill` skills in this directory, and the
`event-analyzer` and `bundle-weaver` subagents in `../agents/`, are copied verbatim from
[scaccogatto/okf-skills](https://github.com/scaccogatto/okf-skills):

- Commit: `8e3187875e66051bb52f91a5ed27342e2c3208da` (plugin version 0.10.0)
- License: MIT, see [`okf-skills.LICENSE`](okf-skills.LICENSE). The OKF v0.2 spec at
  `okf/reference/SPEC.md` is Apache-2.0 (c) Google LLC, see `okf/reference/APACHE-2.0.txt`.

## Differences from the plugin install

Installed as project skills, the names carry no `okf:` plugin prefix:

| Plugin form | Here |
|---|---|
| `/okf:okf` | `/okf` |
| `/okf:validate` | `/validate` |
| `/okf:visualize` | `/visualize` |
| `/okf:backfill` | `/backfill` |
| `okf:event-analyzer` subagent | `event-analyzer` |
| `okf:bundle-weaver` subagent | `bundle-weaver` |

The plugin's MCP server and dormant Stop hook are not vendored. This repository uses
the soft-mode upkeep described in the root `CLAUDE.md`.

The scripts need [`uv`](https://docs.astral.sh/uv/) (or `python3` with `pyyaml`):

```bash
uv run .claude/skills/validate/scripts/okf_validate.py .okf --strict
uv run .claude/skills/visualize/scripts/okf_visualize.py .okf -o /tmp/okf-viz.html
```

To update, re-copy `skills/{okf,validate,visualize,backfill}` and `agents/*.md` from a
newer okf-skills commit and bump the commit above.
