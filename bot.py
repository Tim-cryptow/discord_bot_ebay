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

def get_high_res_image(item_url):
    """
    Fetches the high-res image from the individual eBay item page.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DiscordBot/1.0; +https://discordapp.com)"
    }
    try:
        response = requests.get(item_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
    except Exception as e:
        print(f"Error fetching high-res image: {e}")
    return None

def get_sold_items(item_name):
    """
    Fetches sold items from eBay based on the provided item name.
    """
    query = "+".join(item_name.split())
    url = f"https://www.ebay.com/sch/i.html?_nkw={query}&LH_Complete=1&LH_Sold=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DiscordBot/1.0; +https://discordapp.com)"
    }
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        return {"error": "Unable to fetch results from eBay."}
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    sold_items = []
    for item in soup.select('.s-item'):
        link_tag = item.select_one('.s-item__link[href]')
        title_tag = item.select_one('.s-item__title')
        price_tag = item.select_one('.s-item__price')

        if link_tag and title_tag and price_tag:
            link = link_tag['href']
            title = title_tag.text.strip()
            price = price_tag.text.strip()

            if link.startswith("https://www.ebay.com/itm/") and "itm/" in link:
                sold_items.append({
                    "title": title,
                    "price": price,
                    "link": link
                })
    
    return sold_items[:3] if sold_items else {"error": "No valid sold items found."}

@bot.command()
async def ebay(ctx, *, item_name):
    """
    Discord command to search for sold eBay items and display results.
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
        
        image_url = get_high_res_image(item['link'])
        if image_url:
            embed.set_thumbnail(url=image_url)

        await ctx.send(embed=embed)

bot.run(TOKEN)
