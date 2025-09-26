import discord
import asyncio
import aiohttp
import json
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Set, Optional
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

# English-focused private trackers to monitor
TRACKERS = {
    "RED": {
        "name": "Redacted (RED)",
        "url": "https://redacted.ch",
        "signup_url": "https://redacted.ch/register.php",
        "description": "English music tracker",
        "type": "tracker",
        "language": "english"
    },
    "OPS": {
        "name": "Orpheus (OPS)",
        "url": "https://orpheus.network",
        "signup_url": "https://orpheus.network/register.php",
        "description": "English music tracker",
        "type": "tracker",
        "language": "english"
    },
    "PTP": {
        "name": "PassThePopcorn (PTP)",
        "url": "https://passthepopcorn.me",
        "signup_url": "https://passthepopcorn.me/register.php",
        "description": "English movie tracker",
        "type": "tracker",
        "language": "english"
    },
    "BTN": {
        "name": "BroadcastTheNet (BTN)",
        "url": "https://broadcasthe.net",
        "signup_url": "https://broadcasthe.net/register.php",
        "description": "English TV tracker",
        "type": "tracker",
        "language": "english"
    },
    "HDB": {
        "name": "HDBits (HDB)",
        "url": "https://hdbits.org",
        "signup_url": "https://hdbits.org/register.php",
        "description": "English HD movie/TV tracker",
        "type": "tracker",
        "language": "english"
    },
    "TL": {
        "name": "TorrentLeech (TL)",
        "url": "https://www.torrentleech.org",
        "signup_url": "https://www.torrentleech.org/user/account/register",
        "description": "English general tracker",
        "type": "tracker",
        "language": "english"
    },
    "OTW": {
        "name": "Old Toons World (OTW)",
        "url": "https://oldtoonsworld.com",
        "signup_url": "https://oldtoonsworld.com/register.php",
        "description": "English cartoon/animation tracker",
        "type": "tracker",
        "language": "english"
    },
    # English Usenet Indexers
    "DS": {
        "name": "DrunkenSlug (DS)",
        "url": "https://drunkenslug.com",
        "signup_url": "https://drunkenslug.com/register",
        "description": "English Usenet indexer",
        "type": "usenet",
        "language": "english"
    },
    "GEEK": {
        "name": "NZBGeek (GEEK)",
        "url": "https://nzbgeek.info",
        "signup_url": "https://nzbgeek.info/register.php",
        "description": "English Usenet indexer",
        "type": "usenet",
        "language": "english"
    },
    "PLANET": {
        "name": "NZBPlanet (PLANET)",
        "url": "https://nzbplanet.net",
        "signup_url": "https://nzbplanet.net/register",
        "description": "English Usenet indexer",
        "type": "usenet",
        "language": "english"
    },
    "FINDER": {
        "name": "NZBFinder (FINDER)",
        "url": "https://nzbfinder.ws",
        "signup_url": "https://nzbfinder.ws/register",
        "description": "English Usenet indexer",
        "type": "usenet",
        "language": "english"
    }
}

# Global variables
subscriptions: Dict[int, Set[str]] = {}  # user_id -> set of tracker codes
tracker_status: Dict[str, bool] = {}  # tracker_code -> is_open
reddit_posts: Dict[str, dict] = {}  # post_id -> post_data
last_check_time = None
REDDIT_FILE = "reddit_posts.json"
data_lock = asyncio.Lock()  # Prevent concurrent file writes

def load_data():
    """Load subscriptions, tracker status, and reddit posts from files"""
    global subscriptions, tracker_status, reddit_posts
    
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
    
    # Load reddit posts
    try:
        if os.path.exists(REDDIT_FILE):
            with open(REDDIT_FILE, 'r') as f:
                reddit_posts = json.load(f)
        else:
            reddit_posts = {}
    except Exception as e:
        logger.error(f"Error loading reddit posts: {e}")
        reddit_posts = {}
    
    logger.info(f"Loaded {len(subscriptions)} user subscriptions, status for {len(tracker_status)} trackers, and {len(reddit_posts)} reddit posts")

