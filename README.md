# Discord Bot

A public Discord bot with meme/GIF creation, music playback, and fun commands. No hidden commands, everything is available to all server members.

## Features

### GIF & Meme Commands
- `/gif image:` - Convert any image to GIF format
- `/gif image: text:` - Create a meme with white caption bar on top (bold text) and your image below
- `/caption image: text:` - Same as above, dedicated meme maker

### Music Player
- `/play query` - Play a song (YouTube search or URL)
- `/skip` - Skip current song
- `/stop` - Stop playback, clear queue, and disconnect
- `/queue` - View the current queue
- `/pause` - Pause playback
- `/resume` - Resume playback
- `/nowplaying` - Show current song info
- `/loop` - Toggle loop on current song

### Fun & Utility
- `/avatar [user]` - Get anyone's avatar
- `/serverinfo` - Server stats
- `/userinfo [user]` - User profile info
- `/8ball question` - Magic 8-ball
- `/poll question option1 option2 [option3] [option4]` - Create a poll
- `/coinflip` - Flip a coin
- `/roll [sides]` - Roll dice

## Setup

### Prerequisites
- Python 3.10+
- FFmpeg installed on your system
- A Discord bot token

### Installation

1. Clone the repo:
```bash
git clone https://github.com/sudodc2/discord-bot.git
cd discord-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
   - **Ubuntu/Debian:** `sudo apt install ffmpeg`
   - **macOS:** `brew install ffmpeg`
   - **Windows:** Download from https://ffmpeg.org/download.html and add to PATH

4. Create a `.env` file:
```bash
cp .env.example .env
```
Then paste your bot token in the `.env` file.

5. Run the bot:
```bash
python bot.py
```

### Getting a Bot Token

1. Go to https://discord.com/developers/applications
2. Click "New Application" and name it
3. Go to "Bot" tab and click "Reset Token" to get your token
4. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
5. Go to "OAuth2" > "URL Generator"
   - Check `bot` and `applications.commands`
   - Under Bot Permissions, check: Send Messages, Embed Links, Attach Files, Connect, Speak, Use Slash Commands
6. Use the generated URL to invite the bot to your server

### Hosting (Free Options)
- **Railway.app** - Free tier available
- **Render.com** - Free tier with limitations
- **Oracle Cloud** - Always Free tier VPS
- **Your own PC** - Just keep it running

## License

MIT - Do whatever you want with it.
