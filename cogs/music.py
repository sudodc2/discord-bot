import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
from collections import deque


# YT-DLP options
YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "extract_flat": False,
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


class Song:
    def __init__(self, title, url, stream_url, duration, requester):
        self.title = title
        self.url = url
        self.stream_url = stream_url
        self.duration = duration
        self.requester = requester

    @property
    def duration_str(self):
        if not self.duration:
            return "Live"
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"


class GuildMusicState:
    def __init__(self):
        self.queue = deque()
        self.current = None
        self.voice_client = None
        self.loop = False
        self.inactivity_task = None


class Music(commands.Cog):
    """Music player commands"""

    def __init__(self, bot):
        self.bot = bot
        self.guild_states = {}

    def get_state(self, guild_id):
        if guild_id not in self.guild_states:
            self.guild_states[guild_id] = GuildMusicState()
        return self.guild_states[guild_id]

    async def _join_channel(self, interaction):
        """Join the user's voice channel."""
        if not interaction.user.voice:
            await interaction.followup.send("You need to be in a voice channel!", ephemeral=True)
            return None

        channel = interaction.user.voice.channel
        state = self.get_state(interaction.guild_id)

        if state.voice_client and state.voice_client.is_connected():
            if state.voice_client.channel != channel:
                await state.voice_client.move_to(channel)
        else:
            state.voice_client = await channel.connect()

        return state.voice_client

    async def _search_song(self, query):
        """Search for a song and return info."""
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
        except Exception:
            return None

        if "entries" in data:
            data = data["entries"][0] if data["entries"] else None

        if not data:
            return None

        return data

    def _play_next(self, guild_id):
        """Play the next song in queue."""
        state = self.get_state(guild_id)

        if state.loop and state.current:
            # Re-play current song
            source = discord.FFmpegPCMAudio(state.current.stream_url, **FFMPEG_OPTIONS)
            state.voice_client.play(source, after=lambda e: self._play_next(guild_id))
            return

        if not state.queue:
            state.current = None
            # Start inactivity timer
            if state.voice_client:
                asyncio.run_coroutine_threadsafe(
                    self._inactivity_disconnect(guild_id), self.bot.loop
                )
            return

        state.current = state.queue.popleft()
        source = discord.FFmpegPCMAudio(state.current.stream_url, **FFMPEG_OPTIONS)
        state.voice_client.play(source, after=lambda e: self._play_next(guild_id))

    async def _inactivity_disconnect(self, guild_id):
        """Disconnect after 3 minutes of inactivity."""
        await asyncio.sleep(180)  # 3 minutes
        state = self.get_state(guild_id)
        if state.voice_client and not state.voice_client.is_playing() and not state.queue:
            await state.voice_client.disconnect()
            state.voice_client = None
            state.current = None

    @app_commands.command(name="play", description="Play a song from YouTube (search or URL)")
    @app_commands.describe(query="Song name or YouTube URL")
    async def play(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()

        vc = await self._join_channel(interaction)
        if not vc:
            return

        state = self.get_state(interaction.guild_id)
        state.voice_client = vc

        # Search for the song
        data = await self._search_song(query)
        if not data:
            await interaction.followup.send("Couldn't find that song. Try a different search?", ephemeral=True)
            return

        song = Song(
            title=data.get("title", "Unknown"),
            url=data.get("webpage_url", ""),
            stream_url=data.get("url", ""),
            duration=data.get("duration", 0),
            requester=interaction.user.display_name,
        )

        if state.voice_client.is_playing() or state.current:
            # Add to queue
            state.queue.append(song)
            embed = discord.Embed(
                title="Added to Queue",
                description=f"**{song.title}** - `{song.duration_str}`",
                color=discord.Color.green(),
            )
            embed.set_footer(text=f"Requested by {song.requester} | Position: {len(state.queue)}")
            await interaction.followup.send(embed=embed)
        else:
            # Play immediately
            state.current = song
            source = discord.FFmpegPCMAudio(song.stream_url, **FFMPEG_OPTIONS)
            state.voice_client.play(source, after=lambda e: self._play_next(interaction.guild_id))

            embed = discord.Embed(
                title="Now Playing",
                description=f"**{song.title}** - `{song.duration_str}`",
                color=discord.Color.purple(),
            )
            embed.set_footer(text=f"Requested by {song.requester}")
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)

        if not state.voice_client or not state.voice_client.is_playing():
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)
            return

        state.loop = False
        state.voice_client.stop()  # Triggers _play_next
        await interaction.response.send_message("Skipped! :track_next:")

    @app_commands.command(name="stop", description="Stop playback and clear the queue")
    async def stop(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)

        if not state.voice_client:
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
            return

        state.queue.clear()
        state.current = None
        state.loop = False
        if state.voice_client.is_playing():
            state.voice_client.stop()
        await state.voice_client.disconnect()
        state.voice_client = None
        await interaction.response.send_message("Stopped and disconnected. :wave:")

    @app_commands.command(name="queue", description="Show the current music queue")
    async def queue_cmd(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)

        if not state.current and not state.queue:
            await interaction.response.send_message("Queue is empty. Use `/play` to add songs!", ephemeral=True)
            return

        embed = discord.Embed(title="Music Queue", color=discord.Color.purple())

        if state.current:
            embed.add_field(
                name="Now Playing",
                value=f"**{state.current.title}** - `{state.current.duration_str}`",
                inline=False,
            )

        if state.queue:
            queue_list = ""
            for i, song in enumerate(list(state.queue)[:10], 1):
                queue_list += f"`{i}.` **{song.title}** - `{song.duration_str}`\n"
            if len(state.queue) > 10:
                queue_list += f"\n... and {len(state.queue) - 10} more"
            embed.add_field(name="Up Next", value=queue_list, inline=False)

        embed.set_footer(text=f"{len(state.queue)} song(s) in queue")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)

        if state.voice_client and state.voice_client.is_playing():
            state.voice_client.pause()
            await interaction.response.send_message("Paused :pause_button:")
        else:
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)

    @app_commands.command(name="resume", description="Resume the paused song")
    async def resume(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)

        if state.voice_client and state.voice_client.is_paused():
            state.voice_client.resume()
            await interaction.response.send_message("Resumed :arrow_forward:")
        else:
            await interaction.response.send_message("Nothing is paused.", ephemeral=True)

    @app_commands.command(name="nowplaying", description="Show what's currently playing")
    async def nowplaying(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)

        if not state.current:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Now Playing",
            description=f"**{state.current.title}**",
            color=discord.Color.purple(),
        )
        embed.add_field(name="Duration", value=state.current.duration_str)
        embed.add_field(name="Requested by", value=state.current.requester)
        if state.current.url:
            embed.add_field(name="Link", value=f"[YouTube]({state.current.url})", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="loop", description="Toggle looping the current song")
    async def loop(self, interaction: discord.Interaction):
        state = self.get_state(interaction.guild_id)
        state.loop = not state.loop
        status = "enabled" if state.loop else "disabled"
        await interaction.response.send_message(f"Loop {status} :repeat:")


async def setup(bot):
    await bot.add_cog(Music(bot))
