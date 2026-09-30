# Netlify production provenance audit

Status: **REVIEW — production deploy identified; authoritative source still missing**  
Task: **BSV-R01-C**  
Checked through the authorized Netlify project/deploy reader: **2026-09-30 JST**

This is a non-mutating provenance record. It does not contain environment variables, customer records, orders, txids, keys, source code, function bodies, account identifiers, or secrets. It does not authorize a deploy, rollback, source replacement, or configuration change.

## Verified production identity

| Field | Verified value |
|---|---|
| Netlify project | `botshelf` |
| Site ID | `7e5c8515-c9a8-48cd-892f-1b9bcbfd5b13` |
| Primary URL | <https://botshelfvampire.com> |
| Current production deploy | `6ab49003e165d1d40fdd9ada` |
| Deploy state/context | `ready` / `production` |
| Published | `2026-09-24T02:50:51.765Z` |
| Immutable deploy URL | <https://6ab49003e165d1d40fdd9ada--botshelf.netlify.app> |
| Deploy source | `cli` |
| Branch label | `main` |

The Netlify project reader and deploy reader agree that this deploy is the current production deploy for the existing site.

## Source-provenance result

The deploy metadata reports:

- `public_repo: false`
- `commit_ref: null`
- `commit_url: null`
- `build_id: null`
- `has_source_zip: false`
- `framework: unknown`
- `entry_path: null`
- `deploy_source: cli`
- `manual_deploy: false`

This evidence does **not** identify an authoritative Git repository, commit, build job, local source directory, or downloadable source archive. The `main` branch label alone is not a commit relationship. The public `BotShelfVampire/botshelf` repository therefore remains an evidence/docs repository and must not be treated as production source.

## Verified deployed runtime surface

The current deploy metadata lists five Node.js 20 serverless functions:

- `commerce`
- `free-access`
- `free-pack`
- `gsd-state`
- `license`

It also reports one deployed edge function. Function bodies and edge-function source were not exposed by the read-only metadata call and were not inferred.

The `commerce` and `license` function names make them relevant candidates for the order-state, payment-confirmation, key, and expiry paths. Names alone do not establish their behavior, whether verification is manual or automatic, whether orders are authoritative, or whether any customer has paid.

## Release artifact versus source backup

The immutable deploy URL is an externally addressable reference to the currently published artifact. It is useful for page comparison and release identification, but it is not a source backup because:

- no source ZIP is retained in the deploy metadata;
- no commit or repository is linked;
- function and edge-function source bodies are unavailable from this read;
- no tested restore or rollback procedure has been evidenced.

Do not perform a rollback, lock, deploy, download attempt, or configuration change without explicit approval and a verified recovery procedure.

## Exact remaining handoff dependency

BSV-R01-C remains blocked for implementation until the existing authorized source holder provides, privately:

1. the authoritative local/repository source location and exact revision that produced deploy `6ab49003e165d1d40fdd9ada`;
2. the CLI command and build/publish directory used for that deploy;
3. the source for `commerce`, `license`, and the relevant edge function;
4. the code path for `SUBMITTED` → `VERIFYING` → `ACTIVE`;
5. the code path that exposes, expires, renews, and revokes the Switchboard key;
6. whether a human decision is required before `ACTIVE`;
7. a tested backup and rollback procedure that preserves functions and configuration;
8. a preview-only build proving that proposed copy changes do not alter order or access behavior.

No raw orders, txids, wallet details, emails, IP addresses, keys, environment variables, or customer records should be placed in GitHub.

## Acceptance decision

- Production deploy identity: **VERIFIED**
- CLI deployment provenance: **VERIFIED**
- Connected Git source: **NOT EVIDENCED**
- Netlify source archive: **NOT AVAILABLE IN METADATA**
- Authoritative production source: **UNKNOWN**
- Backup/rollback procedure: **UNKNOWN**
- Payment-confirmation behavior: **UNKNOWN**
- Key and expiry behavior: **UNKNOWN**
- Copy implementation or deploy: **BLOCKED**

The next accepted action is a source handoff and preview-only review. Do not overwrite production with the public docs repository.