async def save_data():
    """Save subscriptions, tracker status, and reddit posts to files"""
    async with data_lock:
        try:
            # Save subscriptions
            with open(SUBSCRIPTIONS_FILE, 'w') as f:
                data = {str(k): list(v) for k, v in subscriptions.items()}
                json.dump(data, f, indent=2)
            
            # Save tracker status
            with open(TRACKER_STATUS_FILE, 'w') as f:
                json.dump(tracker_status, f, indent=2)
            
            # Save reddit posts
            with open(REDDIT_FILE, 'w') as f:
                json.dump(reddit_posts, f, indent=2)
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
                    'invitation required',
                    'closed registration',
                    'registration disabled'
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

def is_likely_english(text: str) -> bool:
    """Simple heuristic to detect if text is likely English"""
    if not text:
        return True  # Default to English for empty text
    
    # Common English words that are good indicators
    english_indicators = [
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'man', 'end', 'few', 'got', 'let', 'put', 'say', 'she', 'too', 'use'
    ]
    
    # Non-English indicators (common words in other languages, excluding English false positives)
    non_english_indicators = [
        # French
        'le', 'de', 'et', 'à', 'un', 'il', 'être', 'avoir', 'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par', 'grand', 'bien', 'autre', 'comme', 'notre', 'sans', 'peut', 'cette', 'faire', 'leur', 'si', 'dit', 'elle', 'deux', 'même', 'lui', 'temps', 'très', 'état', 'sous', 'fait', 'lors', 'depuis', 'contre', 'lieu', 'vie', 'dont', 'fois', 'point', 'année', 'encore', 'aussi', 'alors', 'après', 'ainsi', 'où', 'tant', 'moins', 'selon', 'entre', 'pendant', 'avant', 'toujours', 'jamais', 'souvent', 'parfois', 'quelque', 'chaque', 'plusieurs', 'certains', 'autres', 'tous', 'toutes', 'aucun', 'aucune', 'quelques', 'beaucoup', 'peu', 'assez', 'trop', 'plus', 'moins', 'autant', 'tant', 'si', 'aussi', 'comme', 'que', 'quand', 'où', 'comment', 'pourquoi', 'qui', 'quoi', 'dont', 'lequel', 'laquelle', 'lesquels', 'lesquelles',
        # German (excluding "in" and other English words)
        'der', 'die', 'und', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als', 'auch', 'es', 'an', 'werden', 'aus', 'er', 'hat', 'dass', 'sie', 'nach', 'wird', 'bei', 'einer', 'um', 'am', 'sind', 'noch', 'wie', 'einem', 'über', 'einen', 'so', 'zum', 'war', 'haben', 'nur', 'oder', 'aber', 'vor', 'zur', 'bis', 'mehr', 'durch', 'man', 'sein', 'wurde', 'sei', 'können', 'müssen', 'sollen', 'wollen', 'dürfen', 'mögen', 'lassen', 'gehen', 'kommen', 'sehen', 'wissen', 'sagen', 'geben', 'nehmen', 'machen', 'leben', 'arbeiten', 'spielen', 'lernen', 'verstehen', 'sprechen', 'hören', 'fragen', 'antworten', 'denken', 'glauben', 'hoffen', 'wünschen', 'lieben', 'hassen', 'mögen', 'gefallen', 'helfen', 'brauchen', 'kaufen', 'verkaufen', 'bezahlen', 'kosten', 'verdienen', 'sparen', 'ausgeben', 'finden', 'suchen', 'verlieren', 'gewinnen', 'beginnen', 'aufhören', 'weitermachen', 'bleiben', 'fahren', 'fliegen', 'laufen', 'rennen', 'springen', 'fallen', 'steigen', 'sinken', 'wachsen', 'schrumpfen', 'öffnen', 'schließen', 'bauen', 'zerstören', 'reparieren', 'putzen', 'waschen', 'trocknen', 'kochen', 'essen', 'trinken', 'schlafen', 'aufwachen', 'träumen', 'lachen', 'weinen', 'lächeln', 'küssen', 'umarmen', 'berühren', 'fühlen', 'riechen', 'schmecken', 'schauen', 'beobachten', 'zeigen', 'erklären', 'lehren', 'lernen', 'studieren', 'prüfen', 'testen', 'messen', 'wiegen', 'zählen', 'rechnen', 'addieren', 'subtrahieren', 'multiplizieren', 'dividieren', 'vergleichen', 'unterscheiden', 'ähneln', 'gleichen', 'passen', 'gehören', 'besitzen', 'haben', 'bekommen', 'erhalten', 'geben', 'schenken', 'leihen', 'borgen', 'zurückgeben', 'behalten', 'wegwerfen', 'sammeln', 'ordnen', 'sortieren', 'organisieren', 'planen', 'vorbereiten', 'entscheiden', 'wählen', 'bevorzugen', 'ablehnen', 'akzeptieren', 'zustimmen', 'widersprechen', 'diskutieren', 'streiten', 'kämpfen', 'gewinnen', 'verlieren', 'siegen', 'besiegen', 'scheitern', 'erfolgreich', 'glücklich', 'traurig', 'wütend', 'ängstlich', 'nervös', 'ruhig', 'entspannt', 'müde', 'energisch', 'stark', 'schwach', 'gesund', 'krank', 'jung', 'alt', 'neu', 'alt', 'groß', 'klein', 'hoch', 'niedrig', 'lang', 'kurz', 'breit', 'schmal', 'dick', 'dünn', 'schwer', 'leicht', 'hart', 'weich', 'heiß', 'kalt', 'warm', 'kühl', 'hell', 'dunkel', 'laut', 'leise', 'schnell', 'langsam', 'früh', 'spät', 'pünktlich', 'verspätet', 'rechtzeitig', 'sofort', 'bald', 'später', 'niemals', 'immer', 'manchmal', 'oft', 'selten', 'täglich', 'wöchentlich', 'monatlich', 'jährlich', 'heute', 'gestern', 'morgen', 'übermorgen', 'vorgestern', 'jetzt', 'dann', 'damals', 'früher', 'später', 'zuerst', 'danach', 'schließlich', 'endlich', 'plötzlich', 'langsam', 'schnell', 'vorsichtig', 'sorgfältig', 'genau', 'ungefähr', 'etwa', 'fast', 'ganz', 'halb', 'voll', 'leer', 'offen', 'geschlossen', 'frei', 'besetzt', 'verfügbar', 'beschäftigt', 'fertig', 'bereit', 'möglich', 'unmöglich', 'wahrscheinlich', 'unwahrscheinlich', 'sicher', 'unsicher', 'gefährlich', 'sicher', 'einfach', 'schwierig', 'leicht', 'schwer', 'interessant', 'langweilig', 'wichtig', 'unwichtig', 'nützlich', 'nutzlos', 'notwendig', 'unnötig', 'richtig', 'falsch', 'wahr', 'unwahr', 'echt', 'falsch', 'natürlich', 'künstlich', 'normal', 'abnormal', 'gewöhnlich', 'ungewöhnlich', 'typisch', 'untypisch', 'bekannt', 'unbekannt', 'berühmt', 'unberühmt', 'beliebt', 'unbeliebt', 'freundlich', 'unfreundlich', 'höflich', 'unhöflich', 'nett', 'gemein', 'gut', 'schlecht', 'besser', 'schlechter', 'am besten', 'am schlechtesten', 'mehr', 'weniger', 'am meisten', 'am wenigsten', 'viel', 'wenig', 'genug', 'zu viel', 'zu wenig', 'alles', 'nichts', 'etwas', 'jemand', 'niemand', 'alle', 'keiner', 'einige', 'manche', 'andere', 'verschiedene', 'gleiche', 'ähnliche', 'unterschiedliche', 'dieselben', 'andere', 'nächste', 'letzte', 'erste', 'zweite', 'dritte', 'vierte', 'fünfte', 'sechste', 'siebte', 'achte', 'neunte', 'zehnte', 'elfte', 'zwölfte', 'dreizehnte', 'vierzehnte', 'fünfzehnte', 'sechzehnte', 'siebzehnte', 'achtzehnte', 'neunzehnte', 'zwanzigste', 'einundzwanzigste', 'zweiundzwanzigste', 'dreiundzwanzigste', 'vierundzwanzigste', 'fünfundzwanzigste', 'sechsundzwanzigste', 'siebenundzwanzigste', 'achtundzwanzigste', 'neunundzwanzigste', 'dreißigste', 'vierzigste', 'fünfzigste', 'sechzigste', 'siebzigste', 'achtzigste', 'neunzigste', 'hundertste', 'tausendste', 'millionste', 'milliardste', 'billionste',
        # Spanish
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'una', 'ser', 'del', 'los', 'si', 'ya', 'pero', 'más', 'o', 'este', 'sus', 'ha', 'me', 'mi', 'porque', 'qué', 'sólo', 'han', 'yo', 'hay', 'vez', 'puede', 'todos', 'así', 'nos', 'ni', 'parte', 'tiene', 'él', 'uno', 'donde', 'bien', 'tiempo', 'muy', 'cuando', 'sin', 'sobre', 'también', 'hasta', 'quien', 'desde', 'todo', 'durante', 'les', 'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'unos', 'otro', 'otras', 'otra', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros', 'mis', 'tú', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros', 'vosotras', 'os', 'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo', 'suya', 'suyos', 'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro', 'vuestra', 'vuestros', 'vuestras', 'esos', 'esas'
    ]
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    if len(words) < 3:
        return True  # Too short to determine, assume English
    
    english_count = sum(1 for word in words if word in english_indicators)
    non_english_count = sum(1 for word in words if word in non_english_indicators)
    
    # If we have a significant number of non-English indicators, it's probably not English
    if non_english_count > len(words) * 0.15:  # More than 15% non-English indicators
        return False
    
    # If we have English indicators or no strong non-English indicators, assume English
    return english_count > 0 or non_english_count == 0

