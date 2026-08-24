import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Modal, TextInput


LAYOUT = [
    (
        "═══ ✨ ・ INFO ・ ✨ ═══",
        [
            ("📋┃commands", "commands"),
            ("👋┃welcome", "welcome"),
            ("📢┃announcements", "announcements"),
            ("🎂┃set-age", "set_age"),
        ],
    ),
    (
        "═══ 💬 ・ COMMUNITY ・ 💬 ═══",
        [
            ("💬┃chat", "chat"),
            ("🖼️┃images", "images"),
            ("🎬┃clips", "clips"),
            ("🎭┃confessions", "confessions"),
        ],
    ),
    (
        "═══ 🏆 ・ STATS ・ 🏆 ═══",
        [
            ("🤬┃curse-leaderboard", "curse"),
            ("📈┃levels", "levels"),
        ],
    ),
    (
        "═══ 🎵 ・ MUSIC ・ 🎵 ═══",
        [
            ("🎶┃music-cmds", "music_cmds"),
            ("🔊┃Music", "vc_music", "voice"),
            ("🔊┃Hangout", "vc_hangout", "voice"),
            ("🔊┃Sleep", "vc_sleep", "voice"),
        ],
    ),
    (
        "═══ 🎮 ・ FUN ・ 🎮 ═══",
        [
            ("🎰┃economy", "economy"),
            ("🎲┃games", "games"),
        ],
    ),
    (
        "═══ 🔒 ・ ADMIN ・ 🔒 ═══",
        [
            ("🔐┃admin", "admin"),
            ("🕵️┃confession-logs", "confession_logs"),
        ],
    ),
    (
        "═══ ⚠️ ・ DANGER ・ ⚠️ ═══",
        [
            ("⛔┃do-not-text-here", "trap"),
        ],
    ),
]


EXPLAINERS = {
    "commands": (
        "This channel explains every bot command. "
        "Use it when you're confused instead of freeballing it."
    ),
    "welcome": "Welcome messages and cards show up here.",
    "announcements": "Important server updates belong here.",
    "set_age": (
        "Use `/age` with your real age. "
        "This helps with server safety and makes your age visible on your profile."
    ),
    "chat": "Main chat. Be normal. Or at least interesting.",
    "images": "Drop images here.",
    "clips": "Clips go here.",
    "confessions": (
        "Use `/confess` to post anonymously. "
        "Reactions decide if it was brave or embarrassing."
    ),
    "curse": "Live curse leaderboard. Public shame, updated automatically.",
    "levels": "Level-up messages and XP progress show up here.",
    "music_cmds": (
        "Use music commands here like `/play`, `/skip`, `/queue`, and `/stop`."
    ),
    "economy": (
        "Daily, betting, robbing, and shop stuff. "
        "Financial irresponsibility lives here."
    ),
    "games": "Trivia, RPS, number guessing, and other game commands go here.",
    "admin": "Private admin room for server management.",
    "confession_logs": "Private confession logs.",
    "trap": (
        "Do not send anything here. No text, images, or files. "
        "The bot may ban anyone who does."
    ),
}


class ReservedModal(Modal, title="Enter password to rebuild this server"):
    password = TextInput(
        label="Password",
        style=discord.TextStyle.short,
        required=True,
        max_length=100,
    )

    def __init__(self, cog):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.handle_reserved(
            interaction,
            str(self.password),
        )


class ServerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def storage(self):
        return self.bot.get_cog("Storage")

    async def safe_pin(self, channel, content):
        message = await channel.send(content)

        try:
            await message.pin()
        except Exception:
            pass

        return message

    async def rebuild_server(self, guild):
        store = self.storage()
        guild_data = store.get_guild(guild.id)

        # Delete all existing channels.
        for channel in list(guild.channels):
            try:
                await channel.delete(
                    reason="Server rebuild via reserved command"
                )
            except Exception:
                pass

        # Create the parent age role if it does not exist.
        ages_parent_role = discord.utils.get(
            guild.roles,
            name="Ages",
        )

        if not ages_parent_role:
            try:
                await guild.create_role(
                    name="Ages",
                    permissions=discord.Permissions.none(),
                    reason="Age role bucket",
                )
            except Exception:
                pass

        guild_data["channels"] = {}
        guild_data["roles"] = {}

        admin_overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False,
                send_messages=False,
            )
        }

        for role in guild.roles:
            if role.permissions.administrator:
                admin_overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True,
                )

        for category_name, items in LAYOUT:
            category_overwrites = None

            if "ADMIN" in category_name:
                category_overwrites = admin_overwrites

            category = await guild.create_category(
                category_name,
                overwrites=category_overwrites,
            )

            for item in items:
                name = item[0]
                key = item[1]
                kind = item[2] if len(item) > 2 else "text"

                # Voice channels cannot receive messages or pins.
                if kind == "voice":
                    channel = await guild.create_voice_channel(
                        name,
                        category=category,
                    )

                    guild_data["channels"][key] = channel.id
                    continue

                channel_overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        read_message_history=True,
                    )
                }

                if key in {"admin", "confession_logs"}:
                    channel_overwrites = admin_overwrites

                channel = await guild.create_text_channel(
                    name,
                    category=category,
                    overwrites=channel_overwrites,
                )

                explainer = EXPLAINERS.get(
                    key,
                    "This channel exists for a reason.",
                )

                await self.safe_pin(
                    channel,
                    explainer,
                )

                if key == "trap":
                    await channel.send(
                        "Read the pinned message. "
                        "Type here and you may get banned instantly."
                    )

                if key == "commands":
                    commands_text = "**Bot Commands** | /gif | /caption | /play /skip /stop /queue /pause /resume /nowplaying /loop | /confess | /curseboard | /daily /rob /bet /rep /profile /age /trivia /rps /numguess /poll /avatar /serverinfo /userinfo /8ball /coinflip /roll /remindme /reserved"

                    commands_message = await channel.send(
                        commands_text
                    )

                    try:
                        await commands_message.pin()
                    except Exception:
                        pass

                    guild_data["commands_message_id"] = (
                        commands_message.id
                    )

                if key == "curse":
                    embed = discord.Embed(
                        title="🤬 Curse Leaderboard",
                        description="live shameboard",
                        color=discord.Color.red(),
                    )

                    curse_message = await channel.send(
                        embed=embed
                    )

                    guild_data["curse_message_id"] = (
                        curse_message.id
                    )

                guild_data["channels"][key] = channel.id

        store.save("guilds")

    async def handle_reserved(self, interaction, password):
        store = self.storage()
        guild_data = store.get_guild(interaction.guild.id)

        if password != guild_data.get("password"):
            await interaction.response.send_message(
                "wrong password. nice try.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "starting full server wipe and rebuild. "
            "this is the fun part.",
            ephemeral=True,
        )

        await self.rebuild_server(
            interaction.guild
        )

    @app_commands.command(
        name="reserved",
        description="Rebuild the server layout with the private password",
    )
    async def reserved(self, interaction: discord.Interaction):
        await interaction.response.send_modal(
            ReservedModal(self)
        )

    @app_commands.command(
        name="age",
        description="Set your real age role",
    )
    async def age(
        self,
        interaction: discord.Interaction,
        number: int,
    ):
        if number < 1 or number > 120:
            await interaction.response.send_message(
                "put a real age, not nonsense.",
                ephemeral=True,
            )
            return

        for role in interaction.user.roles:
            if role.name.startswith("Age: "):
                try:
                    await interaction.user.remove_roles(role)
                except Exception:
                    pass

        role_name = f"Age: {number}"

        role = discord.utils.get(
            interaction.guild.roles,
            name=role_name,
        )

        if not role:
            role = await interaction.guild.create_role(
                name=role_name,
                permissions=discord.Permissions.none(),
                reason="Age role",
            )

        try:
            await interaction.user.add_roles(role)
        except Exception:
            await interaction.response.send_message(
                "I created the role, but I couldn't assign it. "
                "Move the bot's role above the age roles.",
                ephemeral=True,
            )
            return

        store = self.storage()

        user = store.get_user(
            interaction.guild.id,
            interaction.user.id,
            interaction.user.display_name,
            interaction.user.name,
            str(interaction.user.display_avatar.url),
        )

        user["age"] = number
        store.save("users")

        await interaction.response.send_message(
            f"✅ role assigned. you are **{number} years old**."
        )


async def setup(bot):
    await bot.add_cog(ServerSetup(bot))
