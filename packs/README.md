# BotShelf Vampire — free prompt pack catalog

Choose a job and open its source. [Try the source-checking exercise](../docs/source-checking-exercise.md) or read the [buyer guide](../docs/buyers.md).

These prompts run in your own AI environment. File presence is not runtime verification. [Contribute a useful improvement](../CONTRIBUTING.md).

## Grok Bot (`grok/`)

- [alt-text-pass.md](grok/alt-text-pass.md) — Write alt text for named images. Don't invent scenes.
- [bio-one-sentence.md](grok/bio-one-sentence.md) — One sentence for the bio. Don't publish.
- [buyer-qa-pass.md](grok/buyer-qa-pass.md) — Walk the buyer path on one page. Don't invent bugs.
- [calendar-before-publish.md](grok/calendar-before-publish.md) — Check the calendar before publish. Stop until Yes.
- [catch-one-breath.md](grok/catch-one-breath.md) — One breath catch line. Don't publish.
- [clip-factory.md](grok/clip-factory.md) — Cut real footage only. No fake voice. Stop before publish.
- [comment-edit-pass.md](grok/comment-edit-pass.md) — Edit one comment. Don't post until Yes.
- [connector-before-browser.md](grok/connector-before-browser.md) — Use the connector first. Don't drive the browser until Yes.
- [dead-link-list.md](grok/dead-link-list.md) — List dead links. Don't rewrite until Yes.
- [empty-shelf-honesty.md](grok/empty-shelf-honesty.md) — Describe an empty paid shelf only when current evidence supports it.
- [evidence-gate-check.md](grok/evidence-gate-check.md) — Check proof of a real run. Missing proof = omit.
- [form-screenshot.md](grok/form-screenshot.md) — Screenshot one form. Don't submit it.
- [four-oh-four-sweep.md](grok/four-oh-four-sweep.md) — List every 404. Don't rewrite until Yes.
- [grok-file-clerk.md](grok/grok-file-clerk.md) — Sort local files. Don’t delete until Yes.
- [grok-research-desk.md](grok/grok-research-desk.md) — Sources only. Missing = omit.
- [hero-copy-pass.md](grok/hero-copy-pass.md) — Draft the hero line. Don't swap live until Yes.
- [i18n-leak-hunt.md](grok/i18n-leak-hunt.md) — Hunt copy leaks across languages. Report only.
- [inbox-propose.md](grok/inbox-propose.md) — Summarize one move. Don’t send the reply.
- [issue-rewrite.md](grok/issue-rewrite.md) — Rewrite one issue. Don't file until Yes.
- [login-handoff.md](grok/login-handoff.md) — Hand off login. Never type a password.
- [marketplace-noun.md](grok/marketplace-noun.md) — Say marketplace, not platform or service.
- [no-spawn-bots.md](grok/no-spawn-bots.md) — One window. Don't spawn bots.
- [numbers-desk.md](grok/numbers-desk.md) — Numbers must match. If they don’t, don’t put them out.
- [og-image-no-jp.md](grok/og-image-no-jp.md) — No Japanese on an English OG image. Don't publish until Yes.
- [one-en-social.md](grok/one-en-social.md) — One English social post. No URL in the body.
- [pack-card-writer.md](grok/pack-card-writer.md) — Write one shelf card. Don't invent GMV.
- [privacy-copy-draft.md](grok/privacy-copy-draft.md) — Draft the privacy lines. Don't publish until Yes.
- [prune-weekly.md](grok/prune-weekly.md) — Propose this week's prune. Don't delete until Yes.
- [register-no-fake-email.md](grok/register-no-fake-email.md) — Check the register form. Don't fill a fake email.
- [reversible-check.md](grok/reversible-check.md) — Mark reversible vs not. Stop on irreversible until Yes.
- [robots-sitemap-check.md](grok/robots-sitemap-check.md) — Check robots and sitemap. Don't deploy until Yes.
- [routine-one.md](grok/routine-one.md) — One item at the hour. Silent on empty days.
- [screenshot-proof.md](grok/screenshot-proof.md) — Take screenshot proof. Don't fake a HUD.
- [seller-qa-pass.md](grok/seller-qa-pass.md) — Walk the seller path on one listing. Don't invent sales.
- [skill-after-clean.md](grok/skill-after-clean.md) — Cut a skill only after a clean run. Don't spawn bots.
- [skill-cutter.md](grok/skill-cutter.md) — One window. Work is skills. Don’t spawn bots.
- [smart-resize-stills.md](grok/smart-resize-stills.md) — Smart Resize stills only. No live price HUD.
- [source-desk.md](grok/source-desk.md) — Copy from sources only. Missing items stay missing.
- [spell-eighty-twenty.md](grok/spell-eighty-twenty.md) — Spell 80 percent and 20 percent. Never shorthand.
- [steal-heat.md](grok/steal-heat.md) — Steal the heat of a title. Don’t copy the words.
- [switchboard-cos.md](grok/switchboard-cos.md) — One window. Ingest and propose. Yes before send.
- [write-then-format.md](grok/write-then-format.md) — Write first. Format second. Don't publish.
- [yes-gate-poster.md](grok/yes-gate-poster.md) — Drafts only. One post after Yes.
- [zip-deploy-gate.md](grok/zip-deploy-gate.md) — Zip the site. Stop before production if gated.

