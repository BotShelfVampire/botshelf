# BSV Field Labs

Four original, local browser tools with complete English and Japanese UI and explanations. No server/API dependency, tracking, external fonts or paid model calls. Static code is intended to be public; no source gate is required.

## Add to the actual full production source

Run `python3 scripts/site/build_field_labs.py --site /path/to/full/staging/site` after the main site generators. This directory and this repository are **not** a full deployment tree. Use the existing production pipeline and fold into its next ready batch.

The generator copies `/labs/`, uses content hashes for JS/CSS asset names, and emits `/labs/catalog.json`. Merge its entries into the existing discovery/search system using that system's actual schema. Each entry counts as one original interactive tool; do not inflate category counts from translated copies. Connect the four homepage categories to the existing field hubs when present, otherwise to the respective `/labs/<field>/` tool. Replace the corresponding Coming soon label only when its tool is in the same deploy. Keep GrokBot's complementary workflows and field content intact.

The hub is `/labs/`. Tool paths are `/labs/healthcare/`, `/labs/space/`, `/labs/biotech/`, `/labs/quantum/`; append `?lang=ja` for Japanese. Switches and lab navigation preserve language. Other site languages currently use English on these new tools; no five-language completeness claim is made.

Verify only the added pages and changed links at phone/desktop widths, both languages, and the tool calculations/actions. No Netlify preview deployment is needed for local checks. Record production URLs and the actual deploy id after the existing publisher ships the batch.
