#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import textwrap
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DATA = ROOT / "data"
MEDIA = ROOT / "media"
DIST = ROOT / "dist"
ASSETS = DIST / "assets"
OG = DIST / "og"

PLACEHOLDER_NAME = "placeholder.png"


def read_catalog() -> dict:
    with (DATA / "catalog.json").open("r", encoding="utf-8") as fh:
        catalog = json.load(fh)
    if "site" not in catalog or "items" not in catalog:
        raise SystemExit("catalog.json must contain 'site' and 'items'.")
    seen = set()
    for item in catalog["items"]:
        item_id = item.get("id")
        if not item_id:
            raise SystemExit("Every item needs a non-empty 'id'.")
        if item_id in seen:
            raise SystemExit(f"Duplicate item id: {item_id}")
        seen.add(item_id)
    return catalog


def ensure_clean_dist() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    OG.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (DIST / "data").mkdir(parents=True, exist_ok=True)
    (DIST / "item").mkdir(parents=True, exist_ok=True)
    (DIST / "checkout").mkdir(parents=True, exist_ok=True)
    (DIST / "about").mkdir(parents=True, exist_ok=True)


def copy_static_assets() -> None:
    shutil.copy2(SRC / "styles.css", ASSETS / "styles.css")
    shutil.copy2(SRC / "app.js", ASSETS / "app.js")
    shutil.copy2(DATA / "catalog.json", DIST / "data" / "catalog.json")
    if MEDIA.exists():
        shutil.copytree(MEDIA, DIST / "media", dirs_exist_ok=True)
    (DIST / ".nojekyll").write_text("", encoding="utf-8")


def slug(item_id: str) -> str:
    return item_id


def wrap_lines(text: str, width: int, max_lines: int = 3) -> list[str]:
    lines = textwrap.wrap(str(text), width=width) or [str(text)]
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1] + [lines[max_lines - 1][: max(0, width - 1)] + "…"]
    return lines


def money(value: float | int | str, site: dict) -> str:
    currency = site.get("currency", "USD")
    number = float(value or 0)
    if currency == "USD":
        return f"${number:,.2f}".replace(".00", "")
    return f"{currency} {number:,.2f}".replace(".00", "")


def run_convert(args: list[str]) -> None:
    subprocess.run(["convert", *args], check=True)


def create_placeholder_png(path: Path) -> None:
    run_convert(
        [
            "-size",
            "900x900",
            "gradient:#f7f8fa-#e4ebf1",
            "-fill",
            "#c7d2db",
            "-draw",
            "roundrectangle 80,80 820,820 46,46",
            "-fill",
            "#6b7c8c",
            "-font",
            "DejaVu-Sans-Bold",
            "-gravity",
            "center",
            "-pointsize",
            "54",
            "-annotate",
            "+0-16",
            "Add a product photo",
            "-font",
            "DejaVu-Sans",
            "-pointsize",
            "28",
            "-annotate",
            "+0+44",
            "Place image files in /media and rebuild",
            str(path),
        ]
    )


def create_favicon(path: Path) -> None:
    path.write_text(
        """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 120 120\">
  <defs>
    <linearGradient id=\"g\" x1=\"0%\" y1=\"0%\" x2=\"100%\" y2=\"100%\">
      <stop offset=\"0%\" stop-color=\"#0f7c5a\"/>
      <stop offset=\"100%\" stop-color=\"#1ea672\"/>
    </linearGradient>
  </defs>
  <rect width=\"120\" height=\"120\" rx=\"28\" fill=\"url(#g)\"/>
  <path d=\"M34 78V42h17c21 0 35 7 35 18 0 7-5 13-14 16l18 22H71L56 79h-6v19H34zm16-12h6c8 0 14-2 14-8 0-5-6-7-14-7h-6v15z\" fill=\"white\"/>
</svg>
""",
        encoding="utf-8",
    )