async def check_reddit_opensignups(session: aiohttp.ClientSession) -> List[dict]:
    """Check /r/OpenSignups for new posts"""
    try:
        headers = {
            'User-Agent': 'TorrentTrackerBot/1.0 (Discord Bot for signup notifications)'
        }
        
        # Use Reddit JSON API
        url = "https://www.reddit.com/r/OpenSignups/new.json?limit=25"
        
        async with session.get(url, headers=headers, timeout=15) as response:
            if response.status == 200:
                data = await response.json()
                new_posts = []
                
                for post in data['data']['children']:
                    post_data = post['data']
                    post_id = post_data['id']
                    
                    # Skip if we've already seen this post
                    if post_id in reddit_posts:
                        continue
                    
                    # Extract relevant information
                    title = post_data['title']
                    url = post_data['url']
                    selftext = post_data.get('selftext', '')
                    created_utc = post_data['created_utc']
                    author = post_data['author']
                    permalink = f"https://reddit.com{post_data['permalink']}"
                    
                    # Check if the post is likely in English
                    full_text = f"{title} {selftext}"
                    if not is_likely_english(full_text):
                        logger.info(f"Skipping non-English Reddit post: {title[:50]}...")
                        continue
                    
                    # Look for expiration dates and invite codes in title and text
                    full_text_lower = full_text.lower()
                    
                    # Extract expiration date patterns
                    expiry_patterns = [
                        r'expires?\s+(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                        r'until\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                        r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{2,4})',
                        r'ends?\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                        r'closes?\s+(?:on\s+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
                    ]
                    
                    expiry_date = None
                    for pattern in expiry_patterns:
                        match = re.search(pattern, full_text_lower, re.IGNORECASE)
                        if match:
                            expiry_date = match.group(1)
                            break
                    
                    # Extract invite codes
                    invite_patterns = [
                        r'invite\s*code[:\s]+([A-Za-z0-9]+)',
                        r'code[:\s]+([A-Za-z0-9]+)',
                        r'use[:\s]+([A-Za-z0-9]+)',
                        r'registration\s*code[:\s]+([A-Za-z0-9]+)'
                    ]
                    
                    invite_code = None
                    for pattern in invite_patterns:
                        match = re.search(pattern, full_text_lower, re.IGNORECASE)
                        if match:
                            invite_code = match.group(1)
                            break
                    
                    # Determine tracker type from title
                    tracker_type = "tracker"  # default
                    if any(word in full_text_lower for word in ['usenet', 'nzb', 'indexer']):
                        tracker_type = "usenet"
                    
                    post_info = {
                        'id': post_id,
                        'title': title,
                        'url': url,
                        'selftext': selftext,
                        'author': author,
                        'permalink': permalink,
                        'created_utc': created_utc,
                        'expiry_date': expiry_date,
                        'invite_code': invite_code,
                        'tracker_type': tracker_type,
                        'notified': False
                    }
                    
                    reddit_posts[post_id] = post_info
                    new_posts.append(post_info)
                
                return new_posts
            else:
                logger.warning(f"Failed to check Reddit: HTTP {response.status}")
                return []
                
    except Exception as e:
        logger.error(f"Error checking Reddit: {e}")
        return []

