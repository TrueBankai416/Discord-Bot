# Systemd Setup Guide for Torrent Tracker Bot

This guide will help you set up the torrent tracker bot to run as a systemd service in the background.

## Quick Setup

1. **Run the setup script:**
   ```bash
   sudo ./setup.sh
   ```

2. **Configure the bot:**
   ```bash
   nano torrent_tracker_bot.py
   ```
   Set `TARGET_CHANNEL_ID` to your Discord channel ID.

3. **Set your Discord bot token:**
   ```bash
   sudo systemctl edit torrent-tracker-bot
   ```
   Add these lines:
   ```ini
   [Service]
   Environment=DISCORD_BOT_TOKEN=your_actual_bot_token_here
   ```

4. **Start the service:**
   ```bash
   sudo systemctl enable torrent-tracker-bot
   sudo systemctl start torrent-tracker-bot
   ```

## Manual Setup (if you prefer)

### 1. Create Virtual Environment
```bash
cd /var/discord/trackers
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Systemd Service
```bash
sudo cp torrent-tracker-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 3. Configure Bot Token
```bash
sudo systemctl edit torrent-tracker-bot
```
Add:
```ini
[Service]
Environment=DISCORD_BOT_TOKEN=your_bot_token_here
```

### 4. Configure Channel ID
Edit `torrent_tracker_bot.py` and set:
```python
TARGET_CHANNEL_ID = 1234567890123456789  # Your channel ID
```

### 5. Start Service
```bash
sudo systemctl enable torrent-tracker-bot
sudo systemctl start torrent-tracker-bot
```

## Service Management Commands

### Check Status
```bash
sudo systemctl status torrent-tracker-bot
```

### View Logs
```bash
# Live logs
sudo journalctl -u torrent-tracker-bot -f

# Recent logs
sudo journalctl -u torrent-tracker-bot --since "1 hour ago"
```

### Restart Service
```bash
sudo systemctl restart torrent-tracker-bot
```

### Stop Service
```bash
sudo systemctl stop torrent-tracker-bot
```

### Disable Auto-start
```bash
sudo systemctl disable torrent-tracker-bot
```

## Troubleshooting

### Bot Won't Start
1. Check logs: `sudo journalctl -u torrent-tracker-bot -n 50`
2. Verify bot token is set correctly
3. Ensure TARGET_CHANNEL_ID is configured
4. Check file permissions: `ls -la /var/discord/trackers/`

### Permission Issues
```bash
sudo chown -R root:root /var/discord/trackers/
sudo chmod +x /var/discord/trackers/torrent_tracker_bot.py
```

### Virtual Environment Issues
```bash
cd /var/discord/trackers
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart torrent-tracker-bot
```

### Update Bot Code
```bash
cd /var/discord/trackers
git pull  # if using git
sudo systemctl restart torrent-tracker-bot
```

## Security Notes

The service file includes security hardening:
- `NoNewPrivileges=true` - Prevents privilege escalation
- `PrivateTmp=true` - Isolates /tmp directory
- `ProtectSystem=strict` - Makes most of filesystem read-only
- `ProtectHome=true` - Hides user home directories
- `ReadWritePaths=/var/discord/trackers` - Only allows writes to bot directory

## File Locations

- **Service file:** `/etc/systemd/system/torrent-tracker-bot.service`
- **Bot directory:** `/var/discord/trackers/`
- **Virtual environment:** `/var/discord/trackers/venv/`
- **Data files:** `/var/discord/trackers/*.json`
- **Logs:** `journalctl -u torrent-tracker-bot`

## Getting Discord Channel ID

1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click on your target channel
3. Select "Copy Channel ID"
4. Use this ID in the `TARGET_CHANNEL_ID` setting