def create_poster_png(path: Path, site: dict, title: str, subtitle_lines: list[str], footer: str) -> None:
    args = [
        "-size",
        "1200x630",
        "gradient:#131a22-#243b55",
        "-fill",
        "#f3a847",
        "-draw",
        "rectangle 0,0 1200,96",
        "-fill",
        "#131a22",
        "-font",
        "DejaVu-Sans-Bold",
        "-gravity",
        "northwest",
        "-pointsize",
        "42",
        "-annotate",
        "+56+26",
        site.get("title", "Congo"),
    ]
    title_lines = wrap_lines(title, 22, max_lines=2)
    y = 156
    for line in title_lines:
        args.extend(
            [
                "-fill",
                "white",
                "-font",
                "DejaVu-Sans-Bold",
                "-pointsize",
                "68",
                "-annotate",
                f"+56+{y}",
                line,
            ]
        )
        y += 80
    for line in subtitle_lines:
        args.extend(
            [
                "-fill",
                "#dbe6ef",
                "-font",
                "DejaVu-Sans",
                "-pointsize",
                "32",
                "-annotate",
                f"+56+{y}",
                line,
            ]
        )
        y += 42
    args.extend(
        [
            "-fill",
            "#0c1118",
            "-draw",
            "roundrectangle 56,476 1144,570 28,28",
            "-fill",
            "#ffd68a",
            "-font",
            "DejaVu-Sans-Bold",
            "-pointsize",
            "34",
            "-annotate",
            "+86+492",
            footer,
            "-fill",
            "#f3f4f6",
            "-font",
            "DejaVu-Sans",
            "-pointsize",
            "26",
            "-annotate",
            "+86+544",
            site.get("sharingTagline", "Guess the price. Unlock the deal."),
            str(path),
        ]
    )
    run_convert(args)


def write_posters(catalog: dict) -> None:
    site = catalog["site"]
    create_poster_png(
        OG / "default.png",
        site,
        f"{site.get('title', 'Congo')} graduation sale",
        wrap_lines(site.get("defaultDescription", "Browse the sale and unlock deals."), 34, max_lines=2),
        site.get("sharingTagline", "Guess the price. Unlock the deal."),
    )
    for item in catalog["items"]:
        create_poster_png(
            OG / f"{slug(item['id'])}.png",
            site,
            item.get("name", "Untitled item"),
            wrap_lines(f"{item.get('category', 'Item')} · Guess high enough to unlock the checkout price", 34, max_lines=2),
            f"Reference: {money(item.get('referencePrice', 0), site)}",
        )


def rel_asset(path: str, rel_root: str) -> str:
    return rel_root + path.lstrip("/")


def topbar_html(rel_root: str, page: str, site: dict) -> str:
    def nav_link(href: str, label: str, icon: str, key: str) -> str:
        active = " active" if page == key else ""
        return f'<a class="nav-link{active}" href="{href}"><span>{icon}</span><span>{label}</span></a>'

    return f"""
    <header class=\"topbar\">
      <div class=\"topbar-inner\">
        <a class=\"brand-lockup\" href=\"{rel_root}\">
          <span class=\"brand-mark\">CO</span>
          <span class=\"brand-copy\">
            <strong>{escape(site.get('title', 'Congo'))}</strong>
            <span>Graduation sale · price guessing</span>
          </span>
        </a>
        <div class=\"search-shell\">
          <input id=\"global-search\" type=\"search\" placeholder=\"Search furniture, monitors, supplies...\" />
          <button id=\"global-search-button\" type=\"button\" aria-label=\"Search\">⌕</button>
        </div>
        <nav class=\"primary-links\" aria-label=\"Primary\">
          {nav_link(rel_root, 'Home', '⌂', 'index')}
          {nav_link(rel_root + 'about/', 'About', 'ℹ', 'about')}
        </nav>
        <a class=\"cart-link\" href=\"{rel_root}checkout/\">
          <div>
            <strong>Cart</strong>
            <span><span data-cart-count>0</span> unlocked item(s)</span>
          </div>
        </a>
      </div>
      <div class=\"nav-secondary\">
        <div class=\"nav-secondary-inner\" id=\"category-chips\"></div>
      </div>
    </header>
    """


def mobile_footer_html(rel_root: str, page: str) -> str:
    def tab(href: str, label: str, icon: str, key: str) -> str:
        active = " active" if page == key else ""
        return f'''<a class="mobile-tab{active}" href="{href}"><span class="mobile-tab-icon">{icon}</span><span class="mobile-tab-label">{label}</span></a>'''

    return f"""
    <nav class=\"mobile-footer-nav\" aria-label=\"Mobile footer\">
      <div class=\"mobile-footer-nav-inner\">
        {tab(rel_root, 'Home', '⌂', 'index')}
        {tab(rel_root + 'checkout/', 'Cart', '🛒', 'checkout')}
        {tab(rel_root + 'about/', 'About', 'ℹ', 'about')}
      </div>
    </nav>
    """


