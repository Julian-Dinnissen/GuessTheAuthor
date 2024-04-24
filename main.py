import discord
import os
from dotenv import load_dotenv
import json
import random

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
JULIAN_CHANNEL = os.getenv("JULIAN_CHANNEL")
GAME_CHANNEL = os.getenv("GAME_CHANNEL")

intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.members = True
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    # get guild by id stored in GUILD


class Message:
    def __init__(self, author, content, date, channel, reply):
        self.author = author
        self.content = content
        self.date = date
        self.channel = channel
        self.reply = reply

    def __str__(self):
        return f"{self.author} said {self.content} on {self.date} in {self.channel}"

    def __repr__(self):
        return f"{self.author} said {self.content} on {self.date} in {self.channel}"


async def get_guild() -> discord.Guild:
    global GUILD
    guild = client.get_guild(int(GUILD))
    return guild


async def get_channel() -> discord.TextChannel:
    global GAME_CHANNEL
    guild = await get_guild()
    channel = guild.get_channel(int(GAME_CHANNEL))
    return channel


async def message_to_json(message: discord.Message) -> None:
    date = message.created_at.strftime("%d-%m-%Y %H:%M:%S")
    author_name = message.author.display_name
    message.content = await get_image(message)

    try:
        # Read existing messages from the JSON file
        with open("./data/messages.json", "r") as f:
            messages = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        # If the file doesn't exist or is empty, initialize messages as an empty list
        messages = []

    # Get the ID of the last message, or set it to 0 if there are no messages
    last_id = messages[-1]["id"] if messages else 0

    # Increment the ID for the new message
    new_id = last_id + 1

    message_dict = {
        "id": new_id,
        "author": author_name,
        "content": message.content,
        "date": date,
        "channel": message.channel.name,
        "reply": message.reference.resolved.content if message.reference else None,
    }

    # Append the new message to the list
    messages.append(message_dict)

    # Write the updated list back to the JSON file
    with open("./data/messages.json", "w") as f:
        json.dump(messages, f, indent=4)  # Optional: indent for better readability


async def get_image(message: discord.Message) -> discord.Message.content:
    if message.attachments:
        for attachment in message.attachments:
            message.content = message.content + " " + attachment.url

        return message.content
    else:
        return message.content


async def scrape_messages(channel: discord.TextChannel):
    async for message in channel.history(limit=None):
        if (
            len(message.content.split()) > 3
            and not message.author.bot
            or message.attachments
        ):
            await message_to_json(message)


def get_random_message():
    with open("./data/messages.json", "r") as f:
        messages = json.load(f)

    random_message = random.choice(messages)
    # get the id of the random message
    random_id = random_message["id"]
    previous_message = messages[random_id - 2]
    if random_id + 1 >= len(messages):
        next_message = "Wow, such empty"
    else:
        next_message = messages[random_id]

    return random_message, previous_message, next_message


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    game_c = await get_channel()

    if message.channel == game_c:
        if (
            len(message.content.split()) > 3
            and not message.author.bot
            or message.attachments
        ):
            await message_to_json(message)

    # the image one
    if message.content.startswith("!image"):
        await message.channel.send(await get_image(message))

    if message.content.startswith("!scrape"):
        await scrape_messages(game_c)

    if message.content.startswith("!random"):
        for i in get_random_message():
            await message.channel.send(i)


client.run(TOKEN)
