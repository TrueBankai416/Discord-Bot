# Torrent Tracker Signup Bot

A Discord bot that monitors popular private torrent trackers for open signups and notifies subscribed users when registrations become available.

## Features

- **Real-time Monitoring**: Checks tracker signup pages and Reddit every 5 minutes
- **User Subscriptions**: Users can subscribe to specific trackers or Reddit notifications
- **Instant Notifications**: Sends Discord notifications when signups become available
- **Multiple Sources**: Monitors 12 torrent trackers, 4 Usenet indexers, and Reddit r/OpenSignups
- **Smart Detection**: Extracts expiration dates and invite codes from Reddit posts
- **Persistent Storage**: Saves user subscriptions and tracker status between restarts

## Monitored Sources

### Torrent Trackers
- **RED** (Redacted) - Music tracker
- **OPS** (Orpheus) - Music tracker  
- **PTP** (PassThePopcorn) - Movie tracker
- **BTN** (BroadcastTheNet) - TV tracker
- **HDB** (HDBits) - HD movie/TV tracker
- **AB** (AnimeBytes) - Anime tracker
- **TL** (TorrentLeech) - General tracker
- **FNP** (FeenoPeer) - General tracker
- **SP** (SeedPool) - General tracker
- **DC** (DigitalCore) - General tracker
- **OTW** (Old Toons World) - Cartoon/Animation tracker
- **BBT** (BakaBT) - Anime tracker

### Usenet Indexers
- **DS** (DrunkenSlug) - Usenet indexer
- **GEEK** (NZBGeek) - Usenet indexer
- **PLANET** (NZBPlanet) - Usenet indexer
- **FINDER** (NZBFinder) - Usenet indexer

### Reddit Monitoring
- **r/OpenSignups** - Automatic monitoring of Reddit's OpenSignups community

## Setup

### Prerequisites

1. Python 3.8 or higher
2. A Discord bot token
3. Required Python packages (see requirements.txt)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Discord-Bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a Discord Bot**:
   - Go to https://discord.com/developers/applications
   - Create a new application
   - Go to the "Bot" section
   - Create a bot and copy the token
   - Enable the following bot permissions:
     - Send Messages
     - Read Message History
     - Use Slash Commands
     - Embed Links

4. **Configure the bot**:
   - Set your Discord bot token as an environment variable:
     ```bash
     export DISCORD_BOT_TOKEN="your_bot_token_here"
     ```
   - Or edit `torrent_tracker_bot.py` and replace `'CHANGE_ME'` with your token
   - Set the `TARGET_CHANNEL_ID` in the script to your desired channel ID

5. **Run the bot**:
   ```bash
   python torrent_tracker_bot.py
   ```

## Commands

### `!help` or `!tracker help`
Shows all available commands and their usage.

### `!trackers`
Lists all monitored trackers with their current signup status (OPEN/CLOSED).

### `!subscribe <tracker>`
Subscribe to notifications for a specific tracker or Reddit.
- Example: `!subscribe RED` or `!subscribe REDDIT`
- Available trackers: RED, OPS, PTP, BTN, HDB, AB, TL, FNP, SP, DC, OTW, BBT
- Available indexers: DS, GEEK, PLANET, FINDER
- Use `REDDIT` for r/OpenSignups notifications

### `!unsubscribe <tracker>`
Unsubscribe from notifications for a specific tracker.
- Example: `!unsubscribe RED`

### `!subscriptions`
Shows your current subscriptions and their status.

### `!status`
Shows bot status including last check time, check interval, and statistics.

## How It Works

1. **Monitoring**: The bot checks each tracker's signup page every 5 minutes
2. **Detection**: It looks for common signup indicators in the HTML content
3. **Notifications**: When a tracker changes from closed to open, it notifies all subscribers
4. **Persistence**: User subscriptions and tracker status are saved to JSON files

## Important Notes

### Limitations

- **Detection Accuracy**: The bot uses simple heuristics to detect open signups. Some trackers may require manual verification.
- **Rate Limiting**: The bot includes delays between requests to be respectful to tracker servers.
- **Legal Compliance**: This bot only monitors publicly accessible signup pages and does not bypass any restrictions.

### Disclaimer

This bot is for educational and informational purposes only. Users are responsible for:
- Following the rules and terms of service of each tracker
- Ensuring they have legitimate reasons for joining private trackers
- Respecting the communities and maintaining good ratios

## Configuration

### Environment Variables

- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `TARGET_CHANNEL_ID`: (Optional) Set in code - the channel where notifications are sent

### Files Created

- `subscriptions.json`: Stores user subscriptions
- `tracker_status.json`: Stores current tracker status

### Customization

You can modify the following in `torrent_tracker_bot.py`:

- `CHECK_INTERVAL`: How often to check trackers (default: 300 seconds)
- `TRACKERS`: Add or remove trackers to monitor
- Detection logic in `check_tracker_signup()` function

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check that the bot has proper permissions in your Discord server
2. **No notifications**: Verify `TARGET_CHANNEL_ID` is set correctly
3. **False positives**: The detection logic may need adjustment for specific trackers

### Logs

The bot logs important events to the console. Check the output for error messages and status updates.

## Contributing

Feel free to contribute by:
- Adding support for more trackers
- Improving detection accuracy
- Adding new features
- Reporting bugs

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.
