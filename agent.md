# agent.md

Instructions for agents working on the Congo repository.

Congo is a static GitHub Pages graduation-sale site with a browsing-first storefront and a per-item price-guessing mechanic.

## Core behavior

- All product and site data live in `data/catalog.json`
- Product images live in `media/`
- The site is built into `dist/` by `scripts/build_site.py`
- Deployment is automatic through `.github/workflows/pages.yml`
- Pushing to `main` should rebuild and redeploy the site on GitHub Pages
- The generator now exports multilingual storefronts for English and Chinese (`/en/` and `/zh/`) and creates language-specific posters with QR codes

## Current pricing rule

For a successful guess:

- if `guess == actualPrice`, checkout price = `actualPrice`
- if `guess > actualPrice`, checkout price = `actualPrice + (guess - actualPrice) * discountFactor`
- default `discountFactor` is stored in `data/catalog.json` under `site.discountFactor`

## For developers

### Files that matter most

- `data/catalog.json` — source of truth for site and item data
- `media/` — product images
- `src/app.js` — client behavior, guessing, cart, checkout email flow
- `src/styles.css` — layout and styling
- `scripts/build_site.py` — static-page and share-poster generator
- `.github/workflows/pages.yml` — Pages build/deploy pipeline

### Safe workflow

1. Edit source files
2. Rebuild locally:

```bash
python3 scripts/build_site.py
```

3. Validate quickly:

```bash
python3 -m py_compile scripts/build_site.py
node --check src/app.js
```

4. Review generated `dist/`
5. Commit
6. Push to `main`
7. Confirm the GitHub Actions Pages workflow succeeds

### Development rules

- Keep the site static; do not add a backend unless explicitly requested
- Preserve GitHub Pages compatibility
- Keep card browsing lightweight and mobile-friendly
- Keep social sharing metadata working for the storefront and individual item pages
- If changing the pricing mechanic, update:
  - `src/app.js`
  - `scripts/build_site.py`
  - this file
  - `README.md` if public behavior changes

## For site-template users

### How to add or update products

1. Put the product photo in `media/`
2. Add or edit an item in `data/catalog.json`
3. Rebuild:

```bash
python3 scripts/build_site.py
```

4. Commit and push to `main`
5. Wait for GitHub Actions to redeploy the site

### Required item fields

Each item should have:

- `id`
- `name`
- `category`
- `condition`
- `referencePrice`
- `referenceLink`
- `actualPrice`
- `quantity`
- `status`
- `earliestPickupDate`
- optional `latestPickupDate`
- `image`
- optional `images` array for gallery photos
- `description`
- `pickupNotes`

If the hidden seller price is not ready yet, set:

- `actualPrice`: `null`
- `status`: `pending`

That keeps the item visible without enabling guessing.

### If the user did not provide a reference price or link

The agent should:

1. Identify the item from the photo or description
2. Search online for a similar current product listing
3. Use a reasonable latest reference price
4. Store the source URL in `referenceLink`
5. Mention in the commit summary or user update that the reference was estimated from a similar live listing

Do not invent a fake premium price when the item is easy to identify.

### Photo handling

- Rename uploaded files to clean product slugs when possible
- Keep image filenames stable after they are referenced in `catalog.json`
- Prefer `.jpg`, `.jpeg`, `.png`, or `.webp`

## Continuing development

Good next improvements if requested:

- bundle discounts
- sold/reserved badges and filters
- multi-photo item galleries
- share buttons per item
- optional CSV → JSON importer
- localStorage migration helpers when data shape changes

## Deployment note

The repo is configured for static GitHub Pages via Actions. The normal rule is:

- edit source/data/media
- push to `main`
- let Actions build and deploy

Do not hand-edit `dist/` as the source of truth.
