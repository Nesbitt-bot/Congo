# Congo

A static GitHub Pages graduation-sale site with a price-guessing mechanic.

The name is a joke on Amazon: Congo is the second-largest rainforest, but this repo is for selling furniture and computer supplies before graduation.

## What it does

- Reads all sale data from `data/catalog.json`
- Expects item photos under `/media`
- Renders a mobile-friendly and desktop-friendly storefront with an Amazon-inspired layout
- Keeps the front page focused on browsing goods
- Gives each visitor **3 chances per item** to guess a price high enough to unlock a checkout deal
- If the guess is above the hidden seller price, computes the checkout price with the configured discount factor
- Lets unlocked items be added to a local cart
- Unlocks **free local delivery** when the total is above the configured threshold
- Builds a checkout page that composes a ready-to-send email for pickup or delivery scheduling
- Generates Open Graph / Twitter preview images for the main store and every item page
- Deploys automatically to **GitHub Pages via Actions** on push to `main`

## Data model

Edit `data/catalog.json`.

```json
{
  "site": {
    "title": "Congo",
    "contactEmail": "me@example.com",
    "freeDeliveryThreshold": 50,
    "discountFactor": 0.8,
    "baseUrl": "https://nesbitt-bot.github.io/Congo"
  },
  "items": [
    {
      "id": "sample-item",
      "name": "Sample Item",
      "category": "Computer Supplies",
      "referencePrice": 100,
      "referenceLink": "https://example.com",
      "actualPrice": 55,
      "image": "media/sample-item.jpg",
      "status": "available"
    }
  ]
}
```

Important fields:

- `id`: stable slug used in the URL
- `referencePrice`: visible comparison price
- `actualPrice`: hidden seller price threshold for success
- `discountFactor`: stored under `site`, used when the successful guess is above `actualPrice`
- `earliestPickupDate`: earliest day the item can be picked up
- `latestPickupDate`: optional latest day for pickup; hidden when omitted
- `image`: primary image path relative to repo root, usually `media/<filename>`
- `images`: optional array of gallery image paths; first image is used as the card/cover image when present
- `status`: `available` or anything else to mark it unavailable / not ready

## Pricing rule

If the user guesses successfully:

- if `guess == actualPrice`, checkout price = `actualPrice`
- if `guess > actualPrice`, checkout price = `actualPrice + (guess - actualPrice) * discountFactor`

Default `discountFactor` is `0.8`.

## Local workflow

1. Put photos in `/media`
2. Update `data/catalog.json`
3. Build locally:

```bash
python3 scripts/build_site.py
```

4. Preview the generated site from `/dist`
5. Commit and push to `main`

## Deployment

GitHub Actions builds the site and deploys it to Pages automatically.

If Pages is not already enabled for the repo, set it to **GitHub Actions** in the repository settings.

## Agent instructions

See `agent.md` for maintenance, upload, redeploy, and template-user instructions.

## Notes

- Guess state and cart state are stored in the browser via `localStorage`
- This is a static site; there is no backend, no real payment processing, and no inventory locking across users
- Social previews come from generated item pages and poster images in `/dist/og`
