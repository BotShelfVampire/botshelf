# BSV Traders Library / Creator Studio v2

A review implementation for registered users to discover trading source code
and publish their own original work, for free or for sale.

Open `Traders-Studio-Preview.html` for a standalone, source-free review of the
library, creator form, free/paid settings and dashboard. It deliberately does
not send email, verify an account, save to production, publish a listing, take
payment or execute code. The visible unavailable-service message is honest.

`public/` contains only frontend code and public catalogue metadata.
`private/` contains 39 curated source packages across 7 actual platforms and
40 older author-directory candidates that remain unpublished pending review.
Platform variants are not counted as extra programs.
`server/` implements verified-email, creator ownership, review and paid-access
checks using adapters to existing BSV services. There is no permissive default.
`tests/` contains local tests and their precise scope.

Read `docs/INTEGRATION.md` before any deployment. This is not the full BSV site.
The original registration-free build must not be anonymously deployed.

## Rebuild and local checks

Python 3 and BeautifulSoup are used by the preview generator. Node 22+ is used
by the server logic and unit tests. No source program is executed by this build.

    python build_v2.py
    python extra_platforms.py
    python make_preview.py
    python tests/static_contract.py
    node --test tests/creator-core.test.mjs

Browser DOM checks use installed Playwright and Chromium and no network. They
load self-authored pages in memory and use explicit fake responses. Real URL
navigation was blocked by administrator policy and was not bypassed.

## License scope
Original third-party source remains under the license shipped with each package.
BSV additions do not relicense third-party material. Author names, copyright,
LICENSE, relevant notices, provenance and setup guidance are retained.
The BSV creator-service and frontend code written in this v2 work are provided
under MIT; see LICENSE-BSV.txt. This does not cover third-party source, trademark
rights, existing BSV production code or user-submitted works.
