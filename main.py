import discord
import os
import dotenv
import requests
import json
from config import MAXIMUM_REQUEST_MESSAGE_LENGTH, MAXIMUM_MESSAGES_COLLECTION_LENGTH, MAXIMUM_MESSAGES_COLLECTION_BATCH_SIZE

intents = discord.Intents.default()

# This intent is also enabled on the Discord Developer Portal: https://discord.com/developers/applications/
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('We have logged in as {}'.format(client.user))

@client.event
async def on_message(message) -> None:
    # We only need brevity to respond to our own messages but not her own.
    # We do this by checking if the Message.author is the same as the Client.user.
    if message.author == client.user:
        return
    
    m_author: discord.User = message.author
    m_guild: discord.Guild = message.guild
    # Check https://discordpy.readthedocs.io/en/stable/api.html#discord.TextChannel for more information on TextChannel
    m_channel: discord.TextChannel = message.channel
    m_content: str = message.content

    author_name = m_author.name
    server_name = m_guild.name
    channel_name = m_channel.name

    if not m_content:
        print('Empty message content')
        return

    if not m_content.startswith('$brief'):
        print('Message is not for Brevity')
        return
    
    # Split message content by spaces
    args = m_content.split()

    # Check if the user provided more than one argument
    if len(args) > 2:
        await m_channel.send(
            'Please provide exactly one argument, '
            'which is the number of messages to abbreviate.\n'
            'Example: `$brief 5`\n'
        )
        return
    
    num_messages = None
    
    if len(args) > 1:
        num_messages = args[1]

    await m_channel.send('Cool! I will send you the abbreviation of the last {} messages in private.'.format(num_messages))

    # Collect the last `num_messages` messages
    await collect_messages_and_build_prompt(m_channel, num_messages)

    # Send the abbreviation to the user
    await m_author.send(
        'Hey {}, here is the abbreviation of the last {} messages in the {} channel of the {} server.'.format(author_name, num_messages, channel_name, server_name)
    )

async def collect_messages_and_build_prompt(m_channel: discord.TextChannel, num_messages: int = None):
    if not num_messages:
        num_messages = MAXIMUM_MESSAGES_COLLECTION_LENGTH

    m_channel_history = m_channel.history(limit=int(num_messages))

    def write_prompt_to_file(collected_msgs: list) -> None:
        with open('request_prompt.txt', 'a') as file:
            for collected_msg in collected_msgs:
                if collected_msg.reference and collected_msg.reference.resolved:
                    referenced_msg = collected_msg.reference.resolved
                    file.write(f'"{collected_msg.author}" responds to "{referenced_msg.author}" with "{collected_msg.content}"\n')
                else:
                    file.write(f'"{collected_msg.author}" says "{collected_msg.content}"\n')

    collected_msgs = []
    async for msg in m_channel_history:
        # Skip messages sent by Brevity
        if msg.author == client.user:
            continue

        collected_msgs.append(msg)

        # Write to file every MAXIMUM_MESSAGES_COLLECTION_BATCH_SIZE messages collected
        if len(collected_msgs) == MAXIMUM_MESSAGES_COLLECTION_BATCH_SIZE:
            write_prompt_to_file(collected_msgs)
            collected_msgs.clear()

    # Write any remaining messages to file
    if len(collected_msgs) > 0:
        write_prompt_to_file(collected_msgs)
        collected_msgs.clear()
        del collected_msgs

dotenv.load_dotenv()

# Run Brevity client.
client.run(os.getenv("DISCORD_TOKEN"))
