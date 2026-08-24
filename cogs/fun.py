import discord
from discord.ext import commands
from discord import app_commands
import random


class Fun(commands.Cog):
    """Fun and utility commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="avatar", description="Get a user's avatar")
    @app_commands.describe(user="The user to get the avatar of (leave empty for yourself)")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        embed = discord.Embed(
            title=f"{user.display_name}'s Avatar",
            color=discord.Color.purple(),
        )
        embed.set_image(url=user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Get info about this server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.purple(),
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Channels", value=len(guild.channels))
        embed.add_field(name="Roles", value=len(guild.roles))
        embed.add_field(name="Created", value=guild.created_at.strftime("%B %d, %Y"))
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown")
        embed.add_field(name="Boosts", value=guild.premium_subscription_count)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Get info about a user")
    @app_commands.describe(user="The user to look up")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        embed = discord.Embed(
            title=user.display_name,
            color=user.color if user.color != discord.Color.default() else discord.Color.purple(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Username", value=user.name)
        embed.add_field(name="ID", value=user.id)
        embed.add_field(name="Joined Server", value=user.joined_at.strftime("%B %d, %Y") if user.joined_at else "Unknown")
        embed.add_field(name="Account Created", value=user.created_at.strftime("%B %d, %Y"))
        roles = [r.mention for r in user.roles[1:]]  # Skip @everyone
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles[:10]) if roles else "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your yes/no question")
    async def eightball(self, interaction: discord.Interaction, question: str):
        responses = [
            "It is certain.", "It is decidedly so.", "Without a doubt.",
            "Yes, definitely.", "You may rely on it.", "As I see it, yes.",
            "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
            "Reply hazy, try again.", "Ask again later.",
            "Better not tell you now.", "Cannot predict now.",
            "Concentrate and ask again.", "Don't count on it.",
            "My reply is no.", "My sources say no.",
            "Outlook not so good.", "Very doubtful.",
        ]
        embed = discord.Embed(color=discord.Color.purple())
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=f":8ball: {random.choice(responses)}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="poll", description="Create a quick poll")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
    )
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
        emojis = ["1\u20e3", "2\u20e3", "3\u20e3", "4\u20e3"]
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)

        description = ""
        for i, opt in enumerate(options):
            description += f"{emojis[i]} {opt}\n\n"

        embed = discord.Embed(
            title=f":bar_chart: {question}",
            description=description,
            color=discord.Color.purple(),
        )
        embed.set_footer(text=f"Poll by {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        emoji = ":coin:" 
        await interaction.response.send_message(f"{emoji} **{result}!**")

    @app_commands.command(name="roll", description="Roll dice")
    @app_commands.describe(sides="Number of sides (default: 6)")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        if sides < 2:
            await interaction.response.send_message("Dice need at least 2 sides!", ephemeral=True)
            return
        result = random.randint(1, sides)
        await interaction.response.send_message(f":game_die: Rolled a **{result}** (d{sides})")


async def setup(bot):
    await bot.add_cog(Fun(bot))
