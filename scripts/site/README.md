# Live-site integration for trader-toolkit/ and ai-toolkit/

These scripts put the repo catalogs into the **existing** live categories on https://botshelfvampire.com.
They do not create new categories. The live-site source is not in this repository. It is the current
Netlify production deploy of site `7e5c8515-c9a8-48cd-892f-1b9bcbfd5b13`.

## What gets generated

| Surface | Public | Behind the email-verified session gate |
| --- | --- | --- |
| Trader: `/trading/build/` hub (7-step path, start points, platform/type/test-status filters, compatibility) | yes | — |
| Trader: `/trading/tools/bsv-<id>.html` summaries (32: 20 catalog entries + 12 recipes) | yes | — |
| Trader: `/trading/items/bsv-<id>.html` source + copy, `/trading/downloads/bsv-<id>.zip` (source + LICENSE) | — | yes (existing gate) |
| Recipes: JSON + pre-generated Pine v6 / MQL5 / cTrader starters, with honest TODO counts | — | yes |
| AI: `/library/toolkit/` hub (by job, by framework, filters) + `/library/toolkit/<id>/` summaries | yes | — |
| AI: `/library/source/<id>.html` / `.zip` | — | yes (`/library/source/*` added to `free-session-gate.ts`) |
| Entry blocks in `/trading/index.html` and `/library/index.html` (between `BSV-TOOLKIT` markers) | yes | — |
| `/search/` index rows, `sitemap.xml`, register return link for `/library/source/*` | yes | — |

The catalog status is copied as-is. Nothing is labelled Verified. "Runtime-tested by BSV" is shown as 0 until there is real evidence.

## Run

```bash
python3 scripts/site/build_live_toolkit.py --site <site-tree>      # idempotent
python3 scripts/site/test_live_toolkit.py --site <site-tree>       # local checks
python3 scripts/site/test_live_toolkit.py --live https://botshelfvampire.com   # LIVE checks
```

`test_live_toolkit.py` checks the following:

- No toolkit source line appears on a public page.
- Every gated path is covered by the edge gate.
- On LIVE, anonymous requests to gated paths are redirected: `/trading/items/*` goes to the public summary, and the other gated paths go to registration.
- Internal links resolve, entry points exist, and there is no forbidden copy.

## Deploy method used on 2026-10-03 (Netlify CLI, no spend; auto top-up is off on the account)

1. Fetch the current production source. Use the Netlify deploy download, or reuse the box copy only after checking it against the published deploy id.
2. Build into a copy of that tree, then run the local tests.
3. Make the layout. Static files go to `deploy/site/`. `netlify/`, `netlify.toml`, `package.json` and `node_modules` stay **outside** the publish dir, so the function sources and `_free_bodies.json` are never uploaded as static files.
4. Run `netlify deploy --dir site --functions netlify/functions --site <id>` to create a draft. Compare it with production: 6 functions, 2 edge functions, 107 redirects, 22 header rules.
5. Re-check that the published deploy id has not changed, then publish that exact draft (`restoreSiteDeploy`).
6. Run the LIVE tests.

CSS and JS on this site are served `immutable`, so changed assets must get new file names. The build script adds a content hash to its own CSS/JS names.

## CI proposal

`site-integration-check.workflow.yml` is a ready-to-use GitHub Actions workflow. The bot token has no `workflow` scope, so someone with that scope needs to move it to `.github/workflows/`.
