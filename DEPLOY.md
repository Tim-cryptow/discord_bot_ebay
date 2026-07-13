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

## Using a residential proxy (datacenter-IP blocking)

eBay blocks datacenter IPs, so from a host like DigitalOcean every search returns
HTTP 403. The fix is to route eBay requests through a **residential** proxy. Usage is
tiny (a few MB per search), so a pay-as-you-go residential plan costs pennies.

1. Sign up with a residential proxy provider (e.g. DataImpulse or IPRoyal) and copy the
   endpoint they give you, in the form `http://username:password@host:port`.
2. Add it to the environment file and restart:
   ```bash
   echo 'EBAY_PROXY=http://username:password@host:port' >> /etc/discord_bot_ebay.env
   systemctl restart discordbot
   ```
3. Confirm it was picked up: `journalctl -u discordbot -e` should log
   `eBay proxy configured: yes`. Then test `!ebay pokemon charizard`.

Leave `EBAY_PROXY` unset to connect directly (fine on a residential/unblocked host).

## Troubleshooting / caveats

- **"eBay returned an error (HTTP 403)"** or **"blocking automated requests"**:
  eBay blocks datacenter IP ranges (DigitalOcean's included). The scraper already uses
  curl_cffi Chrome impersonation and handles both the `s-card` and `s-item` layouts, but
  from a blocked IP the only reliable fix is a **residential proxy** — see "Using a
  residential proxy" above. (Alternatively run on a residential/unblocked host, or move to
  eBay's official API, whose sold-price data needs the gated Marketplace Insights API.)
- **Commands do nothing**: confirm the **Message Content Intent** is enabled (see
  Prerequisites) and that the bot has *Send Messages* / *Embed Links* permissions in
  the channel.
- **Service keeps restarting**: `journalctl -u discordbot -e` usually shows the cause
  (an invalid token logs a Discord `LoginFailure`).
