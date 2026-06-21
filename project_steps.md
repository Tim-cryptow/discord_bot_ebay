# Project Steps: Discord eBay Bot

This file outlines the steps to create, configure, and deploy the Discord eBay Bot that returns the last three sold item for any words given.

---

## 1. Project Setup

1. Install Python 3.8+ on your system.
2. Set up a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install required Python libraries:
   ```bash
   pip install discord.py requests beautifulsoup4
   ```

4. Save the dependencies:
   ```bash
   pip freeze > requirements.txt
   ```

---

## 2. Building the Bot

1. Write the bot script (`bot.py`) with the following key features:
   - Fetch sold items from eBay using `requests` and `BeautifulSoup`.
   - Implement the `!ebay` command using `discord.py`.

2. Create a `.env` file to store sensitive credentials:
   ```plaintext
   DISCORD_TOKEN=your_discord_bot_token
   ```

3. Add a `.gitignore` file to exclude unnecessary files from the repository.

---

## 3. Testing Locally

1. Provide the token and run the bot locally (the bot reads `DISCORD_TOKEN` from the
   environment):
   ```bash
   cp .env.example .env   # then edit .env and paste your token
   set -a; source .env; set +a
   python bot.py
   ```

2. Test the bot commands on your Discord server, e.g. `!ebay pokemon charizard`.

---

## 4. Deployment

The bot runs as a `systemd` service. A complete, step-by-step DigitalOcean Droplet
walkthrough lives in [`DEPLOY.md`](./DEPLOY.md), covering server setup, the service
user, the virtual environment, token handling via `/etc/discord_bot_ebay.env`, and
verification.

The unit file is [`discord_bot.service`](./discord_bot.service); install it to
`/etc/systemd/system/` and load the token from the environment file rather than
hardcoding it.

---

## 6. Final Steps

1. Update the `README.md` and other project files as needed.

2. Share the bot with your Discord server and test its uptime.
