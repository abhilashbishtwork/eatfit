# EatFit website

This is a static site (plain HTML, one CSS file, a little vanilla JS) for EatFit, Curefoods' healthy-food delivery brand.

## The two commands

```sh
./build.sh          # build every page, image variant and SEO file from site.config.json
./build.sh check    # build, then verify against a local server that mirrors the canonical base
```

`check` does the following:
- Requests every URL in sitemap.xml, robots.txt and llms*.txt, plus every internal link and asset.
- Confirms og:image is 800x800 (square, so WhatsApp shows a compact preview).
- Confirms the robots meta matches the mode.
- Parses all JSON-LD.
- Scans for placeholder text.
- Confirms every order button goes to a configured platform link.
- Builds a throwaway copy in the other mode and confirms the flip.

## Where things live

| What | Where |
|---|---|
| Mode, canonical base, crawler policy, cities and order links, brand facts, contact/trust slots, menu date, dish details | `site.config.json` |
| Page templates and copy | `build/generate.py` |
| Blog posts | `build/posts.py` |
| Menu data (category, dish, units sold) | `build/menu_live.tsv` |
| WebP copies, share image, favicon | `build/images.py` (run by build.sh) |
| Open data questions | `NEEDS-INPUT.md` |

The built output (`*.html`, `assets/style.css`, `assets/site.js`, `robots.txt`, `sitemap.xml`, `llms.txt`, `llms-full.txt`, `favicon.ico`) is committed alongside the sources. Don't edit the built files by hand.

## Deployment modes

`deployment_mode` in `site.config.json` picks the canonical base from `canonical_base`:

- `review` (default): the canonical base is the review URL, and every page carries `<meta name="robots" content="noindex,nofollow">`. That is a strong signal to keep the review copy out of search, but it isn't a guarantee; engines act on it when they recrawl.
- `production`: the canonical base is https://www.eatfit.in and pages are indexable. The 404 page is always noindex.

Changing that one value and running `./build.sh` restamps canonicals, og:url and og:image, the JSON-LD URLs, sitemap.xml, robots.txt and llms*.txt. Only switch to production with the owner's written go-ahead. Pointing www.eatfit.in at this site (DNS, hosting) is a separate step for the owner.

## AI crawler policy

`robots_ai_policy` controls the two commented groups in robots.txt:

- `allow-all` (default, same as before): retrieval and training crawlers are both allowed.
- `retrieval-only`: retrieval/search crawlers (OAI-SearchBot, ChatGPT-User, PerplexityBot, Perplexity-User, Claude-SearchBot, Claude-User, DuckAssistBot, MistralAI-User) are explicitly allowed. Training crawlers (GPTBot, ClaudeBot, anthropic-ai, Google-Extended, Applebot-Extended, CCBot, Meta-ExternalAgent, Amazonbot) are disallowed.
- `block-training`: training crawlers are disallowed. Retrieval crawlers get no group of their own and fall under `User-agent: *`. In practice this crawls the same way as `retrieval-only`; the only difference is that retrieval bots aren't named.

These rules express permission only. They don't cause indexing or citation, and they only take effect when robots.txt is served from the host root. On the review URL it sits under /eatfit/, where crawlers don't read it.

## Order links

The order page (`order.html`) lists each city with buttons that link directly to EatFit on that platform. Per-city URLs live in `site.config.json` under `cities[].order`. A `null` value means no verified link, so no button is shown. The links were tested on 25 Oct 2026 on desktop web and mobile web (iPhone emulation). Re-test any new or changed link before shipping, and don't add tracking parameters to app deep links without re-testing.

## Data rules

Never add a price, nutrition number, rating, claim, contact detail or dish description without a verified source. Leave the field `null` and add a line to NEEDS-INPUT.md instead.
