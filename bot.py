import os
os.environ["DISCORD_NO_VOICE"] = "1"
import discord
from discord.ext import commands # type: ignore
import requests
from bs4 import BeautifulSoup
import sys

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_sold_items(item_name):
    """
    Fetches sold items from eBay based on the provided item name, including the sold price and image.
    """
    query = "+".join(item_name.split())
    url = f"https://www.ebay.com/sch/i.html?_nkw={query}&LH_Complete=1&LH_Sold=1"
    
    response = requests.get(url)
    if response.status_code != 200:
        return {"error": "Unable to fetch results from eBay."}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    sold_items = []
    for item in soup.select('.s-item'):
        link_tag = item.select_one('.s-item__link[href]')
        title_tag = item.select_one('.s-item__title')
        price_tag = item.select_one('.s-item__price')
        image_tag = item.select_one('.s-item__image-img')  # Extract the item's image URL

        if link_tag and title_tag and price_tag:
            link = link_tag['href']
            title = title_tag.text.strip()
            price = price_tag.text.strip()
            image_url = image_tag['src'] if image_tag and image_tag.has_attr('src') else None

            if link.startswith("https://www.ebay.com/itm/") and "itm/" in link:
                sold_items.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "image": image_url
                })
    
    return sold_items[:3] if sold_items else {"error": "No valid sold items found."}

@bot.command()
async def ebay(ctx, *, item_name):
    """
    Discord command to search for sold eBay items and display results in the preferred format with images.
    """
    await ctx.send(f"🔎 Searching eBay for sold items matching: **{item_name}**...")
    results = get_sold_items(item_name)
    
    if "error" in results:
        await ctx.send(f"❌ {results['error']}")
        return
    
    for item in results:
        embed = discord.Embed(
            title=item['title'],
            description=(
                f"💰 **Sold Price**: {item['price']}\n"
                f"🔗 [View on eBay]({item['link']})"
            ),
            color=discord.Color.blue()
        )
        if item.get('image'):
            embed.set_thumbnail(url=item['image'])  # Add the item's image as a thumbnail

        await ctx.send(embed=embed)

bot.run(TOKEN)
