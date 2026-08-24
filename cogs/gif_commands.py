import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import os


class GifCommands(commands.Cog):
    """GIF and meme creation commands"""

    def __init__(self, bot):
        self.bot = bot

    def _get_font(self, size):
        """Get a bold font, falling back to default if Impact isn't available."""
        font_paths = [
            "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/Impact.ttf",
            "C:/Windows/Fonts/Impact.ttf",
            "/System/Library/Fonts/Impact.ttf",
            "fonts/Impact.ttf",
        ]
        for path in font_paths:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        # Fallback to default
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        except:
            return ImageFont.load_default()

    def _create_meme(self, image_bytes, caption_text):
        """Create a meme with white caption bar on top and image below."""
        # Open the image
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGBA")

        # Resize image to a reasonable width if too large
        max_width = 600
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)

        # Calculate caption area
        font_size = max(24, img.width // 15)
        font = self._get_font(font_size)

        # Wrap text
        chars_per_line = max(15, img.width // (font_size // 2))
        wrapped = textwrap.wrap(caption_text, width=chars_per_line)
        if not wrapped:
            wrapped = [caption_text]

        # Calculate text height
        line_height = font_size + 10
        caption_height = (len(wrapped) * line_height) + 40  # padding

        # Create new image with caption space
        total_height = caption_height + img.height
        meme = Image.new("RGBA", (img.width, total_height), (255, 255, 255, 255))

        # Draw caption text
        draw = ImageDraw.Draw(meme)
        y_offset = 20
        for line in wrapped:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (img.width - text_width) // 2
            draw.text((x, y_offset), line, fill=(0, 0, 0), font=font)
            y_offset += line_height

        # Paste original image below caption
        meme.paste(img, (0, caption_height))

        # Save to bytes
        output = io.BytesIO()
        meme_rgb = meme.convert("RGB")
        meme_rgb.save(output, format="PNG")
        output.seek(0)
        return output

    def _convert_to_gif(self, image_bytes):
        """Convert an image to GIF format."""
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert("RGBA")

        # If it's already animated, just pass it through
        output = io.BytesIO()
        img.convert("P", palette=Image.ADAPTIVE).save(output, format="GIF")
        output.seek(0)
        return output

    @app_commands.command(name="gif", description="Convert an image to GIF, or add a meme caption to it")
    @app_commands.describe(
        image="The image to convert or caption",
        text="Optional: Add caption text above the image (meme style)"
    )
    async def gif_command(self, interaction: discord.Interaction, image: discord.Attachment, text: str = None):
        await interaction.response.defer()

        # Validate it's an image
        if not image.content_type or not image.content_type.startswith("image"):
            await interaction.followup.send("That doesn't look like an image. Send me a pic!", ephemeral=True)
            return

        # Download the image
        image_bytes = await image.read()

        if text:
            # Create meme with caption
            result = self._create_meme(image_bytes, text)
            filename = "meme.png"
            await interaction.followup.send(
                file=discord.File(result, filename=filename)
            )
        else:
            # Just convert to GIF
            result = self._convert_to_gif(image_bytes)
            await interaction.followup.send(
                file=discord.File(result, filename="converted.gif")
            )

    @app_commands.command(name="caption", description="Add a meme-style caption to an image")
    @app_commands.describe(
        image="The image to caption",
        text="The caption text (appears in white bar above image)"
    )
    async def caption_command(self, interaction: discord.Interaction, image: discord.Attachment, text: str):
        await interaction.response.defer()

        if not image.content_type or not image.content_type.startswith("image"):
            await interaction.followup.send("That doesn't look like an image. Send me a pic!", ephemeral=True)
            return

        image_bytes = await image.read()
        result = self._create_meme(image_bytes, text)
        await interaction.followup.send(
            file=discord.File(result, filename="meme.png")
        )


async def setup(bot):
    await bot.add_cog(GifCommands(bot))
