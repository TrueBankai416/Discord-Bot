#!/bin/bash

# Torrent Tracker Bot Setup Script
set -e

echo "🚀 Setting up Torrent Tracker Bot..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (sudo ./setup.sh)"
    exit 1
fi

# Get script directory (where the repo files are)
SCRIPT_DIR=$(dirname "$(realpath "$0")")
echo "📂 Script location: $SCRIPT_DIR"

# Set up target directory
BOT_DIR="/var/discord/trackers"
echo "📁 Target directory: $BOT_DIR"

# Create target directory if it doesn't exist
mkdir -p "$BOT_DIR"

# Copy files if not already in target directory
if [ "$SCRIPT_DIR" != "$BOT_DIR" ]; then
    echo "📋 Copying bot files to $BOT_DIR..."
    cp "$SCRIPT_DIR"/*.py "$BOT_DIR/"
    cp "$SCRIPT_DIR"/*.txt "$BOT_DIR/"
    cp "$SCRIPT_DIR"/*.service "$BOT_DIR/" 2>/dev/null || true
    cp "$SCRIPT_DIR"/*.md "$BOT_DIR/" 2>/dev/null || true
    echo "✅ Files copied successfully"
else
    echo "✅ Already running from target directory"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$BOT_DIR/venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv "$BOT_DIR/venv"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
source "$BOT_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$BOT_DIR/requirements.txt"

# Copy systemd service file
echo "⚙️  Installing systemd service..."
cp "$BOT_DIR/torrent-tracker-bot.service" /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit the bot configuration:"
echo "   nano $BOT_DIR/torrent_tracker_bot.py"
echo "   - Set TARGET_CHANNEL_ID to your Discord channel ID"
echo ""
echo "2. Set your Discord bot token:"
echo "   systemctl edit torrent-tracker-bot"
echo "   Add these lines:"
echo "   [Service]"
echo "   Environment=DISCORD_BOT_TOKEN=your_actual_bot_token_here"
echo ""
echo "3. Start the bot:"
echo "   systemctl enable torrent-tracker-bot"
echo "   systemctl start torrent-tracker-bot"
echo ""
echo "4. Check status:"
echo "   systemctl status torrent-tracker-bot"
echo "   journalctl -u torrent-tracker-bot -f"
echo ""
