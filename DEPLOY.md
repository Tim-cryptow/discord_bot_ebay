# Deploying the eBay Discord Bot on a DigitalOcean Droplet

This guide runs the bot as a `systemd` service on a small Ubuntu Droplet. The bot
maintains a persistent gateway connection to Discord, so a long-running VM is the
natural fit.

## Prerequisites

- A Discord bot token (Discord Developer Portal -> your app -> Bot -> Reset Token).
- **Message Content Intent enabled**: Developer Portal -> your app -> Bot ->
  Privileged Gateway Intents -> enable **Message Content Intent**. Without this the
  `!ebay` command will never fire.
- The bot invited to your server with the *Send Messages* and *Embed Links* permissions.

## 1. Create the Droplet

- Create a Droplet: Ubuntu 24.04 LTS, the smallest shared-CPU size is sufficient.
- Add your SSH key, then connect: `ssh root@YOUR_DROPLET_IP`.

## 2. Install system packages

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git
```

## 3. Create a dedicated service user

The service file runs as `discordbot` from `/home/discordbot/discord_bot`.

```bash
adduser --system --group --home /home/discordbot discordbot
```

## 4. Clone the repository

```bash
git clone https://github.com/tim-cryptow/discord_bot_ebay.git /home/discordbot/discord_bot
chown -R discordbot:discordbot /home/discordbot/discord_bot
```

## 5. Create the virtual environment and install dependencies

```bash
cd /home/discordbot/discord_bot
sudo -u discordbot python3 -m venv venv
sudo -u discordbot venv/bin/pip install --upgrade pip
sudo -u discordbot venv/bin/pip install -r requirements.txt
```

## 6. Provide the bot token

Secrets are kept out of the repository and loaded by `systemd` from a root-owned file:

```bash
echo 'DISCORD_TOKEN=PASTE_YOUR_REAL_TOKEN_HERE' > /etc/discord_bot_ebay.env
chmod 600 /etc/discord_bot_ebay.env
```

## 7. Install and start the service

```bash
cp /home/discordbot/discord_bot/discord_bot.service /etc/systemd/system/discordbot.service
systemctl daemon-reload
systemctl enable --now discordbot
```

## 8. Verify

```bash
systemctl status discordbot
journalctl -u discordbot -f
```

A healthy start logs `Logged in as <bot name>`. In Discord, run:

```
!ebay pokemon charizard
```

You should get up to three embeds, each with a sold price, an eBay link, and a thumbnail.

## Updating the bot later

```bash
cd /home/discordbot/discord_bot
sudo -u discordbot git pull
sudo -u discordbot venv/bin/pip install -r requirements.txt
systemctl restart discordbot
```

## Troubleshooting / caveats

- **"eBay is currently blocking automated requests"** or **"No sold items found"**:
  eBay blocks datacenter IP ranges (which includes DigitalOcean's) more aggressively
  than residential ones, and varies its page layout. If this persists, the options are
  to route eBay requests through a proxy, or to migrate to eBay's official API (note:
  sold/completed price data requires the gated Marketplace Insights API, not the open
  Browse API). The scraper already handles both the `s-card` and `s-item` layouts and
  sends browser-like headers, which covers the common cases.
- **Commands do nothing**: confirm the **Message Content Intent** is enabled (see
  Prerequisites) and that the bot has *Send Messages* / *Embed Links* permissions in
  the channel.
- **Service keeps restarting**: `journalctl -u discordbot -e` usually shows the cause
  (an invalid token logs a Discord `LoginFailure`).
