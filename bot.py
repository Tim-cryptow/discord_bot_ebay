import os
os.environ["DISCORD_NO_VOICE"] = "1"

import asyncio
import logging
import sys

import discord
from discord.ext import commands  # type: ignore
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("discord_bot_ebay")

TOKEN = os.getenv("DISCORD_TOKEN")

EBAY_SEARCH_URL = "https://www.ebay.com/sch/i.html"
MAX_RESULTS = 3

# Headers that mimic a real browser. eBay serves 403/challenge pages to requests
# that look automated, so a complete and consistent header set matters.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.ebay.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# eBay serves two search-result layouts. Newer pages use the ".s-card" structure,
# older pages use ".s-item". Detect whichever is present and parse accordingly.
RESULT_LAYOUTS = (
    {
        "container": "li.s-card, .s-card",
        "title": ".s-card__title",
        "price": ".s-card__price",
    },
    {
        "container": "li.s-item, .s-item",
        "title": ".s-item__title",
        "price": ".s-item__price",
    },
)

# Text that indicates eBay returned an anti-bot interstitial instead of results.
BLOCK_MARKERS = (
    "pardon our interruption",
    "checking your browser",
    "captcha",
    "please verify yourself",
)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def _build_session():
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    return session


def _looks_blocked(html):
    lowered = html.lower()
    return any(marker in lowered for marker in BLOCK_MARKERS)


def _extract_card_image(card):
    """Returns a usable image URL from a search-result card, or None."""
    for img in card.select("img"):
        for attr in ("src", "data-src", "data-img-src"):
            value = img.get(attr)
            if value and value.startswith("http"):
                return value
    return None


def get_high_res_image(session, item_url):
    """Fallback: fetch the item page and read its og:image meta tag."""
    try:
        response = session.get(item_url, timeout=10)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]
    except requests.RequestException as exc:
        logger.warning("Failed to fetch high-res image from %s: %s", item_url, exc)
    return None


def _parse_layout(soup, layout):
    """Extracts sold items from the soup using one layout's selectors."""
    items = []
    for card in soup.select(layout["container"]):
        title_tag = card.select_one(layout["title"])
        price_tag = card.select_one(layout["price"])
        link_tag = card.select_one('a[href*="/itm/"]')
        if not (title_tag and price_tag and link_tag):
            continue

        title = title_tag.get_text(strip=True)
        price = price_tag.get_text(strip=True)
        link = link_tag["href"].split("?")[0]

        # Skip eBay's placeholder/header card and anything without a real listing link.
        if not title or title.lower() == "shop on ebay":
            continue
        if "/itm/" not in link:
            continue

        items.append({
            "title": title,
            "price": price,
            "link": link,
            "image": _extract_card_image(card),
        })
        if len(items) >= MAX_RESULTS:
            break
    return items


def parse_search_html(html):
    """Extracts sold listings from eBay search HTML using whichever layout is present."""
    soup = BeautifulSoup(html, "html.parser")
    for layout in RESULT_LAYOUTS:
        if not soup.select_one(layout["container"]):
            continue
        items = _parse_layout(soup, layout)
        if items:
            return items
    return []


def get_sold_items(item_name):
    """Fetches up to MAX_RESULTS sold eBay listings matching item_name."""
    session = _build_session()
    params = {"_nkw": item_name, "LH_Complete": "1", "LH_Sold": "1"}

    try:
        response = session.get(EBAY_SEARCH_URL, params=params, timeout=15)
    except requests.RequestException as exc:
        logger.error("eBay request failed: %s", exc)
        return {"error": "Could not reach eBay. Please try again later."}

    if response.status_code != 200:
        logger.error("eBay returned HTTP %s for query %r", response.status_code, item_name)
        return {"error": f"eBay returned an error (HTTP {response.status_code})."}

    if _looks_blocked(response.text):
        logger.error("eBay served an anti-bot page for query %r", item_name)
        return {"error": "eBay is currently blocking automated requests. Please try again later."}

    items = parse_search_html(response.text)
    if not items:
        logger.warning("No sold items parsed for query %r", item_name)
        return {"error": "No sold items found for that search."}

    for item in items:
        if not item["image"]:
            item["image"] = get_high_res_image(session, item["link"])
    return items


@bot.command()
async def ebay(ctx, *, item_name):
    """Search eBay for recent sold items and display the results."""
    await ctx.send(f"🔎 Searching eBay for sold items matching: **{item_name}**...")

    results = await asyncio.to_thread(get_sold_items, item_name)

    if isinstance(results, dict) and "error" in results:
        await ctx.send(f"❌ {results['error']}")
        return

    for item in results:
        embed = discord.Embed(
            title=item["title"],
            description=(
                f"💰 **Sold Price**: {item['price']}\n"
                f"🔗 [View on eBay]({item['link']})"
            ),
            color=discord.Color.blue(),
        )
        if item.get("image"):
            embed.set_thumbnail(url=item["image"])

        await ctx.send(embed=embed)


@bot.event
async def on_ready():
    logger.info("Logged in as %s (id: %s)", bot.user, getattr(bot.user, "id", "unknown"))


def main():
    if not TOKEN:
        logger.error("DISCORD_TOKEN environment variable is not set. Exiting.")
        sys.exit(1)
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
