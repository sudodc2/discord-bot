import discord
from discord.ext import commands
from datetime import datetime


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_buckets = {}

    def storage(self):
        return self.bot.get_cog("Storage")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        store = self.storage()
        guild_data = store.get_guild(message.guild.id)
        user = store.get_user(message.guild.id, message.author.id, message.author.display_name, message.author.name, str(message.author.display_avatar.url))

        # Spam detection
        key = (message.guild.id, message.author.id)
        now = datetime.utcnow().timestamp()
        bucket = self.message_buckets.get(key, [])
        bucket = [t for t in bucket if now - t < 7]
        bucket.append(now)
        self.message_buckets[key] = bucket

        if len(bucket) >= 6:
            if message.author == message.guild.owner or message.author.guild_permissions.administrator:
                return
            strikes = user.get("spam_strikes", 0)
            try:
                if strikes < 2:
                    await message.author.timeout(discord.utils.utcnow() + discord.utils.timedelta(seconds=10), reason="Spam detected")
                    user["spam_strikes"] = strikes + 1
                    embed = discord.Embed(title="Spam timeout", description=f"{message.author.mention} got a 10 second timeout for spamming.", color=discord.Color.orange())
                    embed.add_field(name="Username", value=message.author.name)
                    embed.add_field(name="Display", value=message.author.display_name)
                    embed.set_thumbnail(url=message.author.display_avatar.url)
                    await message.channel.send(embed=embed)
                else:
                    warning = await message.channel.send(f"{message.author.mention} quit spamming. next step is owner decision, not me.")
                    async for msg in message.channel.history(limit=20):
                        if msg.author.id == message.author.id:
                            try:
                                await msg.delete()
                            except:
                                pass
            except:
                pass
            store.save("users")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