def html_shell(*, title: str, description: str, canonical: str, image_url: str, body: str, rel_root: str, page: str, site: dict, extra_script: str = "") -> str:
    site_title = escape(site.get("title", "Congo"))
    payload = json.dumps(site, ensure_ascii=False)
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{escape(title)}</title>
    <meta name=\"description\" content=\"{escape(description)}\" />
    <meta property=\"og:type\" content=\"website\" />
    <meta property=\"og:title\" content=\"{escape(title)}\" />
    <meta property=\"og:description\" content=\"{escape(description)}\" />
    <meta property=\"og:url\" content=\"{escape(canonical)}\" />
    <meta property=\"og:image\" content=\"{escape(image_url)}\" />
    <meta property=\"og:site_name\" content=\"{site_title}\" />
    <meta name=\"twitter:card\" content=\"summary_large_image\" />
    <meta name=\"twitter:title\" content=\"{escape(title)}\" />
    <meta name=\"twitter:description\" content=\"{escape(description)}\" />
    <meta name=\"twitter:image\" content=\"{escape(image_url)}\" />
    <link rel=\"canonical\" href=\"{escape(canonical)}\" />
    <link rel=\"icon\" href=\"{rel_root}assets/favicon.svg\" type=\"image/svg+xml\" />
    <link rel=\"stylesheet\" href=\"{rel_root}assets/styles.css\" />
  </head>
  <body data-page=\"{page}\" class=\"has-mobile-footer\">
    {topbar_html(rel_root, page, site)}
    {body}
    <footer class=\"footer\">
      <div class=\"footer-inner\">
        <div><strong>{site_title}</strong> · {escape(site.get('subtitle', ''))}</div>
        <div>{escape(site.get('deliveryNote', ''))}</div>
        <div>Update items in <code>data/catalog.json</code>, add photos to <code>/media</code>, then push to redeploy.</div>
      </div>
    </footer>
    {mobile_footer_html(rel_root, page)}
    <script>window.CONGO_REL_ROOT = {json.dumps(rel_root)}; window.CONGO_SITE = {payload}; {extra_script}</script>
    <script src=\"{rel_root}assets/app.js\"></script>
  </body>
