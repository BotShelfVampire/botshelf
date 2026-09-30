# GitHub review scope

This directory is the source-safe review subset of `BSV-Traders-Studio-v2.zip`.

The full local artifact was verified at 2,427,865 bytes with SHA-256
`36828e3b1c9fc9905adc8f9979871d32af996bb3e10680d807cf97068fb8f5c1`.
Its local Node suite passed 30/30 tests and its full-artifact static suite passed
325 checks. Those checks are not production authentication, commerce, runtime,
deployment, compilation, backtesting or live-trading evidence.

The public GitHub review branch intentionally omits:

- `private/` source bodies, downloadable archives, full provenance and pending
  author-directory data;
- screenshots and other binary review captures.

The generated standalone preview is included because it contains no curated or
user source payload. Its reviewable components are also present under `public/`
and `server/`.

Those omissions prevent the review repository from becoming an anonymous source
delivery route. The gated payload remains in the verified local artifact and must
be connected only to the authoritative production private store. `public/` is
metadata and UI only. `server/` contains adapter-based domain logic that fails
closed until the real BSV authentication, durable store, review and commerce
adapters are connected.

Do not deploy this review directory as the whole site. Do not deploy the example
Netlify entry without replacing every test/example adapter with the current BSV
production interfaces and completing the release checks in `docs/INTEGRATION.md`.
