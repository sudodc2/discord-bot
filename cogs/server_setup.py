import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput

LAYOUT = [
    ("═══ ✨ ・ INFO ・ ✨ ═══", [
        ("📋┃commands", "commands"),
        ("👋┃welcome", "welcome"),
        ("📢┃announcements", "announcements"),
        ("🎂┃set-age", "set_age"),
    ]),
    ("═══ 💬 ・ COMMUNITY ・ 💬 ═══", [
        ("💬┃chat", "chat"),
        ("🖼️┃images", "images"),
        ("🎬┃clips", "clips"),
        ("🎭┃confessions", "confessions"),
    ]),
    ("═══ 🏆 ・ STATS ・ 🏆 ═══", [
        ("🤬┃curse-leaderboard", "curse"),
        ("📈┃levels", "levels"),
    ]),
    ("═══ 🎵 ・ MUSIC ・ 🎵 ═══", [
        ("🎶┃music-cmds", "music_cmds"),
        ("🔊┃Music", "vc_music", "voice"),
        ("🔊┃Hangout", "vc_hangout", "voice"),
        ("🔊┃Sleep", "vc_sleep", "voice"),
    ]),
    ("═══ 🎮 ・ FUN ・ 🎮 ═══", [
        ("🎰┃economy", "economy"),
        ("🎲┃games", "games"),
    ]),
    ("═══ 🔒 ・ ADMIN ・ 🔒 ═══", [
        ("🔐┃admin", "admin"),
        ("🕵️┃confession-logs", "confession_logs"),
    ]),
    ("═══ ⚠️ ・ DANGER ・ ⚠️ ═══", [
        ("⛔┃do-not-text-here", "trap"),
    ]),
]

EXPLAINERS = {
    "commands": "This channel explains every bot command. Use it when you're confused instead of freeballing it.",
    "welcome": "Welcome messages and cards show up here.",
    "announcements": "Important server updates belong here.",
    "set_age": "Use `/age <number>` with your real age. This helps with server safety and makes your age visible on your profile.",
    "chat": "Main chat. Be normal. Or at least interesting.",
    "images": "Drop images here.",
    "clips": "Clips go here.",
    "confessions": "Use `/confess` to post anonymously. Reactions decide if it was brave or embarrassing.",
    "curse": "Live curse leaderboard. Public shame, updated automatically.",
    "levels": "Level-up messages and XP progress show up here.",
    "music_cmds": "Use music commands here like `/play`, `/skip`, `/queue`, `/stop`.",
    "economy": "Daily, betting, robbing, shop stuff. Financial irresponsibility lives here.",
    "games": "Trivia, rps, numguess and other game commands go here.",
    "admin": "Private admin room for server management.",
    "confession_logs": "Private confession logs. Real identities behind anonymous confessions go here.",
    "trap": "Do not send anything here. No text, no images, no files. If you do, the bot will try to ban you instantly.",
}


class ReservedModal(Modal, title="Enter password to rebuild this server"):
    password = TextInput(label="Password", style=discord.TextStyle.short, required=True, max_length=100)

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.handle_reserved(interaction, str(self.password))


class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def storage(self):
        return self.bot.get_cog("Storage")

    async def safe_pin(self, channel, content):
        msg = await channel.send(content)
        try:
            await msg.pin()
        except:
            pass
        return msg

    async def rebuild_server(self, guild):
        store = self.storage()
        guild_data = store.get_guild(guild.id)

        # Delete channels
        for channel in list(guild.channels):
            try:
                await channel.delete(reason="Server rebuild via reserved command")
            except:
                pass

        # Age roles bucket role
        ages_parent_role = discord.utils.get(guild.roles, name="Ages")
        if not ages_parent_role:
            try:
                ages_parent_role = await guild.create_role(name="Ages", permissions=discord.Permissions.none(), reason="Age role bucket")
            except:
                pass

        guild_data["channels"] = {}
        guild_data["roles"] = {}

        admin_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        for role in guild.roles:
            if role.permissions.administrator:
                admin_overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)

        for category_name, items in LAYOUT:
            overwrites = None
            if "ADMIN" in category_name:
                overwrites = admin_overwrites
            category = await guild.create_category(category_name, overwrites=overwrites)
            for item in items:
                name, key = item[0], item[1]
                kind = item[2] if len(item) > 2 else "text"
                if kind == "voice":
                    channel = await guild.create_voice_channel(name, category=category)
                else:
                    perms = {
                        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True)
                    }
                    if key in {"admin", "confession_logs"}:
                        perms = admin_overwrites
                    channel = await guild.create_text_channel(name, category=category, overwrites=perms)
                    explainer = EXPLAINERS.get(key, "This channel exists for a reason.")
                    await self.safe_pin(channel, explainer)
                    if key == "trap":
                        await channel.send("Read the pinned message. Type here and you get banned if I can ban you.")
                    if key == "commands":
                        commands_text = (
                            "**Bot Commands**\n"
                            "`/gif` convert image to gif or make a meme caption\n"
                            "`/caption` meme caption image\n"
                            "`/play /skip /stop /queue /pause /resume /nowplaying /loop` music\n"
                            "`/confess` anonymous confession\n"
                            "`/curseboard` curse leaderboard\n"
                            "`/daily /rob /bet /rep /profile /age /trivia /rps /numguess /poll /avatar /serverinfo /userinfo /8ball /coinflip /roll /remindme /reserved`"
                        )
                        msg = await channel.send(commands_text)
                        try:
                            await msg.pin()
                        except:
                            pass
                        guild_data["commands_message_id"] = msg.id
                    if key == "curse":
                        embed = discord.Embed(title="🤬 Curse Leaderboard", description="live shameboard", color=discord.Color.red())
                        msg = await channel.send(embed=embed)
                        guild_data["curse_message_id"] = msg.id
                guild_data["channels"][key] = channel.id

        store.save("guilds")

    async def handle_reserved(self, interaction, password):
        store = self.storage()
        guild_data = store.get_guild(interaction.guild.id)
        if password != guild_data.get("password"):
            await interaction.response.send_message("wrong password. nice try.", ephemeral=True)
            return
        await interaction.response.send_message("starting full server wipe and rebuild. this is the fun part.", ephemeral=True)
        await self.rebuild_server(interaction.guild)

    @app_commands.command(name="reserved", description="Rebuild the server layout with the private password")
    async def reserved(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ReservedModal(self))

    @app_commands.command(name="age", description="Set your real age role")
    async def age(self, interaction: discord.Interaction, number: int):
        if number < 1 or number > 120:
            await interaction.response.send_message("put a real age, not nonsense.", ephemeral=True)
            return
        # remove old age roles
        for role in interaction.user.roles:
            if role.name.startswith("Age: "):
                try:
                    await interaction.user.remove_roles(role)
                except:
                    pass
        role_name = f"Age: {number}"
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if not role:
            role = await interaction.guild.create_role(name=role_name, permissions=discord.Permissions.none(), reason="Age role")
        await interaction.user.add_roles(role)
        store = self.storage()
        user = store.get_user(interaction.guild.id, interaction.user.id, interaction.user.display_name, interaction.user.name, str(interaction.user.display_avatar.url))
        user["age"] = number
        store.save("users")
        await interaction.response.send_message(f"✅ role assigned. you are **{number} years old**.")


async def setup(bot):
    await bot.add_cog(ServerSetup(bot))