</html>
"""


def index_body(site: dict) -> str:
    return f"""
    <main class=\"section\">
      <div class=\"section-header\">
        <div>
          <h1>Available items</h1>
          <p>Furniture, computer supplies, and anything else that needs a new home before graduation.</p>
        </div>
      </div>
      <div id=\"page-error\" class=\"status-box bad hide\"></div>
      <div id=\"catalog-grid\" class=\"catalog-grid\"></div>
    </main>
    """


def item_body(site: dict, item: dict) -> str:
    category = escape(item.get("category", "Item"))
    condition = escape(item.get("condition", "Used"))
    reference_link = escape(item.get("referenceLink", "#"))
    reference_price = escape(money(item.get("referencePrice", 0), site))
    description = escape(item.get("description", ""))
    pickup_notes = escape(item.get("pickupNotes", ""))
    image = escape(rel_asset(item.get("image", f"assets/{PLACEHOLDER_NAME}"), "../../"))
    quantity = int(item.get("quantity", 1))
    raw_status = str(item.get("status", "available"))
    status = escape(raw_status)
    earliest_pickup = escape(item.get("earliestPickupDate", ""))
    latest_pickup = escape(item.get("latestPickupDate", ""))
    latest_pickup_line = f'<li><span class=\"spec-label\">Latest pickup</span><span>{latest_pickup}</span></li>' if latest_pickup else ''
    return f"""
    <main class=\"item-page\">
      <section class=\"panel media-panel\">
        <div class=\"media-frame\">
          <img src=\"{image}\" alt=\"{escape(item.get('name', 'Item image'))}\" onerror=\"this.src='../../assets/{PLACEHOLDER_NAME}'\" />
        </div>
      </section>
      <section class=\"item-meta\">
        <div class=\"panel detail-panel\">
          <div class=\"badge-row\" style=\"position:static;justify-content:flex-start;margin-bottom:10px\">
            <span class=\"badge gold\">{category}</span>
            <span class=\"badge\">{condition}</span>
            <span class=\"badge {'green' if raw_status == 'available' else ''}\">{status}</span>
          </div>
          <h1>{escape(item.get('name', 'Untitled item'))}</h1>
          <p class=\"muted\">{description}</p>
          <ul class=\"spec-list\">
            <li><span class=\"spec-label\">Reference price</span><span><a class=\"reference-link\" href=\"{reference_link}\" target=\"_blank\" rel=\"noreferrer\">{reference_price}</a></span></li>
            <li><span class=\"spec-label\">Quantity</span><span>{quantity}</span></li>
            <li><span class=\"spec-label\">Earliest pickup</span><span>{earliest_pickup or 'Available now'}</span></li>
            {latest_pickup_line}
            <li><span class=\"spec-label\">Pickup note</span><span>{pickup_notes or 'Will coordinate after checkout.'}</span></li>
          </ul>
        </div>
        <div class=\"panel guess-panel\">
          <h2 class=\"block-title\">Unlock the checkout price</h2>
          <p class=\"muted\">Enter your offer to reveal the checkout price.</p>
          <div class=\"guess-box\">
            <div class=\"status-box info\" id=\"guess-status\">Offers left: <strong id=\"remaining-guesses\">3</strong></div>
            <div class=\"guess-input-row\">
              <input id=\"guess-input\" type=\"number\" min=\"0\" step=\"0.01\" placeholder=\"Enter your guess in dollars\" />
              <button id=\"guess-button\" class=\"btn-amazon\">Guess</button>
            </div>
            <div class=\"small-note\" id=\"hidden-price-hint\">The checkout price is still hidden.</div>
            <div class=\"reveal-price hide\" id=\"reveal-price\">Unlocked checkout price: <span data-offer-price></span></div>
            <div class=\"inline-actions hide\" id=\"unlock-actions\">
              <button id=\"add-to-cart\" class=\"btn-amazon\">Add to cart</button>
              <button id=\"buy-now\" class=\"btn-secondary\">Checkout now</button>
            </div>
          </div>
        </div>
      </section>
    </main>
    """


def checkout_body(site: dict) -> str:
    threshold = escape(money(site.get("freeDeliveryThreshold", 0), site))
    contact_email = escape(site.get("contactEmail", "your-email@example.com"))
    return f"""
    <main class=\"checkout-page\">
      <section class=\"cart-panel panel\">
        <div class=\"section-header\" style=\"margin-bottom:18px\">
          <div>
            <h1>Checkout</h1>
            <p>Unlock items first, then use this page to compose the pickup or delivery email.</p>
          </div>
          <button id=\"clear-cart\" class=\"btn-ghost\">Clear cart</button>
        </div>
        <div id=\"page-error\" class=\"status-box bad hide\"></div>
        <div id=\"cart-list\" class=\"cart-list\"></div>
      </section>
      <aside class=\"summary-card checkout-card\">
        <h2 class=\"block-title\">Order summary</h2>
        <div class=\"checkout-summary-rows\" style=\"margin:16px 0\">
          <div class=\"checkout-summary-row\"><span>Items</span><strong id=\"summary-count\">0</strong></div>
          <div class=\"checkout-summary-row\"><span>Total</span><strong id=\"summary-total\">$0</strong></div>
        </div>
        <div class=\"progress\"><span id=\"delivery-progress\" style=\"width:0%\"></span></div>
        <div id=\"delivery-message\" class=\"status-box info\" style=\"margin-top:12px\">Spend {threshold} to unlock free local delivery.</div>
        <p class=\"small-note\">Checkout email will be addressed to <strong>{contact_email}</strong>.</p>
        <form id=\"checkout-form\" class=\"checkout-form\">
          <div class=\"form-grid\">
            <input name=\"name\" placeholder=\"Your name\" />
            <input name=\"email\" type=\"email\" placeholder=\"Your email\" />
            <input name=\"phone\" placeholder=\"Phone / Telegram / Signal\" />
            <input name=\"when\" placeholder=\"Preferred time\" />
          </div>
          <select name=\"deliveryMode\">
            <option>Pickup</option>
            <option>Local delivery</option>
            <option>Either works</option>
          </select>
          <input name=\"address\" placeholder=\"Pickup point or delivery area\" />
          <textarea name=\"notes\" placeholder=\"Any schedule details, questions, or bundle offers\"></textarea>
          <div class=\"inline-actions\">
            <button type=\"button\" id=\"copy-email\" class=\"btn-amazon\">Copy email text</button>
            <a id=\"open-mailto\" class=\"btn-secondary\" href=\"mailto:{contact_email}\">Open email draft</a>
          </div>
        </form>
      </aside>
    </main>
    """


def about_body(site: dict) -> str:
    return f"""
    <main class=\"section\">
      <div class=\"about-stack\">
        <section class=\"about-panel panel\">
          <h1 class=\"block-title\">Guess the price. Unlock the deal.</h1>
          <p class=\"muted\">Congo is a graduation-sale storefront for local pickup and delivery. The front page stays focused on browsing goods; this page explains the shopping mechanic.</p>
        </section>
        <section class=\"about-panel panel\">
          <h2 class=\"block-title\">How it works</h2>
          <ul class=\"about-list\">
            <li>Each product page starts with a hidden seller checkout price.</li>
            <li>You can make up to 3 offers per item from the same browser.</li>
            <li>If your offer is too low, the site asks you to try again.</li>
            <li>If your offer succeeds, the site unlocks a checkout price and lets you add the item to cart.</li>
            <li>Unlocked items can be bundled for pickup or local delivery.</li>
            <li>Orders above {escape(money(site.get('freeDeliveryThreshold', 0), site))} qualify for free local delivery.</li>
            <li>The final checkout page prepares a ready-to-send email to <strong>{escape(site.get('contactEmail', ''))}</strong> for scheduling.</li>
          </ul>
        </section>
      </div>
    </main>
    """


def write_pages(catalog: dict) -> None:
    site = catalog["site"]
    base_url = site.get("baseUrl", "").rstrip("/")
    default_title = f"{site.get('title', 'Congo')} · Graduation sale"
    default_description = site.get("defaultDescription", "Graduation sale catalog.")
    default_image = f"{base_url}/og/default.png"

    (DIST / "index.html").write_text(
        html_shell(
            title=default_title,
            description=default_description,
            canonical=f"{base_url}/",
            image_url=default_image,
            body=index_body(site),
            rel_root="./",
            page="index",
            site=site,
        ),
        encoding="utf-8",
    )

    (DIST / "checkout" / "index.html").write_text(
        html_shell(
            title=f"Checkout · {site.get('title', 'Congo')}",
            description=f"Compose your pickup or delivery email for the {site.get('title', 'Congo')} graduation sale.",
            canonical=f"{base_url}/checkout/",
            image_url=default_image,
            body=checkout_body(site),
            rel_root="../",
            page="checkout",
            site=site,
        ),
        encoding="utf-8",
    )

    (DIST / "about" / "index.html").write_text(
        html_shell(
            title=f"About · {site.get('title', 'Congo')}",
            description="How the Congo graduation-sale guessing mechanic works.",
            canonical=f"{base_url}/about/",
            image_url=default_image,
            body=about_body(site),
            rel_root="../",
            page="about",
            site=site,
        ),
        encoding="utf-8",
    )

    for item in catalog["items"]:
        item_slug = slug(item["id"])
        item_dir = DIST / "item" / item_slug
        item_dir.mkdir(parents=True, exist_ok=True)
        og_image = f"{base_url}/og/{item_slug}.png"
        description = f"{item.get('category', 'Item')} — reference price {money(item.get('referencePrice', 0), site)}. Guess high enough to unlock the checkout price."
        extra_script = f"window.CONGO_CURRENT_ITEM = {json.dumps(item, ensure_ascii=False)};"
        (item_dir / "index.html").write_text(
            html_shell(
                title=f"{item.get('name', 'Item')} · {site.get('title', 'Congo')}",
                description=description,
                canonical=f"{base_url}/item/{item_slug}/",
                image_url=og_image,
                body=item_body(site, item),
                rel_root="../../",
                page="item",
                site=site,
                extra_script=extra_script,
            ),
            encoding="utf-8",
        )


def write_support_assets() -> None:
    create_favicon(ASSETS / "favicon.svg")
    create_placeholder_png(ASSETS / PLACEHOLDER_NAME)


def main() -> None:
    catalog = read_catalog()
    ensure_clean_dist()
    copy_static_assets()
    write_support_assets()
    write_posters(catalog)
    write_pages(catalog)
    print(f"Built Congo site into {DIST}")


if __name__ == "__main__":
    main()
