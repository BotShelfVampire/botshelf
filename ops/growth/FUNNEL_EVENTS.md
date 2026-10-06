# Homepage funnel markers (growth tranche, 2026-10-06)

The site has no analytics script or vendor (homepage loads only first-party JS; Netlify `analytics_instance_id` is null).
Per the owner's lock, nothing new was added or loaded. Funnel steps are marked with the existing `data-evt`
attribute convention (already used by `#layer-marketplace` / `#layer-library`), and every step after the click lands
on a distinct URL, so any analytics the owner later turns on (Netlify Analytics pageviews or server logs) can count the
funnel without code changes.

| Step | Marker (`data-evt`) | Destination (path-level measure) |
|---|---|---|
| Hero band CTAs (owner-approved band, 2026-10-06 21:33 JST) | `home_hero_cta_explore`, `home_hero_cta_browse_all` | `#what-bsv-gives`, `/search/` |
| Hero-adjacent entry | `home_value` (section), `home_hero_cta_browse`, `home_audience_trading`, `home_audience_ai`, `home_value_search` | `/` → `#what-bsv-gives`, `#packs`, `#trader-library`, `#ai-library`, `/search/` |
| Product primitive | `home_primitive_{tools,workflows,agents,templates,research,robotics}` | `/trading/tools/`, `/library/`, `/library/toolkit/`, `/library/skills/`, `/trading/guides/tradingview-alternatives/` (JA `/trading/ja/guides/...`), `/robot-pilot/` |
| Category (8 peer tiles) | `home_cat_{ai,trading,robotics,healthcare,data,space,biotech,quantum}` | `/library/`, `/trading/`, `/robot-pilot/`, `/fields/healthcare/`, `/search/?q=data`, `/fields/space/`, `/fields/biotech/`, `/fields/quantum/` |
| Goal (Browse by goal; holds the moved For traders / Explore AI templates cards) | `home_audience_{trading,ai}`, `home_goal_{ai_workflow,find_trading_tool,build_trading_tool,robot_poc,compare,agent_sdks,medical_robotics}` | `#trader-library`, `#ai-library`, `/library/workflows/`, `/trading/tools/`, `/trading/tools/bsv-builder.html`, `/robot-pilot/`, compare guide, `/library/toolkit/`, `/fields/healthcare/` (research & education only) |
| Resource / workflow start | (existing pages) | `/trading/tools/*.html`, `/library/<runtime>/<team>/`, gated `/library/source/*`, `/trading/items/*` (anonymous → 302 `/register.html?next=` or `/trading/register.html`) |
| Register | `home_register_header` | `/register.html`, `/trading/register.html` |
| Verified access | (not instrumented: auth/entitlement locked) | `/registered` after the email link |

Not measurable today: click counts per marker (no collector). Measurable as soon as pageview analytics exists: every step's destination path, and `next=` on the register redirect.

## Verification (2026-10-07 01:57 JST, LIVE 6ac52627)

- Homepage required markers present with expected hrefs; each path destination HTTP 200.
- Evidence: `ops/growth/FUNNEL_VERIFY_6ac52627.json`.
- Still not measurable as click counts (no collector). Path-level destinations remain the measure.
- Verified-access step still not instrumented (auth lock).
