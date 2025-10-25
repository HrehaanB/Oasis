import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from Railway (or .env locally)
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# Intents let your bot read messages & reply
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Simple on_ready confirmation
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

# Basic ping command
@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓", ephemeral=True)

# Ask Gemini command
@bot.tree.command(name="ask", description="Ask Gemini a question")
async def ask(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()
    try:
        response = model.generate_content(prompt)
        await interaction.followup.send(response.text or "(no reply)")
    except Exception as e:
        await interaction.followup.send(f"⚠️ Error: {e}")

# Keep the bot running
bot.run(DISCORD_TOKEN)
