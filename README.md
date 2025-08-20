# Discord Bots Collection

This repository contains multiple Discord bots for different purposes.

## Bots Available

### 1. Nextcloud Support Bot (`bot.py`)
A Discord bot that provides automated support for Nextcloud-related questions.

**Features:**
- Responds to common Nextcloud questions
- Provides documentation links for migration, reverse proxy setup, and OCC commands
- Interactive reverse proxy configuration help
- Supports Nginx, Apache, and Caddy configurations

**Usage:**
- Configure the `TARGET_CHANNEL_ID` and bot token
- Run with: `python bot.py`

### 2. Torrent Tracker Signup Bot (`torrent_tracker_bot.py`)
A Discord bot that monitors popular private torrent trackers for open signups and notifies users.

**Features:**
- Monitors 6 popular private trackers (RED, OPS, PTP, BTN, HDB, AB)
- User subscription system
- Real-time notifications when signups open
- Persistent storage of subscriptions and tracker status
- Comprehensive command system

**Usage:**
- See `README_torrent_tracker_bot.md` for detailed setup instructions
- Install dependencies: `pip install -r requirements.txt`
- Configure bot token and channel ID
- Run with: `python torrent_tracker_bot.py`

## Configuration Files

The repository also includes example reverse proxy configurations:
- `nextcloud_nginx.conf` - Nginx configuration for Nextcloud
- `apache.conf` - Apache configuration for Nextcloud  
- `Caddyfile` - Caddy configuration for Nextcloud

## Setup Requirements

### For Nextcloud Bot:
- Python 3.6+
- discord.py library
- Discord bot token

### For Torrent Tracker Bot:
- Python 3.8+
- Dependencies from `requirements.txt`
- Discord bot token
- Target channel ID configuration

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Contributing

Feel free to contribute by:
- Adding new bot features
- Improving existing functionality
- Adding support for more services
- Reporting bugs and issues

## Disclaimer

These bots are for educational and informational purposes. Users are responsible for following Discord's Terms of Service and any applicable laws and regulations.
