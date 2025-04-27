import discord
discord.opus = None
from discord.ext import commands # type: ignore
import requests
from bs4 import BeautifulSoup
import os
import sys

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def get_sold_items(item_name):

    query = "+".join(item_name.split())
    url = f"https://www.ebay.com/sch/i.html?_nkw={query}&LH_Complete=1&LH_Sold=1"
    
    response = requests.get(url)
    if response.status_code != 200:
        return ["Error: Unable to fetch results from eBay."]
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    sold_items = set()  # to avoid duplicates
    for item in soup.select('.s-item__link[href]'):
        link = item['href']
        if link.startswith("https://www.ebay.com/itm/") and "itm/" in link:
            sold_items.add(link)
    
    return list(sold_items)[:3] if sold_items else ["No valid sold items found."]

@bot.command()
async def ebay(ctx, *, item_name):
    await ctx.send(f"Searching eBay for sold items matching: **{item_name}**...")
    results = get_sold_items(item_name)
    for link in results:
        await ctx.send(link)

bot.run(TOKEN)
