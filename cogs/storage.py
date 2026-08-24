import json
import os
from discord.ext import commands


class Storage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs("data", exist_ok=True)
        self.files = {
            "users": "data/users.json",
            "guilds": "data/guilds.json",
            "confessions": "data/confessions.json",
            "quotes": "data/quotes.json",
        }
        self.cache = {}
        for key, path in self.files.items():
            self.cache[key] = self._load(path)

    def _load(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except:
                    return {}
        return {}

    def save(self, key):
        with open(self.files[key], "w", encoding="utf-8") as f:
            json.dump(self.cache[key], f, indent=2)

    def get_user(self, guild_id, user_id, display_name=None, username=None, avatar_url=None):
        gid = str(guild_id)
        uid = str(user_id)
        users = self.cache["users"]
        if gid not in users:
            users[gid] = {}
        if uid not in users[gid]:
            users[gid][uid] = {
                "xp": 0,
                "level": 1,
                "coins": 0,
                "rep": 0,
                "curse_count": 0,
                "daily_streak": 0,
                "last_daily": None,
                "age": None,
                "night_streak": 0,
                "spam_strikes": 0,
                "last_messages": [],
                "display_name": display_name or "Unknown",
                "username": username or "Unknown",
                "avatar_url": avatar_url or "",
                "rejoined": False,
                "join_count": 1,
            }
        if display_name:
            users[gid][uid]["display_name"] = display_name
        if username:
            users[gid][uid]["username"] = username
        if avatar_url:
            users[gid][uid]["avatar_url"] = avatar_url
        self.save("users")
        return users[gid][uid]

    def get_guild(self, guild_id):
        gid = str(guild_id)
        guilds = self.cache["guilds"]
        if gid not in guilds:
            guilds[gid] = {
                "channels": {},
                "roles": {},
                "curse_message_id": None,
                "commands_message_id": None,
                "welcome_image_url": None,
                "password": "Xv9$kP2!mW7#qR4@nL",
            }
        self.save("guilds")
        return guilds[gid]


async def setup(bot):
    await bot.add_cog(Storage(bot))