async def notify_reddit_signup(post_info: dict):
    """Notify subscribers about a Reddit signup post"""
    if not TARGET_CHANNEL_ID:
        return
    
    channel = client.get_channel(TARGET_CHANNEL_ID)
    if not channel:
        logger.error(f"Could not find channel {TARGET_CHANNEL_ID}")
        return
    
    # Create notification message
    embed = discord.Embed(
        title="🔥 New Signup from r/OpenSignups!",
        description=post_info['title'],
        color=0xff4500,  # Reddit orange
        timestamp=datetime.fromtimestamp(post_info['created_utc'], timezone.utc),
        url=post_info['permalink']
    )
    
    embed.add_field(name="Type", value=post_info['tracker_type'].title(), inline=True)
    embed.add_field(name="Author", value=f"u/{post_info['author']}", inline=True)
    
    if post_info['expiry_date']:
        embed.add_field(name="⏰ Expires", value=post_info['expiry_date'], inline=True)
    
    if post_info['invite_code']:
        embed.add_field(name="🎫 Invite Code", value=f"`{post_info['invite_code']}`", inline=False)
    
    if post_info['selftext'] and len(post_info['selftext']) > 0:
        # Truncate long text
        text = post_info['selftext'][:500]
        if len(post_info['selftext']) > 500:
            text += "..."
        embed.add_field(name="Details", value=text, inline=False)
    
    if post_info['url'] != post_info['permalink']:
        embed.add_field(name="🔗 Direct Link", value=post_info['url'], inline=False)
    
    embed.set_footer(text="From r/OpenSignups • React quickly!")
    
    # Get all users subscribed to reddit notifications (using "REDDIT" as a special tracker code)
    subscribers = []
    for user_id, user_trackers in subscriptions.items():
        if "REDDIT" in user_trackers:
            subscribers.append(f"<@{user_id}>")
    
    if subscribers:
        mention_text = " ".join(subscribers)
        await channel.send(f"{mention_text}", embed=embed)
    else:
        await channel.send(embed=embed)

