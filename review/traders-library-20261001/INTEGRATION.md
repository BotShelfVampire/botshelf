# Traders Library — production integration

## This package is an additive section, NOT the whole BSV website

Do not deploy this directory by itself over the existing production site.
The current public BotShelfVampire/botshelf repository has not been established
as the complete production source. A preview, an email sent or a successful
local build is not evidence that the BSV homepage has changed.

Owner-authorized scope: add a free Traders Library category to the BSV homepage,
link it to `/trading/`, and publish the documented trading-source library.
No changes to prices, payment processing, registration, authentication, DNS,
customer data, platform accounts or existing AI products are included.

## Contents

- `trading/`: deployable static section, with 75 independent catalogue entries,
  5 guides and an index (81 HTML pages).
- 35 actual original-source ZIP packages: 34 Pine programs and one EA with
  both MT4 and MT5 source versions. Platform variants are not extra items.
- 40 author-hosted source listings: their public README, source platforms and
  explicit Apache-2.0 repository license listing were checked. No complete
  per-file/dependency audit or BSV redistribution is claimed for these entries.
- `Traders-Library-Preview.html`: self-contained owner-review version containing
  the 35 ZIPs, source displays, all 75 details and all five guides. This is not
  proof of production deployment.
- `Homepage-Category-Preview.html`: the proposed new homepage section alone.
- `integration/`: scoped category markup, CSS and navigation link.
- `build.py`: offline rebuild using catalogues and existing source/license files.
  Run `python3 build.py` from this package to rebuild. No network is needed.
- `seed_*.py`: source reconstruction/editorial scripts, not deployment scripts.
  For the exact dataset: seed_extra.py, seed_mt.py, seed_author.py, then build.py.
- `tests/qa.py`, `tests/qa-report.json`: actual offline checks and their scope.

## Safe addition to the authoritative site

1. Locate and verify the current complete production source and deployed version.
   Preserve a backup and the known rollback path. Check for concurrent changes
   before editing. Do not assume an old source directory is current.
2. Copy only `trading/` into that site's static publish directory, with the
   same `/trading/` URL structure. These files need no serverless function.
3. Copy `integration/homepage-category.css` into the site's appropriate public
   asset directory and add a stylesheet reference on the homepage. Its selectors
   are scoped to `.bsv-traders` and do not style the rest of the existing site.
   Do NOT add `trading/assets/library.css` to the main BSV homepage.
4. Insert `integration/homepage-section.html` as a visible category section near
   the existing primary library/category choices, not hidden in a footer.
   Add the short navigation link from `integration/homepage-nav.html` in the
   appropriate existing main navigation. Keep existing content intact.
5. The homepage component follows the existing `<html lang>` value for EN/JA.
   If the site uses another language mechanism, adapt the two labelled spans
   to that mechanism without introducing a second global language controller.
6. Add the URLs in `trading/sitemap.xml` to the existing sitemap/index. Do not
   replace the old sitemap or unrelated URLs. Test `/trading/` and each `.html`
   route against the existing redirect rules. Keep the library scripts and
   stylesheet on the same origin. Do not disable the site's security headers.
7. Deploy a preview from the complete current site using the established deploy
   process. Retain all current functions, edge functions, redirects and headers.
   In particular, do not revert BSV-R02 access fixes while adding this section.
8. After successful checks below, publish the complete updated site using the
   existing authorized production process. Record the deploy ID and actual URLs.

## Required checks on the real preview and production

- Homepage category is visibly present at desktop and mobile widths and points
  to `/trading/`; existing homepage categories and primary actions remain intact.
- All 81 new pages return the intended content, not only an HTTP 200 fallback.
- EN/JA, multiword search, type/platform/use-case/license/source filters, empty
  results, reset and keyboard focus work with the actual deployed headers.
- Actual localStorage behavior across reloads and between separate item pages;
  blocked storage must not falsely claim persistence.
- Actual HTTPS clipboard action and source ZIP download. Match all 35 ZIP hashes
  to catalog.json and confirm each package contains original source, LICENSE,
  attribution, explanation and provenance. Test a mobile download as well.
- All author-hosted links lead to the intended original projects and licenses;
  if an author changes or withdraws a source, review that entry before claiming
  it remains available. An upstream link is not a local source package.
- Existing registration, authorized content access, commerce, license and other
  primary flows continue to work. Tests must not issue a real trade or payment.
- No old unauthenticated content exposure has been reintroduced. Do not alter
  customer records or request private authentication data as part of testing.

## License boundaries

This is an aggregate. Pine files under MIT retain James Bachini's original MIT
notice. The everget source remains GPL-3.0-only with its original notices and
full GPL license. Spike Trader retains EarnForex's Apache-2.0 license. Its MT5
standard-library includes are supplied by MetaTrader and are not relicensed or
bundled here. Original source files and licenses were checked by Git blob SHA1
and SHA256. Code logic was not changed. The web copy helper adds clearly marked
license comments; original ZIP source remains unchanged.

Do not apply a global MIT notice to these third-party files. Do not remove
attribution or add a proprietary restriction to GPL source. Do not copy third-
party images or promotional performance charts into the site. A source license
is not an absolute legal guarantee or permission to misrepresent a partnership.

## Verification accurately completed here

See tests/qa-report.json. Actual offline checks passed, including source byte
and ZIP validation, local static reference checks and Chromium rendering of our
own HTML in memory. The browser environment denied file:// navigation; policies
were not disabled. These tests do not establish real HTTP delivery, browser
storage persistence, production clipboard/download behavior or live deployment.

No Pine/MQL compilation, broker demo, backtest or live trade was performed.
Known source issues, including Spike Trader's missing broker-side stops and
MT5 position-selection/data-error caveats, remain visible in the entry.

## Acceptance record to return

Return the real homepage and `/trading/` URLs, production deploy ID, category
placement, exact catalogue counts, source ZIP hash checks, the actual HTTP/
mobile/clipboard/storage results, existing-route regression checks and rollback
reference. Mark unavailable checks explicitly. Do not turn SENT, an unpublished
preview, or an unverified completion statement into a production DONE status.
