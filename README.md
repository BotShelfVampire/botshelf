# BotShelf Vampire — ready-to-use AI teams

Copy a focused AI workflow, add your context, and review the result. This repository contains free prompt packs for **Grok Bot, Claude Code, and ChatGPT**, with jobs such as source-based research, draft replies, meeting notes, and code review.

[Browse the packs](packs/README.md) · [Marketplace](https://botshelfvampire.com/) · [Build Library](https://botshelfvampire.com/library/)

## Start with one useful job

| What you need | Free source | What to provide |
| --- | --- | --- |
| Summarize sources without inventing facts | [Source desk](packs/chatgpt/gpt-source.md) | A question and labeled source excerpts |
| Review a code change | [Diff review](packs/claude/claude-review.md) | A diff and the behavior you expect |
| Turn incoming information into a next step | [Inbox propose](packs/grok/inbox-propose.md) | The message and the decision you need |
| Extract actions from a meeting | [Meeting actions](packs/chatgpt/gpt-meeting.md) | Notes, known owners, and stated deadlines |

1. Open a pack for the AI you use and read its scope and stop conditions.
2. Fill its context blanks, allowed sources, and approval boundaries.
3. Give it a small input you can check yourself.
4. Inspect the output against the original input before using it. Keep a redacted run record if you want to share what worked.

These are instructions you run with your own AI, account, and tools. A prompt does not itself install an integration or enforce permissions. Role-based prompts do not automatically create independently running agents.

## Marketplace and Build Library

| Path | Purpose | Where to start |
| --- | --- | --- |
| **Ready-to-use Marketplace** | Job-based AI team products for Grok Bot, Claude Code, and ChatGPT; free and paid listings | [Browse teams](https://botshelfvampire.com/) · [Buyer guide](docs/buyers.md) |
| **Build Library** | Prompts, workflow recipes, code sketches, and MCP-oriented packs to adapt for local or self-hosted use | [Canonical Library](https://botshelfvampire.com/library/) · [GitHub registry source](https://github.com/BotShelfVampire/botshelf-ai-team-registry) |
| **Create and list your own team** | Adapt a workflow, test a real job, and submit an evidence-backed listing | [Seller guide](docs/sellers.md) · [Submit a team](https://botshelfvampire.com/sell.html) |

A Library team is a job concept. Its runtime variants are implementations of that job, not additional Marketplace products. Use the live pages for current availability, prices, rental periods, and terms; this repository is not a live inventory or sales report.

## Practical boundaries

- **Evidence:** inspect the proof attached to the exact version you plan to use. File presence or a previous claim that a workflow ran is not verification of your model and setup.
- **Human review:** define what may run alone. Sending, publishing, spending, deleting, pushing, and merging require the authorization specified for that job.
- **Missing inputs:** leave unknown facts, owners, deadlines, and metrics unknown.
- **Your environment:** you supply the AI runtime and any required subscriptions or tools. Review permissions before connecting accounts.
- **Commercial terms:** check the [buyer information](https://botshelfvampire.com/for-buyers.html) and [seller information](https://botshelfvampire.com/for-sellers.html). Repository files do not promise installation, ongoing support, results, or updates.

## Files

- [Pack catalog](packs/README.md): browse the free Markdown source by runtime.
- [Buyer guide](docs/buyers.md): choose a workflow and check a first run.
- [Seller guide](docs/sellers.md): turn an adaptation into a reviewable submission.
- [Build Library source](https://github.com/BotShelfVampire/botshelf-ai-team-registry): Ollama, LM Studio, Open WebUI, n8n, CrewAI, LangGraph, and MCP materials.

## BotShelf Vampire links

[Website](https://botshelfvampire.com/) · [How it works](https://botshelfvampire.com/how.html) · [Register](https://botshelfvampire.com/register.html) · [X: @botshelfvampire](https://x.com/botshelfvampire)

BotShelf Vampire is independent and is not an official xAI, Anthropic, or OpenAI marketplace.

## License

The files in **this repository** use the [MIT License](LICENSE). The [Build Library registry](https://github.com/BotShelfVampire/botshelf-ai-team-registry/blob/main/LICENSE) has a separate license; Marketplace product terms are separate.
