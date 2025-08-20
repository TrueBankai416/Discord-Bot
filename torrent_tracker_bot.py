import discord
import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

client = discord.Client(intents=intents)

# Configuration
TARGET_CHANNEL_ID = None  # Set this to your target channel ID
CHECK_INTERVAL = 300  # Check every 5 minutes (300 seconds)
SUBSCRIPTIONS_FILE = "subscriptions.json"
TRACKER_STATUS_FILE = "tracker_status.json"

# Popular private trackers to monitor
TRACKERS = {
    "RED": {
        "name": "Redacted (RED)",
        "url": "https://redacted.ch",
        "signup_url": "https://redacted.ch/register.php",
        "description": "Music tracker"
    },
    "OPS": {
        "name": "Orpheus (OPS)",
        "url": "https://orpheus.network",
        "signup_url": "https://orpheus.network/register.php",
        "description": "Music tracker"
    },
    "PTP": {
        "name": "PassThePopcorn (PTP)",
        "url": "https://passthepopcorn.me",
        "signup_url": "https://passthepopcorn.me/register.php",
        "description": "Movie tracker"
    },
    "BTN": {
        "name": "BroadcasTheNet (BTN)",
        "url": "https://broadcasthe.net",
        "signup_url": "https://broadcasthe.net/register.php",
        "description": "TV tracker"
    },
    "HDB": {
        "name": "HDBits (HDB)",
        "url": "https://hdbits.org",
        "signup_url": "https://hdbits.org/register.php",
        "description": "HD movie/TV tracker"
    },
    "AB": {
        "name": "AnimeBytes (AB)",
        "url": "https://animebytes.tv",
        "signup_url": "https://animebytes.tv/register.php",
        "description": "Anime tracker"
    }
}

# Global variables
subscriptions: Dict[int, Set[str]] = {}  # user_id -> set of tracker codes
tracker_status: Dict[str, bool] = {}  # tracker_code -> is_open
last_check_time = None

def load_data():
    """Load subscriptions and tracker status from files"""
    global subscriptions, tracker_status
    
    # Load subscriptions
    try:
        if os.path.exists(SUBSCRIPTIONS_FILE):
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                data = json.load(f)
                subscriptions = {int(k): set(v) for k, v in data.items()}
        else:
            subscriptions = {}
    except Exception as e:
        logger.error(f"Error loading subscriptions: {e}")
        subscriptions = {}
    
    # Load tracker status
    try:
        if os.path.exists(TRACKER_STATUS_FILE):
            with open(TRACKER_STATUS_FILE, 'r') as f:
                tracker_status = json.load(f)
        else:
            tracker_status = {}
    except Exception as e:
        logger.error(f"Error loading tracker status: {e}")
        tracker_status = {}
    
    logger.info(f"Loaded {len(subscriptions)} user subscriptions and status for {len(tracker_status)} trackers")

