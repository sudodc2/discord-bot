import discord
from discord.ext import commands
from discord import app_commands
import random


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_trivia = {}
        self.active_guess = {}

    def storage(self):
        return self.bot.get_cog("Storage")

    @app_commands.command(name="avatar", description="Get a user's avatar")
    async def avatar(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        embed = discord.Embed(title=f"{user.display_name}'s Avatar", color=discord.Color.purple())
        embed.set_image(url=user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="serverinfo", description="Get info about this server")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=guild.name, color=discord.Color.purple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Channels", value=len(guild.channels))
        embed.add_field(name="Roles", value=len(guild.roles))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Get info about a user")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        user = user or interaction.user
        embed = discord.Embed(title=user.display_name, color=discord.Color.purple())
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Username", value=user.name)
        embed.add_field(name="Joined", value=user.joined_at.strftime("%B %d, %Y") if user.joined_at else "Unknown")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    async def eightball(self, interaction: discord.Interaction, question: str):
        responses = ["Yes.", "No.", "Maybe.", "You know better than me.", "absolutely not."]
        await interaction.response.send_message(f"🎱 {random.choice(responses)}")

    @app_commands.command(name="poll", description="Create a quick poll")
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        options = [option1, option2] + ([option3] if option3 else []) + ([option4] if option4 else [])
        desc = "\n".join([f"{emojis[i]} {opt}" for i, opt in enumerate(options)])
        embed = discord.Embed(title=question, description=desc, color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        for i in range(len(options)):
            await msg.add_reaction(emojis[i])

    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🪙 **{random.choice(['Heads', 'Tails'])}**")

    @app_commands.command(name="roll", description="Roll dice")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        await interaction.response.send_message(f"🎲 rolled **{random.randint(1, max(2, sides))}**")

    @app_commands.command(name="rob", description="Try robbing another user")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):
        if user.id == interaction.user.id:
            await interaction.response.send_message("robbing yourself is just budgeting.", ephemeral=True)
            return
        store = self.storage()
        robber = store.get_user(interaction.guild.id, interaction.user.id, interaction.user.display_name, interaction.user.name, str(interaction.user.display_avatar.url))
        target = store.get_user(interaction.guild.id, user.id, user.display_name, user.name, str(user.display_avatar.url))
        if random.random() < 0.55:
            amount = min(target.get("coins", 0), random.randint(20, 120))
            target["coins"] -= amount
            robber["coins"] += amount
            msg = f"you stole **{amount}** coins from {user.mention}"
        else:
            amount = min(robber.get("coins", 0), random.randint(10, 60))
            robber["coins"] -= amount
            msg = f"you got caught and lost **{amount}** coins. clown activity."
        store.save("users")
        await interaction.response.send_message(msg)

    @app_commands.command(name="bet", description="Bet coins on a coinflip")
    async def bet(self, interaction: discord.Interaction, amount: int):
        store = self.storage()
        user = store.get_user(interaction.guild.id, interaction.user.id, interaction.user.display_name, interaction.user.name, str(interaction.user.display_avatar.url))
        if amount <= 0 or user.get("coins", 0) < amount:
            await interaction.response.send_message("you don't have that much.", ephemeral=True)
            return
        if random.random() < 0.5:
            user["coins"] += amount
            msg = f"you won **{amount}** coins"
        else:
            user["coins"] -= amount
            msg = f"you lost **{amount}** coins"
        store.save("users")
        await interaction.response.send_message(msg)

    @app_commands.command(name="trivia", description="Answer trivia first to win coins")
    async def trivia(self, interaction: discord.Interaction):
        questions = [
            ("What planet is known as the Red Planet?", "mars"),
            ("How many continents are there?", "7"),
            ("What gas do plants breathe in?", "carbon dioxide"),
        ]
        q, a = random.choice(questions)
        self.active_trivia[interaction.channel_id] = a.lower()
        await interaction.response.send_message(f"🧠 Trivia: **{q}**\nfirst correct answer wins 50 coins")

    @app_commands.command(name="numguess", description="Guess a number from 1 to 100")
    async def numguess(self, interaction: discord.Interaction):
        number = random.randint(1, 100)
        self.active_guess[interaction.channel_id] = number
        await interaction.response.send_message("I picked a number from 1 to 100. start guessing in chat.")

    @app_commands.command(name="rps", description="Challenge someone to rock paper scissors")
    async def rps(self, interaction: discord.Interaction, user: discord.Member):
        choice1 = random.choice(["rock", "paper", "scissors"])
        choice2 = random.choice(["rock", "paper", "scissors"])
        win = {
            ("rock", "scissors"), ("scissors", "paper"), ("paper", "rock")
        }
        if choice1 == choice2:
            result = "tie"
        elif (choice1, choice2) in win:
            result = f"{interaction.user.mention} wins"
        else:
            result = f"{user.mention} wins"
        await interaction.response.send_message(f"{interaction.user.display_name}: **{choice1}**\n{user.display_name}: **{choice2}**\n{result}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        store = self.storage()
        if message.channel.id in self.active_trivia:
            if message.content.lower().strip() == self.active_trivia[message.channel.id]:
                user = store.get_user(message.guild.id, message.author.id, message.author.display_name, message.author.name, str(message.author.display_avatar.url))
                user["coins"] += 50
                store.save("users")
                del self.active_trivia[message.channel.id]
                await message.channel.send(f"{message.author.mention} got it right and won **50** coins")
        if message.channel.id in self.active_guess:
            try:
                guess = int(message.content.strip())
                target = self.active_guess[message.channel.id]
                if guess == target:
                    user = store.get_user(message.guild.id, message.author.id, message.author.display_name, message.author.name, str(message.author.display_avatar.url))
                    user["coins"] += 40
                    store.save("users")
                    del self.active_guess[message.channel.id]
                    await message.channel.send(f"{message.author.mention} guessed it. **{target}**. won **40** coins")
            except:
                pass


async def setup(bot):
    await bot.add_cog(Fun(bot))