## Claude Code (`claude/`)

- [claude-alt.md](claude/claude-alt.md) — Alt text from filename and visible scene. Don't invent.
- [claude-changelog.md](claude/claude-changelog.md) — Changelog from the diff. Don't publish until Yes.
- [claude-ci-log.md](claude/claude-ci-log.md) — Read the CI log. Don't merge.
- [claude-comment.md](claude/claude-comment.md) — Edit one code comment. Don't push.
- [claude-dead-path.md](claude/claude-dead-path.md) — Find dead paths in the repo. Don't rewrite until Yes.
- [claude-debug.md](claude/claude-debug.md) — Reproduce, then patch. Stop before push.
- [claude-docs.md](claude/claude-docs.md) — README from code. Do not invent APIs.
- [claude-evidence-shot.md](claude/claude-evidence-shot.md) — Capture a proof screenshot. Don't fake a run.
- [claude-four-oh-four.md](claude/claude-four-oh-four.md) — Draft a 404 page from existing copy. Don't deploy until Yes.
- [claude-i18n-keys.md](claude/claude-i18n-keys.md) — Match i18n keys to copy. Don't patch until Yes.
- [claude-lint.md](claude/claude-lint.md) — Lint one file. Don't push.
- [claude-meta-desc.md](claude/claude-meta-desc.md) — Write one meta description from the page. Don't deploy until Yes.
- [claude-no-jp-en.md](claude/claude-no-jp-en.md) — Flag Japanese on English HTML. Don't deploy until Yes.
- [claude-og-meta.md](claude/claude-og-meta.md) — Write OG meta for one page. Don't deploy until Yes.
- [claude-one-job.md](claude/claude-one-job.md) — One job per CLAUDE.md. Don’t dump 20 rules.
- [claude-pr.md](claude/claude-pr.md) — Write the PR body from the diff. Do not open the PR until Yes.
- [claude-prune-files.md](claude/claude-prune-files.md) — List unused files. Don't delete until Yes.
- [claude-readme-open.md](claude/claude-readme-open.md) — README opening from the code. Don't invent APIs.
- [claude-refactor.md](claude/claude-refactor.md) — Refactor one file. Don't push.
- [claude-reversible.md](claude/claude-reversible.md) — Label git moves reversible vs not. Stop on push.
- [claude-review.md](claude/claude-review.md) — Review the diff. Do not merge.
- [claude-robots.md](claude/claude-robots.md) — Draft robots.txt from live rules. Don't deploy until Yes.
- [claude-seo-title.md](claude/claude-seo-title.md) — Write one SEO title from the page. Don't deploy until Yes.
- [claude-sitemap.md](claude/claude-sitemap.md) — Check sitemap URLs against the site. Don't deploy until Yes.
- [claude-skill-cut.md](claude/claude-skill-cut.md) — Cut one skill file. Don't dump 20 rules.
- [claude-tests.md](claude/claude-tests.md) — Write tests. Do not push.
- [claude-types.md](claude/claude-types.md) — Fix types in one file. Don't push.
- [claude-zip-local.md](claude/claude-zip-local.md) — Zip the local site. Stop before production.

