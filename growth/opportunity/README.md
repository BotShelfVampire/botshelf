# BSV Opportunity Feed — deterministic evidence ranking

This utility ranks builder opportunities from **real recorded signals**.

It is not:
- a revenue forecast
- an estimate of market size
- a promise that a request will convert
- permission to fabricate demand

## Inputs

One JSON array of opportunity buckets.

Each bucket should contain:

- `jobKey`
- `sector`
- `platform`
- `openRequests`
- `uniqueRequesters`
- `noResultSearches`
- `missingVariantSignals`
- `remixSignals`
- `explicitWtpActors`
- `fulfilledRequests`

Use only deduplicated, privacy-safe aggregate counts.

## Ranking

The score is intentionally simple and public:

```
score =
  min(uniqueRequesters, 10) * 8
+ min(openRequests, 20) * 2
+ min(noResultSearches, 25) * 1
+ min(missingVariantSignals, 10) * 2
+ min(remixSignals, 10) * 1
+ min(explicitWtpActors, 5) * 6
- min(fulfilledRequests, 10) * 2
```

Floor at 0.

The output always includes the component counts and formula version.

Why:
- real requester diversity matters most
- explicit willingness-to-pay is a strong but bounded signal
- no-result search indicates missing supply
- already fulfilled requests reduce urgency
- the formula is inspectable

BSV can change weights later only with a version bump and measured reason.

## Usage

```bash
node growth/opportunity/rank.mjs input.json > ranked.json
```

The script does not call an LLM or external service.
