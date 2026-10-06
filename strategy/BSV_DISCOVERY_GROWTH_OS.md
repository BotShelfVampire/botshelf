# BSV Discovery & Growth OS

Updated: 2026-10-03
Status: P0 growth infrastructure

## Objective

Make BSV unusually easy to discover and understand by:

- human search engines
- AI answer/search systems
- technical builders
- trading/robotics/frontier-industry users
- software agents and future machine clients

Growth must come from real utility, not thin programmatic pages.

## Core rule

Every indexed page should contain at least one hard asset:

- working source/template
- real request/demand signal
- exact compatibility/prerequisite data
- reproducible workflow
- verified or explicitly unverified evidence
- useful comparison
- failure/limitation record

Do not generate hundreds of empty sector/platform landing pages merely to target keywords.

## Search + AI search

### Google

Google's current guidance for AI features still relies on core Search quality/ranking systems. Normal SEO remains relevant.

Therefore:
- crawlable public pages
- canonical URLs
- accurate titles/H1/meta descriptions
- useful internal links
- sitemap
- robots rules
- structured data only when it truthfully matches page content
- original utility/evidence

### ChatGPT search

OpenAI currently separates:
- OAI-SearchBot: search/discovery
- GPTBot: model-training crawl
- ChatGPT-User: user-initiated page fetches

BSV can intentionally allow search discovery while independently deciding whether to allow training crawl.

Recommended privacy/discovery posture to test:
- OAI-SearchBot: allow public pages
- GPTBot: disallow by default unless owner later chooses otherwise
- private/account/gated source: never expose merely for AI discovery

OpenAI states these controls are independent.

### AIO / AEO / ACO

Treat these as an engineering discipline, not a magic ranking trick.

Optimize public BSV pages so an answer engine can extract:
- what this asset does
- exact platform/runtime
- inputs
- outputs
- prerequisites
- price/access
- verification state
- known limitations
- source/license
- canonical URL

This is where the Universal Capability Manifest becomes strategically important.

## Public / gated split

Public:
- summary
- purpose
- supported platform
- prerequisites
- verification state
- limitation/failure notes
- seller public attribution if opted in
- price/access terms
- real demand/request metadata where public

Gated:
- email-gated free source where product policy requires it
- paid protected source
- private seller/customer data
- unpublished requests
- private pilot evidence

Search engines and AI systems should have enough public metadata to understand the asset without bypassing access controls.

## Structured data

Use Schema.org/Google-supported types only where the page actually qualifies.

Good candidates:
- Organization for BSV brand/support identity
- Product + Offer for eligible paid/free marketplace product pages
- BreadcrumbList for hierarchy
- Dataset / DataDownload for genuine public datasets
- Article only for actual editorial/article pages
- QAPage only when the page truly contains a question and answers

Do not add structured data merely because a rich-result type exists.

Operator identity principle:
Organization markup can identify the operating brand and support contact without publishing a founder persona.

## Machine-readable BSV layer

Public endpoints/files should eventually expose:
- capability manifests
- public asset catalogs
- public request manifests
- verification state
- canonical URLs
- sector/platform taxonomy
- version/update timestamps

This enables agents to search BSV without scraping card prose.

## Experimental llms.txt

BSV may publish an experimental `/llms.txt` as a compact map for AI agents.

Important:
- llms.txt is supplementary, not a substitute for robots.txt, sitemap, canonical links or normal crawlability.
- include only public, stable URLs
- do not expose gated/private paths
- regenerate it from actual public inventory

## Builder acquisition

The strongest acquisition page for engineers is not:
"Sell your AI tool."

It is:
"These are real problems users are asking to solve."

Public Builder Opportunity pages should show only real signals:
- open requests
- repeated no-result searches
- requested platforms
- missing variants
- explicit WTP when supplied
- fulfilled/unfulfilled state

Never invent revenue estimates.

## Content strategy

High-value page patterns:

### Build pages
"Build a custom TradingView liquidity-sweep alert"
"Build an Isaac Teleop pilot evidence pipeline"
"Build a Hugging Face MCP research desk"

Each must contain real source/workflow or a concrete implementation path.

### Request pages
"Need a Bookmap X tool"
"Need a robot-pilot QA dashboard"

Index only public requests with enough substance.

### Compatibility pages
"BSV Trader Recipe support by platform"
"Robot Pilot evidence support by runtime"

### Failure/limitation pages
Publicly useful when they prevent repeated mistakes.

### Comparison pages
Only when based on documented capabilities and scoped use cases.

## Organic loops

1. Search finds a concrete build page.
2. User registers/downloads/remixes.
3. User posts a missing capability request.
4. Request becomes visible to builders.
5. Builder publishes solution.
6. Product page attracts search/AI referrals.
7. More demand arrives.

This is better than publishing generic AI news at scale.

## Metrics

Discovery:
- Google organic entrances
- ChatGPT referral traffic
- other AI referral traffic
- indexed public utility pages
- crawler errors
- no-result site search

Activation:
- email registrations from public utility pages
- free-access activation
- remix starts
- request creation

Supply:
- builder signup
- first listing
- request-to-product conversion

Commerce:
- purchase conversion
- GMV
- seller earnings
- renewal

## Audit loop

At least weekly:
- fetch current robots.txt
- fetch sitemap
- verify canonical tags
- sample structured data
- test OAI-SearchBot accessibility on public pages
- verify gated paths remain gated
- inspect no-result search terms
- identify public pages with impressions but weak activation

Do not declare AIO/SEO success from implementation alone.
Measure referrals and conversion.
