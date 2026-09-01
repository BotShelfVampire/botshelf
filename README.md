# Bot Shelf

A marketplace where you rent out the AI agent team you built, for a fee. That's Bot Shelf.

**Rent out the AI team you built. Get paid.**

Sellers get 100 ready-to-use AI teams, free.

Bot Shelf is a marketplace for Grok Bot, Claude Code, and ChatGPT ready-to-use AI teams. You copy a team, paste it into that AI, fill the buyer blanks, and run the job. The shop does not set it up, debug it, or stay on the line after the sale.

Of the USDT the buyer pays, 80% you / 20% shop.

## Five rules

1. **Proof it ran.** A list needs a real run as proof — a screen or log that the work completed. Paste-anyone text cannot list.
2. **Human Yes.** Send / pay / delete wait for a human Yes in that chat or on that job. Stop until then.
3. **Blanks the buyer fills.** Who you talk to / work for, what may run alone, what always needs Yes, project or account name. You fill them. The team does not.
4. **No after-follow.** No help after you buy, setup help, results promise, refund, or update promise. The shop does not handle complaints, chargebacks, or fights. Seller and buyer settle between themselves only.
5. **Fee.** Of the USDT the buyer pays, 80% you / 20% shop. USDT TRC20 is the live pay path. Card / Stripe is not. The shop does not auto-confirm. This is a sale share, not a subscription cycle.

## What works today

- Free teams on the shelf. Copy the markdown in this repo, or from the shop pages. Free teams stay free until prices are set.
- **USDT TRC20 checkout** for paid lists: https://botshelf.netlify.app/checkout.html — send USDT on TRON / TRC20, then email the txid. The shop does not auto-confirm. ERC20 / BEP20 will not arrive. Not an exchange deposit address.
- Register (email capture, not a login). Sellers and buyers both start there.
- Rate a seller (stars plus good / ok / not good). Ratings sit on the seller, not the shop. A rating is not a ticket.
- How-to, list rules, and the three AI tabs.

## What is not live

**Card / Stripe is not live.** There is no card field. List is not fully wired to the public paid shelf yet. Sending the Sell form does not put a team up. Free teams stay free. We do not invent sales counts or "X sellers made $Y".

Paid path: buyer sends USDT on TRON/TRC20 to the shop address, emails the txid, team is delivered privately when the shop checks it by hand. Of the USDT the buyer pays, 80% you / 20% shop. No auto-confirm. No after-follow. No refunds. No stepping in. Sale and use = your own risk.

## Links

- Shop: https://botshelf.netlify.app
- Pay (USDT TRC20): https://botshelf.netlify.app/checkout.html
- Register: https://botshelf.netlify.app/register.html
- Sell: https://botshelf.netlify.app/sell.html
- Grok Bot teams: https://botshelf.netlify.app/grok.html
- Claude Code teams: https://botshelf.netlify.app/claude.html
- ChatGPT teams: https://botshelf.netlify.app/chatgpt.html
- How to use: https://botshelf.netlify.app/how.html
- X: [@getbotshelf](https://x.com/getbotshelf)

## Not official

Not an official xAI, Anthropic, or OpenAI shop. Sale and use = your own risk.

## How to use a team

Pick the file for the AI you actually run. Fill every blank. Then paste:

- **Grok Bot** — Open Grok Bot → click the bot’s name at the top of the chat (or Cmd+Shift+I) → click the gear next to the X → paste into **Description** → fill the blanks → talk to that bot.
- **Claude Code** — Paste into `CLAUDE.md` in the project root (or the project’s instruction file). Fill blanks. Run the job. Stop before git push / merge / spend unless a human said Yes.
- **ChatGPT** — New chat → paste as Custom Instructions, or create a Custom GPT → paste into Instructions. Fill blanks. Do not publish or send until Yes.

The shop will not install it for you.

## Files in this repo

See [packs/README.md](packs/README.md). All files here are the free shelf copies.

```
packs/grok/      Grok Bot
packs/claude/    Claude Code
packs/chatgpt/   ChatGPT
```

## License

MIT. See [LICENSE](LICENSE).
