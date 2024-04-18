import discord
import os
import dotenv
import requests
import json

dotenv.load_dotenv()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

maximum_request_message_length = 10000


@client.event
async def on_ready():
    print("we have logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user = message.author  # Fetch the user who sent the message
    server_name = message.guild.name
    channel_name = message.channel.name

    channel = message.channel

    accumulated_string = ""

    async for fetched_message in channel.history(limit=None):
        if (
            len(accumulated_string) + len(fetched_message.content)
            > maximum_request_message_length
        ):
            break

        accumulated_string += fetched_message.content
        accumulated_string += "\n"

    request = f"Message sent by: {user.name}\nServer: {server_name}\nChannel: {channel_name}\n\n{accumulated_string}"
    await user.send(request)


client.run(os.getenv("DISCORD_TOKEN"))
