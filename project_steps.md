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

1. Run the bot locally:
   ```bash
   python bot.py
   ```

2. Test the bot commands on your Discord server.

---

## 4. **Preparing for Deployment**

1. Create a `discord_bot.service` file for systemd to run the bot as a service
   
2. Place the file in `/etc/systemd/system/`.

---

## 5. Deploying on Contabo

1. Log in to your Contabo server using SSH.
2. Upload your project files to the server:
   ```bash
   scp -r /local/project/path user@server-ip:/remote/project/path
   ```

3. Install Python and dependencies on the server:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   pip install -r requirements.txt
   ```

4. Start the bot as a service:
   ```bash
   sudo systemctl enable discord_bot
   sudo systemctl start discord_bot
   ```

---

## 6. Final Steps

1. Update the `README.md` and other project files as needed.

2. Share the bot with your Discord server and test its uptime.
