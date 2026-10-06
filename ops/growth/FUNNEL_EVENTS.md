# Homepage funnel markers (growth tranche, 2026-10-06)

The site has no analytics script or vendor (homepage loads only first-party JS; Netlify `analytics_instance_id` is null).
Per the owner's lock, nothing new was added or loaded. Funnel steps are marked with the existing `data-evt`
attribute convention (already used by `#layer-marketplace` / `#layer-library`), and every step after the click lands
on a distinct URL, so any analytics the owner later turns on (Netlify Analytics pageviews or server logs) can count the
funnel without code changes.

| Step | Marker (`data-evt`) | Destination (path-level measure) |
|---|---|---|
| Hero-adjacent entry | `home_value` (section), `home_hero_cta_browse`, `home_audience_trading`, `home_audience_ai`, `home_value_search` | `/` → `#what-bsv-gives`, `#packs`, `#trader-library`, `#ai-library`, `/search/` |
| Product primitive | `home_primitive_{tools,workflows,agents,templates,research,robotics}` | `/trading/tools/`, `/library/`, `/library/toolkit/`, `/library/skills/`, `/trading/guides/tradingview-alternatives/` (JA `/trading/ja/guides/...`), `/robot-pilot/` |
| Field / goal | `home_field_{ai,trading,robotics}`, `home_goal_{ai_workflow,find_trading_tool,build_trading_tool,robot_practice,compare,agent_sdks}` | `/library/`, `/trading/`, `/robot-pilot/`, `/library/workflows/`, `/trading/tools/`, `/trading/tools/bsv-builder.html`, `/library/toolkit/` |
| Resource / workflow start | (existing pages) | `/trading/tools/*.html`, `/library/<runtime>/<team>/`, gated `/library/source/*`, `/trading/items/*` (anonymous → 302 `/register.html?next=` or `/trading/register.html`) |
| Register | `home_register_header` | `/register.html`, `/trading/register.html` |
| Verified access | (not instrumented: auth/entitlement locked) | `/registered` after the email link |

Not measurable today: click counts per marker (no collector). Measurable as soon as pageview analytics exists: every step's destination path, and `next=` on the register redirect.
