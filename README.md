# Brevitii Bot

> [!IMPORTANT]
> Here is the invite link: https://discord.com/oauth2/authorize?client_id=1230505478967005224&permissions=68608&scope=bot

# Usage

You can call Brevitii by ``$brief`` and then tell her how many messages you want to abbreviate. For example:

```
$brief 10000
```

# Compiling

Create a .env file that contains the following:

```
DISCORD_TOKEN=
GOOGLE_API_KEY=
```

then download the dependencies:

```bash
pip install -r requirements.txt
```

then run using:

```bash
python brevitii.py
```

# Improving Gemini's prompt for Brevitii

See [Prompting Intro](https://ai.google.dev/gemini-api/docs/prompting-intro) by Google.
