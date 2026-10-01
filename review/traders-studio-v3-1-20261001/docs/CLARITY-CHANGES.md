# Traders Studio v3.1 — plain-language UI changes

The actual UI is revised, not only this document. This package is a local review build, not a deployed production service.

## Where the explanation appears

- Homepage integration fragment: registration, monthly-only pricing, USDT/TRC20 and 80/20 before the user enters the library.
- Library: separate explanations for people using tools and people publishing work, with a 100 USDT -> 80/20 example.
- Every trading page: discoverable How it works link.
- Guide: registration, publication, page visibility versus source visibility, source protection and invite-only, fees, 30-day periods, renewal, remakes and testing status.
- Creator fields: concrete descriptions and writing examples.
- Creator settings and preview: dynamic plain-language explanation of the actual public/private, visible/protected/invite-only and free/monthly combination.
- Buyer details: explains source or protected use, registration, monthly renewal and author approval before payment for invite-only work.
- Access management: permission does not waive a subscription fee; device-local expiry input is labelled accurately.

## Preserved behavior

All 39 curated works remain free. No private source, permission evidence or customer content is added to public pages. All server files and private source bytes are unchanged from the verified v3 ZIP. Author-set prices, USDT/TRC20 only and 80/20 remain unchanged. Code visibility does not silently grant an open-source license.

## Validation performed here

66 Node tests; 327 package/static checks; 23 existing browser assertions; 299 clarity checks including source/server preservation checks. Own-document browser tests stub every API. Japanese and English plus 320/390/1440 viewports were checked. No real email, account, payment, publication, native-platform permission or trading operation was performed. These tests do not prove that every newcomer understands the page; there has been no outside user study.

## Integration

Use public/trading/ only for public pages. private/ is not a publish directory. Integrate into the current complete authoritative site with its real authentication, storage, commerce and protected-delivery adapters. Update the homepage using integration/homepage-section.html. Preserve existing functions, headers, redirects, BSV-R02 and payment flows.

The source-free standalone preview is for review only. It cannot send mail, save a work or charge a customer. Current production rendering could not be retrieved through the web reader. No claim of production publication is made.
