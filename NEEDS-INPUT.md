# NEEDS-INPUT

Each line lists what's needed, why it's needed, the audit findings it blocks, and the files it touches. Nothing on this list has been guessed or filled with placeholder text on the site. Once a value is supplied, add it to `site.config.json` (unless the line says otherwise) and run `./build.sh check`.

## Deployment and indexing
- **D0 Production go-live.** Needed: written confirmation from the owner to set `deployment_mode` to `production` and to point www.eatfit.in at this site (DNS stays the owner's call). Why: the review copy carries noindex on purpose. Blocks: [51,56]. Files: `site.config.json`.
- **D1 Crawler policy choice.** Needed: the owner picks `allow-all`, `retrieval-only` or `block-training`. Why: it's a business decision; the default keeps today's allow-all behaviour. Blocks: [69]. Files: `site.config.json`, `robots.txt`.
- **D2 robots.txt location.** Needed: nothing until go-live. Why: crawlers only read robots.txt at the host root, so the copy at abhilashbishtwork.github.io/eatfit/robots.txt is ignored. It takes effect once the site is served from the root of www.eatfit.in. Blocks: [55,69]. Files: none.

## Brand facts (VERIFY; current site text left unchanged)
- **B1 City count.** Needed: the confirmed list of EatFit cities. The site says 8; curefoods.in lists 9. Why: conflicting sources. Blocks: [35]. Files: `site.config.json` `cities[]`, which feeds the home page, FAQ, order page, llms.txt and the Restaurant `areaServed`.
- **B2 Hashtag.** Needed: confirm #HealthyMadeHappier (site) or #BodySaysThanks (recent Instagram bio). Blocks: [33,34,38]. Files: `site.config.json` `brand.hashtag`.
- **B3 Tagline.** Needed: confirm whether the official tagline "Not just a meal - It's a Bowl" should replace the site's own line. Blocks: [33,34,38]. Files: `site.config.json` `brand.tagline`.
- **B4 Sub-brand portfolio and logos.** Needed: the confirmed portfolio (the site shows 5; the official announcement lists 8) and official logo files for every brand in it. Why: the current logos were cropped from a single combined image. Blocks: [36,39]. Files: `site.config.json` `brand.sub_brands`, `assets/img/brand-*.png`.
- **B5 Other official profiles.** Needed: the official Facebook, LinkedIn, X and YouTube URLs, if they exist. Why: Organization `sameAs` currently lists only the verified Instagram. Blocks: [61]. Files: `site.config.json` `brand.same_as_verified`.
- **B6 Restaurant schema address.** Needed: confirm whether the Curefoods head-office address (Roopena Agrahara, Bengaluru) is the right address for the EatFit Restaurant schema and footer, or supply the correct one. Why: it's a corporate address, not a kitchen. Blocks: [77]. Files: `site.config.json` `brand.address_lines`, `build/generate.py` `restaurant_ld()`.

## Ordering
- **O0 Order page removed (owner, 25 Oct 2026).** Every Order button now uses the owner-supplied brand links in `site.config.json` `order_links`. On desktop web, Swiggy direct lands on swiggy.com and the Zomato onelink lands on zomato.com, because both target the apps. Needed: the newer Zomato link the owner said they would share, and ideally web-friendly brand links. The verified per-city links stay in `cities[]` and are listed in llms.txt. Blocks: [1,2,4,26]. Files: `site.config.json`.
- **O1 Ownly links.** Needed: a per-city EatFit Ownly URL that works on the web, if one exists. Why: Ownly has no web ordering. The owner-supplied link (ownly.food/app/brand/BR112474) shows an "Open in Ownly" screen on mobile web and Ownly's generic Hyderabad page on desktop (tested 25 Oct 2026). It's labelled "Ownly app" on the site. Blocks: [3,5,26,98]. Files: `site.config.json` `cities[].order.ownly`.
- **O2 Ownly cities.** Needed: confirm which cities EatFit is live in on Ownly. The site shows Ownly for Bengaluru, Hyderabad and Delhi NCR, based on Ownly's own city list and recent EatFit Ownly orders. A handful of Mumbai and Pune Ownly orders also appear in the data. Blocks: [5,26]. Files: `site.config.json`.
- **O3 Swiggy for Chandigarh and Coimbatore.** Needed: the EatFit Swiggy URLs for these two cities. Why: swiggy.com/city/chandigarh/eatfit and /coimbatore/eatfit both land on the Swiggy homepage, so those cities currently show Zomato only. Blocks: [1,26]. Files: `site.config.json`.
- **O4 Platform logos.** Needed: official Swiggy, Zomato and Ownly logo assets and confirmation that brand guidelines permit using them on order buttons. Why: I couldn't verify the guidelines, so the buttons are text-only. Blocks: [32]. Files: `assets/img/`, `build/generate.py`.
- **O5 Deep-link tracking.** Needed: a decision on UTM tagging. Why: none was added. The city URLs are plain web pages and the old Zomato onelink is no longer used. Any parameter must be re-tested before shipping. Blocks: [98]. Files: `site.config.json`.

## Menu data
- **M1 Verified menu.** Needed: the kitchen's current menu as the source of truth. Why: the menu is built from 7 days of sales data (16-22 Oct 2026). That reflects what's selling, but the kitchen hasn't signed it off. Blocks: [41]. Files: `build/menu_live.tsv`, then `menu.last_changed`.
- **M2 Dish descriptions.** Needed: verified ingredients or a one-line description for each of the 98 dishes. Why: none were written, because I don't invent ingredients from dish names. Blocks: [16,24,72]. Files: `site.config.json` `menu.dish_details`.
- **M3 Nutrition and price.** Needed: kcal, protein (g) and price per dish, with source and date. Why: the slots render only once real values exist. Prices vary by city and app, so decide which price to show. Blocks: [6,7,8,60,62]. Files: `site.config.json` `menu.dish_details`.
- **M4 Allergens and disclaimer.** Needed: verified allergen and dietary data per dish, plus disclaimer copy reviewed by legal. These ship together with the nutrition values. Blocks: [50,80]. Files: `build/generate.py`.
- **M5 Diet attributes.** Needed: verified Jain, high-protein and gluten-free flags per dish. Why: only the veg/non-veg filter ships. The veg flag comes from dish-name keywords (chicken, egg, mutton, fish, meatball, carne), so ask the kitchen to confirm it. Blocks: [12,82]. Files: `build/generate.py` `NON_VEG`, `site.config.json`.
- **M6 Papacream story.** Needed: approved facts about the Papacream partnership. Why: the ice cream section is unchanged until then. Blocks: [49]. Files: `site.config.json` `menu.papacream_facts`.

## Photos
- **P1 Dish photography.** Needed: real kitchen photos for:
  - Dal Makhani Chawal, Black Chana with Steamed Rice and Desi Dal Tadka Chawal, which are near-identical (same plate, angle and garnish)
  - Lasooni Methi Paneer with Steam Rice, which uses the same set-up as those three
  - Classic Rajma Chawal, the #1 seller, which has no photo yet

  Each flagged image has an HTML comment in index.html. No replacement images were generated. Blocks: [28,40]. Files: `assets/img/dish-*.jpg`.

## Health and quality claims (on the site already; not repeated anywhere new)
- **H1 ISO certification.** Needed: certificate standard, number and issuing body. Blocks: [47,48,81]. Files: `build/generate.py` `PHILOSOPHY`, `build/posts.py`.
- **H2 Farm-to-fork tracking.** Needed: what is tracked and how. Blocks: [47,48,81].
- **H3 Nutritionist approved.** Needed: who approves the dishes and their credential. Blocks: [47,48,81].
- **H4 Zero trans fat, zero chemicals, no preservatives, no deep frying.** Needed: confirmation from the kitchen or quality team. Blocks: [47,48,81]. Files: hero copy, menu intro, FAQ, `PHILOSOPHY`, posts.
- **H5 Calorie-counted, with nutrition shown in the apps.** Needed: confirm that every dish is calorie-counted and that the apps show nutrition details (FAQ answer). Blocks: [47,81].

## Trust, contact and legal
- **T1 Ratings.** Needed: average rating, ratings count, source platform and as-of date. Why: the trust strip is built but stays hidden until then. Blocks: [42]. Files: `site.config.json` `trust`.
- **T2 Press.** Needed: press mentions, each with title, outlet, URL and date. Blocks: [43]. Files: `site.config.json` `trust.press`.
- **C1 Contact.** Needed: a monitored support email and phone number, plus the FSSAI licence number. Why: the footer slots stay hidden until supplied. Blocks: [31,75,79,83]. Files: `site.config.json` `contact`.
- **L1 Legal pages.** Needed: reviewed privacy, terms and refund copy. Blocks: [78].

## Content
- **F1 New FAQs.** Needed: verified answers on calories, Jain options, gluten-free options and protein. Why: each answer must be direct, with careful non-medical wording on anything weight-related. Blocks: [74]. Files: `build/generate.py` `FAQ`.
- **W1 Blog depth.** Needed: substantiated detail (recipes, sourcing, nutrition facts) to expand posts. Why: posts were not padded. Blocks: [44,66]. Files: `build/posts.py`.
- **W2 Named author.** Needed: a named author with a short bio, if the owner wants one. Why: posts are credited to "Team EatFit" as an Organization. Blocks: [64]. Files: `build/generate.py` `author_ld()`.
- **W3 Ambassador, founding story and certifications.** Needed: confirmed and current facts before any of this content is written. Blocks: [37,46,47,48].
- **W4 City landing pages.** Needed: genuinely city-specific content. Why: thin near-duplicate city pages would be doorway pages. Blocks: [65,93].
- **W5 "New this month" slot.** Needed: a named owner to keep it current. Blocks: [97].
- **W6 Macro calculator / build-your-bowl.** Needed: verified nutrition data (M3). Blocks: [94].

## Future work (no data collection in this pass)
- **X1 Analytics and Search Console.** Needed: the chosen tools, a stated purpose and an approved consent approach. Blocks: [57,67].
- **X2 Newsletter, WhatsApp opt-in, corporate/bulk enquiries.** Needed: real endpoints, a stated purpose and a privacy notice. Blocks: [84,95,96].
- **X3 Off-site entity work.** Needed: the owner to set up a Wikidata entry, a Google Business Profile and third-party listicle citations. These sit outside this repo. Blocks: [73,76].

## Process
- **Q1 Quarterly content review.** Needed: a named owner who reviews the menu, claims, links and this file every quarter. Blocks: [100].