def save_data():
    """Save subscriptions and tracker status to files"""
    try:
        # Save subscriptions
        with open(SUBSCRIPTIONS_FILE, 'w') as f:
            data = {str(k): list(v) for k, v in subscriptions.items()}
            json.dump(data, f, indent=2)
        
        # Save tracker status
        with open(TRACKER_STATUS_FILE, 'w') as f:
            json.dump(tracker_status, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

async def check_tracker_signup(session: aiohttp.ClientSession, tracker_code: str, tracker_info: dict) -> bool:
    """
    Check if a tracker has open signups
    This is a simplified implementation - in reality, you'd need to check each tracker's specific signup page
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with session.get(tracker_info['signup_url'], headers=headers, timeout=10) as response:
            if response.status == 200:
                text = await response.text()
                # Simple heuristic - look for common signup indicators
                # This would need to be customized for each tracker
                signup_indicators = [
                    'registration is open',
                    'sign up',
                    'create account',
                    'register now',
                    'join us'
                ]
                
                closed_indicators = [
                    'registration is closed',
                    'invites only',
                    'invitation required',
                    'closed registration'
                ]
                
                text_lower = text.lower()
                
                # Check for closed indicators first
                for indicator in closed_indicators:
                    if indicator in text_lower:
                        return False
                
                # Check for open indicators
                for indicator in signup_indicators:
                    if indicator in text_lower:
                        return True
                        
                return False
            else:
                logger.warning(f"Failed to check {tracker_code}: HTTP {response.status}")
                return False
                
    except Exception as e:
        logger.error(f"Error checking {tracker_code}: {e}")
        return False

async def monitor_trackers():
    """Main monitoring loop"""
    global last_check_time
    
    while True:
        try:
            logger.info("Checking tracker signups...")
            last_check_time = datetime.now()
            
            async with aiohttp.ClientSession() as session:
                for tracker_code, tracker_info in TRACKERS.items():
                    is_open = await check_tracker_signup(session, tracker_code, tracker_info)
                    previous_status = tracker_status.get(tracker_code, False)
                    
                    # If status changed from closed to open, notify subscribers
                    if is_open and not previous_status:
                        await notify_subscribers(tracker_code, tracker_info)
                    
                    tracker_status[tracker_code] = is_open
                    
                    # Small delay between checks to be respectful
                    await asyncio.sleep(2)
            
            save_data()
            logger.info(f"Tracker check completed. Next check in {CHECK_INTERVAL} seconds.")
            
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
        
        await asyncio.sleep(CHECK_INTERVAL)

async def notify_subscribers(tracker_code: str, tracker_info: dict):
    """Notify all subscribers when a tracker opens"""
    if not TARGET_CHANNEL_ID:
        return
    
    channel = client.get_channel(TARGET_CHANNEL_ID)
    if not channel:
        logger.error(f"Could not find channel {TARGET_CHANNEL_ID}")
        return
    
    # Create notification message
    embed = discord.Embed(
        title="🚨 Tracker Signup Open!",
        description=f"**{tracker_info['name']}** signups are now open!",
        color=0x00ff00,
        timestamp=datetime.now()
    )
    embed.add_field(name="Description", value=tracker_info['description'], inline=False)
    embed.add_field(name="Signup URL", value=tracker_info['signup_url'], inline=False)
    embed.set_footer(text="Act fast - signups may close at any time!")
    
    # Get all users subscribed to this tracker
    subscribers = []
    for user_id, user_trackers in subscriptions.items():
        if tracker_code in user_trackers:
            subscribers.append(f"<@{user_id}>")
    
    if subscribers:
        mention_text = " ".join(subscribers)
        await channel.send(f"{mention_text}", embed=embed)
    else:
        await channel.send(embed=embed)

@client.event
async def on_ready():
    print(f'Torrent Tracker Bot logged in as {client.user}')
    
    # Warn if TARGET_CHANNEL_ID is not set
    if TARGET_CHANNEL_ID is None:
        print("⚠️  WARNING: TARGET_CHANNEL_ID is not set!")
        print("   - Notifications will not be sent")
        print("   - Bot will respond in ALL channels where it has access")
        print("   - Please set TARGET_CHANNEL_ID in the script")
    else:
        channel = client.get_channel(TARGET_CHANNEL_ID)
        if channel:
            print(f"✅ Target channel set to: #{channel.name} ({TARGET_CHANNEL_ID})")
        else:
            print(f"❌ ERROR: Could not find channel with ID {TARGET_CHANNEL_ID}")
            print("   Please verify the channel ID is correct")
    
    load_data()
    # Start monitoring in the background
    asyncio.create_task(monitor_trackers())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    # Only respond in the target channel or when mentioned
    # If TARGET_CHANNEL_ID is None, respond everywhere (with warning logged)
    if TARGET_CHANNEL_ID is not None and message.channel.id != TARGET_CHANNEL_ID and not client.user.mentioned_in(message):
        return
    
    content = message.content.lower().strip()
    args = content.split()
    
    # Help command
    if content in ['!help', '!tracker help']:
        embed = discord.Embed(
            title="Torrent Tracker Signup Bot Commands",
            color=0x0099ff
        )
        embed.add_field(
            name="!trackers", 
            value="List all monitored trackers and their current status", 
            inline=False
        )
        embed.add_field(
            name="!subscribe <tracker>", 
            value="Subscribe to notifications for a specific tracker (e.g., !subscribe RED)", 
            inline=False
        )
        embed.add_field(
            name="!unsubscribe <tracker>", 
            value="Unsubscribe from notifications for a specific tracker", 
            inline=False
        )
        embed.add_field(
            name="!subscriptions", 
            value="List your current subscriptions", 
            inline=False
        )
        embed.add_field(
            name="!status", 
            value="Show bot status and last check time", 
            inline=False
        )
        await message.channel.send(embed=embed)
    
    # List trackers
    elif content == '!trackers':
        embed = discord.Embed(
            title="Monitored Torrent Trackers",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        for tracker_code, tracker_info in TRACKERS.items():
            status = "🟢 OPEN" if tracker_status.get(tracker_code, False) else "🔴 CLOSED"
            embed.add_field(
                name=f"{tracker_code} - {tracker_info['name']}",
                value=f"Status: {status}\nType: {tracker_info['description']}",
                inline=True
            )
        
        embed.set_footer(text=f"Last checked: {last_check_time.strftime('%Y-%m-%d %H:%M:%S UTC') if last_check_time else 'Never'}")
        await message.channel.send(embed=embed)
    
    # Subscribe to tracker
    elif content.startswith('!subscribe '):
        if len(args) < 2:
            await message.channel.send("❌ Please specify a tracker code. Example: `!subscribe RED`")
            return
        tracker_code = args[1].upper()
        
        if tracker_code not in TRACKERS:
            await message.channel.send(f"❌ Unknown tracker: {tracker_code}\nUse `!trackers` to see available trackers.")
            return
        
        user_id = message.author.id
        if user_id not in subscriptions:
            subscriptions[user_id] = set()
        
        if tracker_code in subscriptions[user_id]:
            await message.channel.send(f"ℹ️ You're already subscribed to {TRACKERS[tracker_code]['name']}")
        else:
            subscriptions[user_id].add(tracker_code)
            save_data()
            await message.channel.send(f"✅ Subscribed to {TRACKERS[tracker_code]['name']} notifications!")
    
    # Unsubscribe from tracker
    elif content.startswith('!unsubscribe '):
        if len(args) < 2:
            await message.channel.send("❌ Please specify a tracker code. Example: `!unsubscribe RED`")
            return
        tracker_code = args[1].upper()
        
        if tracker_code not in TRACKERS:
            await message.channel.send(f"❌ Unknown tracker: {tracker_code}")
            return
        
        user_id = message.author.id
        if user_id in subscriptions and tracker_code in subscriptions[user_id]:
            subscriptions[user_id].remove(tracker_code)
            if not subscriptions[user_id]:  # Remove empty subscription sets
                del subscriptions[user_id]
            save_data()
            await message.channel.send(f"✅ Unsubscribed from {TRACKERS[tracker_code]['name']} notifications!")
        else:
            await message.channel.send(f"ℹ️ You're not subscribed to {TRACKERS[tracker_code]['name']}")
    
    # List user subscriptions
    elif content == '!subscriptions':
        user_id = message.author.id
        user_subs = subscriptions.get(user_id, set())
        
        if not user_subs:
            await message.channel.send("ℹ️ You have no active subscriptions.")
        else:
            embed = discord.Embed(
                title="Your Subscriptions",
                color=0x0099ff
            )
            
            for tracker_code in user_subs:
                tracker_info = TRACKERS[tracker_code]
                status = "🟢 OPEN" if tracker_status.get(tracker_code, False) else "🔴 CLOSED"
                embed.add_field(
                    name=f"{tracker_code} - {tracker_info['name']}",
                    value=f"Status: {status}",
                    inline=True
                )
            
            await message.channel.send(embed=embed)
    
    # Bot status
    elif content == '!status':
        embed = discord.Embed(
            title="Bot Status",
            color=0x0099ff,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Last Check",
            value=last_check_time.strftime('%Y-%m-%d %H:%M:%S UTC') if last_check_time else 'Never',
            inline=True
        )
        embed.add_field(
            name="Check Interval",
            value=f"{CHECK_INTERVAL} seconds",
            inline=True
        )
        embed.add_field(
            name="Total Subscribers",
            value=str(len(subscriptions)),
            inline=True
        )
        
        open_trackers = sum(1 for status in tracker_status.values() if status)
        embed.add_field(
            name="Open Trackers",
            value=f"{open_trackers}/{len(TRACKERS)}",
            inline=True
        )
        
        await message.channel.send(embed=embed)

if __name__ == "__main__":
    # Replace with your bot token
    TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'CHANGE_ME')
    
    if TOKEN == 'CHANGE_ME':
        print("Please set your Discord bot token!")
        print("Either set the DISCORD_BOT_TOKEN environment variable or edit the script.")
        exit(1)
    
    client.run(TOKEN)
