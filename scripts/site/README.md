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
| Library: 70 team implementations `/library/<runtime>/<team>/` keep explanation, files, examples (`gate_library_bodies.py`) | yes | — |
| Library: full prompt / config / code `/library/source/team-<runtime>-<team>.html`; `body` removed from `/library/catalog/items.json` | — | yes |
| Trader: recipe builder summary `/trading/tools/bsv-builder.html` + entry in `/trading/build/` | yes | — |
| Trader: recipe builder `/trading/items/bsv-builder.html` + generator port `/trading/sources/bsv-builder.<hash>.js` (`build_recipe_builder.py`) | — | yes |
| AI toolkit ↔ Library Teams cross-links (`build_crosslinks.py`, mapping `ai_team_links` in the copy file) | yes | — |

The catalog status is copied as-is. Nothing is labelled Verified. "Runtime-tested by BSV" is shown as 0 until there is real evidence.

## Run

Run in this order (all idempotent):

```bash
python3 scripts/site/build_live_toolkit.py --site <site-tree>
python3 scripts/site/gate_library_bodies.py --site <site-tree>     # also prunes *.bak* and library generator scripts
python3 scripts/site/build_recipe_builder.py --site <site-tree>
python3 scripts/site/build_crosslinks.py --site <site-tree>
node    scripts/site/test_builder_parity.mjs <site-tree>          # browser port == render.mjs (12 recipes x 3 targets)
python3 scripts/site/test_library_gate.py --site <site-tree> --orig <pre-gate tree>
python3 scripts/site/test_library_gate.py --live https://botshelfvampire.com --orig <pre-gate tree> --cookies <operator test cookie jar>
python3 scripts/site/test_live_toolkit.py --site <site-tree>       # local checks
python3 scripts/site/test_live_toolkit.py --live https://botshelfvampire.com   # LIVE checks
```

`test_live_toolkit.py` checks the following:

- No toolkit source line appears on a public page.
- Every gated path is covered by the edge gate.
- On LIVE, anonymous requests to gated paths are redirected: `/trading/items/*` goes to the public summary, and the other gated paths go to registration.
- Internal links resolve, entry points exist, and there is no forbidden copy.

## Deploy method (updated 2026-10-03 after the context incident) (Netlify CLI, no spend; auto top-up is off on the account)

1. Fetch the current production source. Use the Netlify deploy download, or reuse the box copy only after checking it against the published deploy id.
2. Build into a copy of that tree, then run the local tests.
3. Make the layout. Static files go to `deploy/site/`. `netlify/`, `netlify.toml`, `package.json` and `node_modules` stay **outside** the publish dir, so the function sources and `_free_bodies.json` are never uploaded as static files.
4. Run `netlify deploy --prod --dir site --functions netlify/functions --site <id>` (production context).
   **Never publish a draft deploy with `restoreSiteDeploy`.** A CLI draft has context `deploy-preview`; once published it runs
   without the production-scoped env vars (SMTP, operator email). On 2026-10-03 this broke OTP registration and the operator
   digest from 16:04 to 16:23 JST until a `--prod` redeploy fixed it.
5. Check `/api/commerce/health` shows `"email_configured":true`, then run the LIVE tests (anonymous + operator test session).

CSS and JS on this site are served `immutable`, so changed assets must get new file names. The build script adds a content hash to its own CSS/JS names.

## CI proposal

`site-integration-check.workflow.yml` is a ready-to-use GitHub Actions workflow. The bot token has no `workflow` scope, so someone with that scope needs to move it to `.github/workflows/`.

## Operator test account (logged-in QA)

`support@botshelfvampire.com`, display name `OTP test` (classified `test` by `customerRecords.js`, not a customer).
It is created through the normal OTP flow; the code is read from the support mailbox over IMAP. The session cookie jar lives only on
the operations box (`/workspace/bsv-live/qa/opstest.cookies.txt`, mode 600) and is never committed.
