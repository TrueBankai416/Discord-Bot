# discord_bot.py
import discord
import os

# Create a client instance for the bot
intents = discord.Intents.default()
intents.message_content = True # Enables reading messages
intents.messages = True  # Ensure this is enabled
intents.guild_messages = True  # Enables receiving messages in guilds
#intents.direct_messages = True  # Enables receiving direct messages
permissions = discord.Permissions(permissions=274877992000)
permissions.read_messages = True
client = discord.Client(intents=intents)

# The ID of the channel you want the bot to listen to
TARGET_CHANNEL_ID = 1225523691551723720  # Replace this with the actual channel ID
# State to remember if we're waiting for a reverse proxy response from a user
awaiting_reverse_proxy_response = {}
# Dictionary mapping keywords to responses
KEYWORD_RESPONSES = {
    "hello": "Hello! How can I help you today?",
    "help": "Sure, what do you need help with?",
    "migrate": "Hello! Documentation can be found here. https://docs.nextcloud.com/server/latest/admin_manual/maintenance/migrating.html",
    "reverse proxy": "Hello! Documentation can be found here. https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/reverse_proxy_configuration.html",
    "occ": "Hello! Documentation can be found here. https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/occ_command.html",
    # Add more keywords and responses as needed
}

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
@client.event
async def on_message(message):
    global awaiting_reverse_proxy_response
    # Don't let the bot respond to its own messages
    if message.author == client.user:
        return

    # Check if the message is in the target channel
    if message.channel.id == TARGET_CHANNEL_ID or client.user.mentioned_in(message):
        # Check each keyword in the message
        if "reverse proxy" in message.content.lower():
            await message.channel.send("Which reverse proxy are you using? (e.g., Nginx, Apache, Caddy)")
            awaiting_reverse_proxy_response[message.author.id] = True
            return
        for keyword, response in KEYWORD_RESPONSES.items():
            if keyword in message.content.lower():
                await message.channel.send(response)
                break  # Stop checking after the first keyword match

    # Check if we're waiting for a reverse proxy response
    if awaiting_reverse_proxy_response.get(message.author.id):
        reverse_proxy = message.content.lower()
        response = f"Looks like you're using {reverse_proxy}. Here's a helpful link: "
        if "nginx" in reverse_proxy:
            response += "https://nginx.org/en/docs/\n\nMy example can be found here. https://github.com/TrueBankai416/Discord-Bot/blob/main/nextcloud_nginx.conf"
        elif "apache" in reverse_proxy:
            response += "https://httpd.apache.org/docs/\n\nMy example can be found here. https://github.com/TrueBankai416/Discord-Bot/blob/main/apache.conf"
        elif "caddy" in reverse_proxy:
            response += "https://caddyserver.com/docs/\n\nMy example can be found here. https://github.com/TrueBankai416/Discord-Bot/blob/main/Caddyfile\n\nHelpful video provided by DemonWarrior https://www.youtube.com/watch?v=zCyx4vmp4k0\nCaddy starts at timestamp 5:00:00"
        else:
            response = "Sorry, I don't have specific information on that reverse proxy."
        await message.channel.send(response)
        awaiting_reverse_proxy_response[message.author.id] = False
        return

    else:
        # Optionally, handle messages sent in other channels or do nothing
        pass

# Replace 'your_token_here' with your bot's actual token
client.run('CHANGE_ME')