## ChatGPT (`chatgpt/`)

- [gpt-bio-line.md](chatgpt/gpt-bio-line.md) — One sentence for the bio. Don't publish.
- [gpt-buyer-qa.md](chatgpt/gpt-buyer-qa.md) — Buyer path copy check. Don't invent bugs.
- [gpt-calendar-copy.md](chatgpt/gpt-calendar-copy.md) — Check the calendar before publish copy. Stop until Yes.
- [gpt-catch-breath.md](chatgpt/gpt-catch-breath.md) — One breath catch line. Don't publish.
- [gpt-draft.md](chatgpt/gpt-draft.md) — Draft only. Don’t publish.
- [gpt-empty-shelf.md](chatgpt/gpt-empty-shelf.md) — Write empty-shelf copy. Don't invent GMV.
- [gpt-evidence-line.md](chatgpt/gpt-evidence-line.md) — Check the proof line. Missing = omit.
- [gpt-form-labels.md](chatgpt/gpt-form-labels.md) — Write form labels. Don't submit the form.
- [gpt-hero-line.md](chatgpt/gpt-hero-line.md) — Draft one hero line. Don't publish.
- [gpt-inbox.md](chatgpt/gpt-inbox.md) — One move. Don’t send the reply.
- [gpt-marketplace-noun.md](chatgpt/gpt-marketplace-noun.md) — Say marketplace, not platform or service.
- [gpt-meeting-recap.md](chatgpt/gpt-meeting-recap.md) — Recap the meeting from notes. Don't invent attendees.
- [gpt-meeting.md](chatgpt/gpt-meeting.md) — Actions from notes. Don’t invent attendees.
- [gpt-meta-desc.md](chatgpt/gpt-meta-desc.md) — Write one meta description. Don't publish until Yes.
- [gpt-og-alt.md](chatgpt/gpt-og-alt.md) — Write OG image alt. No Japanese on English.
- [gpt-one-en-post.md](chatgpt/gpt-one-en-post.md) — One English social post. No URL in the body.
- [gpt-one-gpt.md](chatgpt/gpt-one-gpt.md) — One job per GPT. Don’t spawn 20.
- [gpt-privacy-copy.md](chatgpt/gpt-privacy-copy.md) — Draft privacy lines. Don't publish.
- [gpt-register-copy.md](chatgpt/gpt-register-copy.md) — Check register copy. Don't invent emails.
- [gpt-seller-qa.md](chatgpt/gpt-seller-qa.md) — Seller path copy check. Don't invent sales.
- [gpt-seo-title.md](chatgpt/gpt-seo-title.md) — Write one SEO title. Don't publish until Yes.
- [gpt-shelf-card.md](chatgpt/gpt-shelf-card.md) — Write one shelf card. Don't invent GMV.
- [gpt-shot-caption.md](chatgpt/gpt-shot-caption.md) — Caption one screenshot. Don't fake a HUD.
- [gpt-source.md](chatgpt/gpt-source.md) — Sources only. Missing = omit.
- [gpt-spell-share.md](chatgpt/gpt-spell-share.md) — Spell 80 percent and 20 percent. Never shorthand.
- [gpt-switchboard.md](chatgpt/gpt-switchboard.md) — One window. Propose. Yes before send.
- [gpt-thread-rewrite.md](chatgpt/gpt-thread-rewrite.md) — Rewrite one thread. Don't post until Yes.
- [gpt-write-format.md](chatgpt/gpt-write-format.md) — Write first. Format second. Don't publish.

