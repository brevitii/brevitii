import discord
import os
from config import MAXIMUM_GEMINI_REQUEST_MESSAGE_LENGTH, MAXIMUM_MESSAGES_COLLECTION_LENGTH, MAXIMUM_MESSAGES_COLLECTION_BATCH_SIZE, MAXIMUM_DISCORD_MESSAGE_LENGTH

import google.generativeai as genai

genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

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

  author_name = m_author.name  # Discord username
  author_global_name = m_author.global_name
  server_name = m_guild.name
  channel_name = m_channel.name

  # Skip messages that are empty
  # This happens if the message is an embed or an attachment
  # TODO: Don't skip messages with attachments
  if m_content == '':
    print('Empty message content')
    return

  if not m_content.startswith('$brief'):
    print('Message is not for Brevity')
    return

  # Split message content by spaces
  args = m_content.split()

  # Check if the user provided more than one argument
  if len(args) > 2:
    await m_channel.send('Please provide exactly one argument, '
                         'which is the number of messages to abbreviate.\n'
                         'Example: `$brief 5`\n')
    return

  num_messages = None

  if len(args) > 1:
    num_messages = args[1]

  await m_channel.send(
      'Cool {}! I will send you the abbreviation of the last {} messages in private.'
      .format(author_global_name, num_messages))

  # Get the directory of the current script
  script_dir = os.path.dirname(os.path.realpath(__file__))
  prompt_body_file_path = os.path.join(script_dir, 'prompt_body.txt')

  # Collect the last `num_messages` messages
  await collect_messages_and_build_prompt(m_channel, prompt_body_file_path,
                                          num_messages)

  ##############################################
  #
  # Send the abbreviation to the user
  #
  ##############################################

  prompt_header_file_path = os.path.join(script_dir, 'prompt_header.txt')

  # Read the header
  with open(prompt_header_file_path, 'rb') as file:
    prompt_header = file.read().decode('utf-8')

  # Read the body
  with open(prompt_body_file_path, 'rb') as file:
    prompt_body = file.read().decode('utf-8')

  greeting_sentence = 'Hello Gemini!  My name is {}.\n\n'.format(author_name)
  end_sentence = '\n\nConversation ends NOW'

  prompt = greeting_sentence + '{}\n\n'.format(
      prompt_header) + prompt_body + end_sentence

  # Save the full prompt to a file
  with open(os.path.join(script_dir, 'prompt.txt'), 'w') as file:
    file.write(prompt)

  # Currently, we are supporting the text only model
  model = genai.GenerativeModel('gemini-pro')

  response = model.generate_content(prompt)

  brevity_response = 'Here is the abbreviation of the last {} messages in the "{}" channel of the "{}" server:\n\n' \
                  '{}'.format(num_messages, channel_name, server_name, response.text)

  # Without Discord nitro, the maximum message length is 2000 characters. We need to split the message into multiple messages.
  # With Discord nitro, the maximum message length is 4000 characters.
  if len(brevity_response) > MAXIMUM_DISCORD_MESSAGE_LENGTH:
    # Split the message into multiple messages
    # https://stackoverflow.com/questions/9475241/split-python-string-every-nth-character
    for i in range(0, len(brevity_response), MAXIMUM_DISCORD_MESSAGE_LENGTH):
      await m_author.send(brevity_response[i:i +
                                           MAXIMUM_DISCORD_MESSAGE_LENGTH])
  else:
    await m_author.send(brevity_response)


async def collect_messages_and_build_prompt(m_channel: discord.TextChannel,
                                            prompt_body_file_path,
                                            num_messages: int = None):
  if not num_messages:
    num_messages = MAXIMUM_MESSAGES_COLLECTION_LENGTH

  m_channel_history = m_channel.history(limit=int(num_messages))

  def write_prompt_to_file(collected_msgs: list,
                           prompt_body_file_path) -> None:
    with open(prompt_body_file_path, 'a') as file:
      for collected_msg in collected_msgs:
        collected_msg_author = collected_msg.author

        if collected_msg.reference and collected_msg.reference.resolved:
          referenced_msg = collected_msg.reference.resolved
          referenced_msg_author = referenced_msg.author
          file.write('{}" (responds to {}): {}\n'.format(
              collected_msg_author.name, referenced_msg_author.name,
              collected_msg.content))
          continue

        file.write('{}: {}\n'.format(collected_msg_author.name,
                                     collected_msg.content))

  collected_msgs = []
  async for msg in m_channel_history:
    # Skip messages sent by Brevity
    if msg.author == client.user:
      continue

    # Skip messages that are empty
    # This happens if the message is an embed or an attachment
    # TODO: Don't skip messages with attachments
    if msg.content == '':
      continue

    collected_msgs.append(msg)

    # Write to file every MAXIMUM_MESSAGES_COLLECTION_BATCH_SIZE messages collected
    if len(collected_msgs) == MAXIMUM_MESSAGES_COLLECTION_BATCH_SIZE:
      write_prompt_to_file(collected_msgs, prompt_body_file_path)
      collected_msgs.clear()

  # Write any remaining messages to file
  if len(collected_msgs) > 0:
    write_prompt_to_file(collected_msgs, prompt_body_file_path)
    collected_msgs.clear()
    del collected_msgs


# Run Brevity client.
client.run(os.environ['DISCORD_TOKEN'])
