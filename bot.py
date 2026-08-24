import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="/", intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} is online and ready!")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, name="/help"
    ))
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


async def setup_hook():
    await bot.load_extension("cogs.gif_commands")
    await bot.load_extension("cogs.music")
    await bot.load_extension("cogs.fun")


bot.setup_hook = setup_hook

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("ERROR: No DISCORD_TOKEN found in .env file!")
        print("Create a .env file with: DISCORD_TOKEN=your_bot_token_here")
    else:
        bot.run(token)
