# Public review scope

This directory is a source-safe review subset of `BSV-Traders-Studio-v3.1.zip`.
It is not the authoritative BotShelf Vampire production source and must not be
deployed as a replacement for the existing site.

Included for review:

- public catalogue, guide, creator and publishing UI;
- server-side domain rules and adapter contracts;
- monthly-only USDT/TRC20 subscription and 20/80 split policy;
- local tests and recorded source-free browser results;
- integration guidance and the source-free standalone preview.

Deliberately omitted:

- `private/` curated source bodies, source ZIPs, full provenance and pending
  author-directory data;
- screenshots and other test images;
- credentials, customer data and production configuration.

Production remains blocked until the current complete production source,
rollback point, verified-email session adapter, durable transactional store and
outbox, rights/security review, native protection bridge, and existing commerce
ledger are connected and independently tested. Local tests do not prove real
registration, payment, publication, native-platform access, customer use or a
Netlify deployment.

