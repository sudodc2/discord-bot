import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput
from datetime import datetime, timezone
import random


CURSE_WORDS = {
    "fuck",
    "shit",
    "bitch",
    "ass",
    "damn",
    "hell",
    "wtf",
    "mf",
    "bullshit",
    "dick",
}


CURSE_LINES = [
    "{user} has cursed once. seems like a beginner at this stuff.",
    "{user} is warming up. foul mouth stocks are rising.",
    "{user} is getting way too comfortable swearing in here.",
    "{user} might actually be allergic to clean language.",
    "{user} is speaking fluent toxicity now.",
    "{user} needs soap, prayer, and maybe supervision.",
]


LATE_NIGHT_LINES = [
    "{user} it's late as hell. go to sleep.",
    "{user} being awake right now is nasty work.",
    "{user} is beefing with sleep again.",
    "{user} has entered goblin hours.",
]


REP_COOLDOWNS = {}


class ConfessionModal(Modal, title="Send an anonymous confession"):
    confession = TextInput(
        label="Your confession",
        style=discord.TextStyle.paragraph,
        max_length=1500,
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.handle_confession(
            interaction,
            str(self.confession),
        )


class Community(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def storage(self):
        return self.bot.get_cog("Storage")

    async def refresh_curse_board(self, guild):
        store = self.storage()
        guild_data = store.get_guild(guild.id)

        channel_id = guild_data["channels"].get("curse")
        message_id = guild_data.get("curse_message_id")

        if not channel_id or not message_id:
            return

        channel = guild.get_channel(channel_id)

        if not channel:
            return

        try:
            message = await channel.fetch_message(message_id)
        except Exception:
            return

        users = store.cache["users"].get(str(guild.id), {})

        ranked = sorted(
            users.items(),
            key=lambda item: item[1].get("curse_count", 0),
            reverse=True,
        )[:10]

        embed = discord.Embed(
            title="🤬 Curse Leaderboard",
            description="live shameboard",
            color=discord.Color.red(),
        )

        if not ranked:
            embed.description = "Nobody has cursed yet. weirdly wholesome."

        for index, (_, data) in enumerate(ranked, 1):
            embed.add_field(
                name=f"#{index} {data.get('display_name', 'Unknown')}",
                value=f"{data.get('curse_count', 0)} curses",
                inline=False,
            )

        await message.edit(embed=embed)

    async def handle_confession(self, interaction, text):
        store = self.storage()
        guild_data = store.get_guild(interaction.guild.id)

        confession_channel_id = guild_data["channels"].get("confessions")
        log_channel_id = guild_data["channels"].get("confession_logs")

        confession_channel = interaction.guild.get_channel(
            confession_channel_id
        )
        log_channel = interaction.guild.get_channel(log_channel_id)

        if not confession_channel or not log_channel:
            await interaction.response.send_message(
                "Confession channels aren't set up yet.",
                ephemeral=True,
            )
            return

        public_embed = discord.Embed(
            title="Anonymous Confession",
            description=text,
            color=discord.Color.dark_purple(),
        )
        public_embed.set_footer(
            text="React however you want. I won't judge. much."
        )

        public_message = await confession_channel.send(
            embed=public_embed
        )

        for emoji in ["👍", "👎", "😭", "💀"]:
            await public_message.add_reaction(emoji)

        log_embed = discord.Embed(
            title="Confession Log",
            description=text,
            color=discord.Color.gold(),
            timestamp=datetime.now(timezone.utc),
        )

        log_embed.add_field(
            name="Username",
            value=interaction.user.name,
            inline=True,
        )
        log_embed.add_field(
            name="Display name",
            value=interaction.user.display_name,
            inline=True,
        )
        log_embed.add_field(
            name="User ID",
            value=str(interaction.user.id),
            inline=False,
        )
        log_embed.set_thumbnail(
            url=interaction.user.display_avatar.url
        )

        await log_channel.send(embed=log_embed)

        await interaction.response.send_message(
            "sent. your secret is ugly but safe.",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        store = self.storage()

        user = store.get_user(
            member.guild.id,
            member.id,
            member.display_name,
            member.name,
            str(member.display_avatar.url),
        )

        if user.get("join_count", 1) >= 1 and user.get("xp", 0) > 0:
            user["rejoined"] = True
            user["join_count"] = user.get("join_count", 1) + 1
        else:
            user["join_count"] = user.get("join_count", 0) + 1

        store.save("users")

        guild_data = store.get_guild(member.guild.id)
        channel_id = guild_data["channels"].get("welcome")

        channel = (
            member.guild.get_channel(channel_id)
            if channel_id
            else None
        )

        if not channel:
            return

        embed = discord.Embed(
            title="Welcome",
            color=discord.Color.blurple(),
        )

        embed.description = (
            f"welcome {member.mention} to "
            f"**{member.guild.name}**"
        )

        embed.add_field(
            name="Username",
            value=member.name,
        )
        embed.add_field(
            name="Display",
            value=member.display_name,
        )
        embed.add_field(
            name="Rejoined",
            value="yes" if user.get("rejoined") else "no",
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        image_url = guild_data.get("welcome_image_url")

        if image_url:
            embed.set_image(url=image_url)

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        store = self.storage()

        user = store.get_user(
            message.guild.id,
            message.author.id,
            message.author.display_name,
            message.author.name,
            str(message.author.display_avatar.url),
        )

        guild_data = store.get_guild(message.guild.id)

        trap_channel_id = guild_data["channels"].get("trap")

        if (
            trap_channel_id
            and message.channel.id == trap_channel_id
        ):
            if (
                message.author == message.guild.owner
                or message.author.guild_permissions.administrator
            ):
                return

            try:
                await message.author.ban(
                    reason="Typed in do-not-text-here trap channel"
                )
                await message.channel.send(
                    f"{message.author.mention} got cooked for not reading."
                )
            except Exception:
                pass

            return

        user["xp"] += random.randint(8, 15)

        next_level = user["level"] * 120

        if user["xp"] >= next_level:
            user["level"] += 1

            level_channel_id = guild_data["channels"].get("levels")
            level_channel = (
                message.guild.get_channel(level_channel_id)
                if level_channel_id
                else None
            )

            if level_channel:
                embed = discord.Embed(
                    title="Level Up",
                    description=(
                        f"{message.author.mention} hit "
                        f"**level {user['level']}**"
                    ),
                    color=discord.Color.green(),
                )

                embed.set_thumbnail(
                    url=message.author.display_avatar.url
                )

                await level_channel.send(embed=embed)

        hour = datetime.now().hour

        if 3 <= hour <= 5 and random.random() < 0.12:
            user["night_streak"] = user.get("night_streak", 0) + 1

            line = random.choice(LATE_NIGHT_LINES)

            await message.channel.send(
                line.format(user=message.author.mention)
            )

        punctuation = "!?.,:;()[]{}\"'`"

        words = {
            word.strip(punctuation).lower()
            for word in message.content.split()
        }

        if words & CURSE_WORDS:
            user["curse_count"] += 1

            count = user["curse_count"]
            index = min(
                (count - 1) // 3,
                len(CURSE_LINES) - 1,
            )

            line = CURSE_LINES[index].format(
                user=message.author.mention
            )

            await message.channel.send(line)
            await self.refresh_curse_board(message.guild)

        store.save("users")

        await self.bot.process_commands(message)

    @app_commands.command(
        name="confess",
        description="Send an anonymous confession",
    )
    async def confess(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            ConfessionModal(self)
        )

    @app_commands.command(
        name="curseboard",
        description="Show the curse leaderboard",
    )
    async def curseboard(self, interaction: discord.Interaction):
        store = self.storage()

        users = store.cache["users"].get(
            str(interaction.guild.id),
            {},
        )

        ranked = sorted(
            users.items(),
            key=lambda item: item[1].get("curse_count", 0),
            reverse=True,
        )[:10]

        embed = discord.Embed(
            title="🤬 Curse Leaderboard",
            color=discord.Color.red(),
        )

        if not ranked:
            embed.description = "Nobody has cursed yet. fake server."

        for index, (_, data) in enumerate(ranked, 1):
            embed.add_field(
                name=f"#{index} {data.get('display_name', 'Unknown')}",
                value=f"{data.get('curse_count', 0)} curses",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="daily",
        description="Claim your daily coins",
    )
    async def daily(self, interaction: discord.Interaction):
        from datetime import date

        store = self.storage()

        user = store.get_user(
            interaction.guild.id,
            interaction.user.id,
            interaction.user.display_name,
            interaction.user.name,
            str(interaction.user.display_avatar.url),
        )

        today = str(date.today())

        if user.get("last_daily") == today:
            await interaction.response.send_message(
                "you already claimed today. greed is ugly.",
                ephemeral=True,
            )
            return

        user["daily_streak"] = user.get("daily_streak", 0) + 1

        reward = 100 + (user["daily_streak"] * 10)

        user["coins"] += reward
        user["last_daily"] = today

        store.save("users")

        await interaction.response.send_message(
            f"claimed **{reward}** coins. "
            f"streak: **{user['daily_streak']}**"
        )

    @app_commands.command(
        name="rep",
        description="Give someone reputation",
    )
    async def rep(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ):
        if user.id == interaction.user.id:
            await interaction.response.send_message(
                "rep yourself? loser move.",
                ephemeral=True,
            )
            return

        key = f"{interaction.guild.id}:{interaction.user.id}"
        today = datetime.utcnow().date().isoformat()

        if REP_COOLDOWNS.get(key) == today:
            await interaction.response.send_message(
                "you already gave rep today.",
                ephemeral=True,
            )
            return

        store = self.storage()

        target = store.get_user(
            interaction.guild.id,
            user.id,
            user.display_name,
            user.name,
            str(user.display_avatar.url),
        )

        target["rep"] += 1

        store.save("users")

        REP_COOLDOWNS[key] = today

        await interaction.response.send_message(
            f"{user.mention} got **+1 rep**"
        )

    @app_commands.command(
        name="profile",
        description="Show a user's server profile",
    )
    async def profile(
        self,
        interaction: discord.Interaction,
        user: discord.Member = None,
    ):
        user = user or interaction.user

        store = self.storage()

        data = store.get_user(
            interaction.guild.id,
            user.id,
            user.display_name,
            user.name,
            str(user.display_avatar.url),
        )

        embed = discord.Embed(
            title=f"{user.display_name}'s profile",
            color=discord.Color.purple(),
        )

        embed.set_thumbnail(
            url=user.display_avatar.url
        )

        embed.add_field(
            name="Level",
            value=data.get("level", 1),
        )
        embed.add_field(
            name="XP",
            value=data.get("xp", 0),
        )
        embed.add_field(
            name="Coins",
            value=data.get("coins", 0),
        )
        embed.add_field(
            name="Rep",
            value=data.get("rep", 0),
        )
        embed.add_field(
            name="Curses",
            value=data.get("curse_count", 0),
        )
        embed.add_field(
            name="Join Date",
            value=(
                user.joined_at.strftime("%b %d, %Y")
                if user.joined_at
                else "Unknown"
            ),
            inline=False,
        )
        embed.add_field(
            name="Age",
            value=data.get("age") or "Not set",
            inline=True,
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Community(bot))