async def monitor_trackers():
    """Main monitoring loop"""
    global last_check_time
    
    while True:
        try:
            logger.info("Checking tracker signups and Reddit...")
            last_check_time = datetime.now(timezone.utc)
            
            async with aiohttp.ClientSession() as session:
                # Check individual trackers
                for tracker_code, tracker_info in TRACKERS.items():
                    is_open = await check_tracker_signup(session, tracker_code, tracker_info)
                    previous_status = tracker_status.get(tracker_code, False)
                    
                    # If status changed from closed to open, notify subscribers
                    if is_open and not previous_status:
                        await notify_subscribers(tracker_code, tracker_info)
                    
                    tracker_status[tracker_code] = is_open
                    
                    # Small delay between checks to be respectful
                    await asyncio.sleep(2)
                
                # Check Reddit for new posts
                new_reddit_posts = await check_reddit_opensignups(session)
                for post_info in new_reddit_posts:
                    await notify_reddit_signup(post_info)
                    post_info['notified'] = True
            
            await save_data()
            logger.info(f"Check completed. Found {len(new_reddit_posts) if 'new_reddit_posts' in locals() else 0} new Reddit posts. Next check in {CHECK_INTERVAL} seconds.")
            
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
        timestamp=datetime.now(timezone.utc)
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
            name="Reddit Monitoring", 
            value="Use `!subscribe REDDIT` or `!unsubscribe REDDIT` for r/OpenSignups notifications", 
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
            timestamp=datetime.now(timezone.utc)
        )
        
        # Group by type
        trackers_by_type = {}
        for tracker_code, tracker_info in TRACKERS.items():
            tracker_type = tracker_info.get('type', 'tracker')
            if tracker_type not in trackers_by_type:
                trackers_by_type[tracker_type] = []
            
            status = "🟢 OPEN" if tracker_status.get(tracker_code, False) else "🔴 CLOSED"
            trackers_by_type[tracker_type].append({
                'code': tracker_code,
                'name': tracker_info['name'],
                'status': status,
                'description': tracker_info['description']
            })
        
        # Add trackers grouped by type
        for tracker_type, trackers in trackers_by_type.items():
            type_emoji = "🎬" if tracker_type == "tracker" else "📰"
            for tracker in trackers:
                embed.add_field(
                    name=f"{type_emoji} {tracker['code']} - {tracker['name']}",
                    value=f"Status: {tracker['status']}\nType: {tracker['description']}",
                    inline=True
                )
        
        # Add Reddit monitoring status
        embed.add_field(
            name="🔥 REDDIT - r/OpenSignups",
            value="Status: 🟢 MONITORING\nType: Reddit posts",
            inline=True
        )
        
        embed.set_footer(text=f"Last checked: {last_check_time.strftime('%Y-%m-%d %H:%M:%S UTC') if last_check_time else 'Never'}")
        await message.channel.send(embed=embed)
    
    # Subscribe to tracker
    elif content.startswith('!subscribe '):
        if len(args) < 2:
            await message.channel.send("❌ Please specify a tracker code. Example: `!subscribe RED` or `!subscribe REDDIT`")
            return
        tracker_code = args[1].upper()
        
        if tracker_code not in TRACKERS and tracker_code != "REDDIT":
            await message.channel.send(f"❌ Unknown tracker: {tracker_code}\nUse `!trackers` to see available trackers or use `REDDIT` for r/OpenSignups.")
            return
        
        user_id = message.author.id
        if user_id not in subscriptions:
            subscriptions[user_id] = set()
        
        if tracker_code in subscriptions[user_id]:
            name = TRACKERS[tracker_code]['name'] if tracker_code in TRACKERS else "Reddit r/OpenSignups"
            await message.channel.send(f"ℹ️ You're already subscribed to {name}")
        else:
            subscriptions[user_id].add(tracker_code)
            await save_data()
            name = TRACKERS[tracker_code]['name'] if tracker_code in TRACKERS else "Reddit r/OpenSignups"
            await message.channel.send(f"✅ Subscribed to {name} notifications!")
    
    # Unsubscribe from tracker
    elif content.startswith('!unsubscribe '):
        if len(args) < 2:
            await message.channel.send("❌ Please specify a tracker code. Example: `!unsubscribe RED` or `!unsubscribe REDDIT`")
            return
        tracker_code = args[1].upper()
        
        if tracker_code not in TRACKERS and tracker_code != "REDDIT":
            await message.channel.send(f"❌ Unknown tracker: {tracker_code}")
            return
        
        user_id = message.author.id
        if user_id in subscriptions and tracker_code in subscriptions[user_id]:
            subscriptions[user_id].remove(tracker_code)
            if not subscriptions[user_id]:  # Remove empty subscription sets
                del subscriptions[user_id]
            await save_data()
            name = TRACKERS[tracker_code]['name'] if tracker_code in TRACKERS else "Reddit r/OpenSignups"
            await message.channel.send(f"✅ Unsubscribed from {name} notifications!")
        else:
            name = TRACKERS[tracker_code]['name'] if tracker_code in TRACKERS else "Reddit r/OpenSignups"
            await message.channel.send(f"ℹ️ You're not subscribed to {name}")
    
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
                if tracker_code == "REDDIT":
                    embed.add_field(
                        name="🔥 REDDIT - r/OpenSignups",
                        value="Status: 🟢 MONITORING",
                        inline=True
                    )
                else:
                    tracker_info = TRACKERS[tracker_code]
                    status = "🟢 OPEN" if tracker_status.get(tracker_code, False) else "🔴 CLOSED"
                    type_emoji = "🎬" if tracker_info.get('type') == "tracker" else "📰"
                    embed.add_field(
                        name=f"{type_emoji} {tracker_code} - {tracker_info['name']}",
                        value=f"Status: {status}",
                        inline=True
                    )
            
            await message.channel.send(embed=embed)
    
    # Bot status
    elif content == '!status':
        embed = discord.Embed(
            title="Bot Status",
            color=0x0099ff,
            timestamp=datetime.now(timezone.utc)
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
        embed.add_field(
            name="Reddit Posts Tracked",
            value=str(len(reddit_posts)),
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
