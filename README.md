# discord_bot_ebay

A Discord bot that returns the last three **sold** eBay listings for a search term.

## Usage

In any channel the bot can see:

```
!ebay <search term>
```

Example: `!ebay pokemon charizard` returns up to three recent sold listings, each with
its sold price, an eBay link, and a thumbnail image.

## How it works

The bot scrapes eBay's completed/sold search results (handling both the `s-card` and
`s-item` page layouts) using `requests` + `BeautifulSoup`, and posts the results as
Discord embeds via `discord.py`.

## Deployment

Runs as a `systemd` service on a DigitalOcean Droplet. See [`DEPLOY.md`](./DEPLOY.md)
for the full setup walkthrough, and [`project_steps.md`](./project_steps.md) for
development notes.
