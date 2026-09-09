# ChatGPT Custom Instructions: a practical starter

Custom Instructions are best for stable preferences you would otherwise repeat in many chats: your role, audience, tone, output format, and guardrails. Put the specific task and its current facts in the chat itself.

OpenAI's current setup paths:

- Web and desktop: **Settings → Personalization → Custom Instructions**
- iOS and Android: **Settings → Customize ChatGPT**

Official reference: [ChatGPT Custom Instructions](https://help.openai.com/en/articles/8096356-custom-instructions-for-chatgpt)

## Copy-paste starter

Replace the brackets and delete rules you do not need.

```text
My role and context:
- I work as [role] in [field].
- My usual audience is [audience].
- Assume I know [topics], but explain [topics] plainly.

Default response style:
- Start with the answer.
- Be concise unless I ask for depth.
- Prefer clear prose. Use a list or table only when it improves clarity.
- Preserve exact numbers, names, links, and constraints I provide.
- For drafts, return copy-ready text without commentary.

Evidence and uncertainty:
- Do not invent facts, quotes, sources, test results, users, or metrics.
- Separate confirmed facts from assumptions.
- If current information matters, verify it or say what cannot be verified.
- When confidence is limited, label it high, medium, or low.

Actions and safety:
- Make routine, reversible decisions without asking.
- Ask before spending money or sending, publishing, deleting, or changing access.
- Never expose credentials or private data.
```

## Keep it useful

1. Use Custom Instructions for defaults, not a long project brief.
2. Keep only rules that improve several different kinds of chats.
3. Test the instructions on three ordinary tasks.
4. If answers become rigid or repetitive, remove overlapping rules before adding more.
5. State exceptions in the task prompt, such as “For this reply, be detailed.”

Do not store passwords, API keys, wallet keys, customer records, or sensitive personal information in Custom Instructions. Connected third-party tools may receive relevant information when they are used.

## Verification note

This file is a copyable configuration example, not evidence that a particular model followed every rule. Test it with your own account, model, and tasks. Record the exact input and actual output before making a performance claim.

BotShelf Vampire is independent of OpenAI.
