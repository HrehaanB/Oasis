import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load environment variables ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# --- Configure Gemini ---
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

# --- Discord setup ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Channel Personas ---
PERSONAS = {
    "general": """You are Oasis, a friendly and helpful personal assistant. 
    Be warm, conversational, and proactive — like an AI coworker that helps with anything.""",

    "email": """You are Oasis, an expert email assistant. 
    Write messages that are clear, concise, professional, and polite. No fluff — get straight to the point.""",

    "brainstorming": """You are Oasis, a creative brainstorming partner. 
    Generate ideas freely, explore multiple angles, and build on suggestions with enthusiasm."""
}

# --- On Ready ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

# --- Ping command ---
@bot.tree.command(name="ping", description="Check if the bot is alive")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓", ephemeral=True)

# --- Ask command (auto-uses channel persona) ---
@bot.tree.command(name="ask", description="Ask Oasis something — behavior changes by channel")
async def ask(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer()

    try:
        channel_name = interaction.channel.name.lower()
        persona = PERSONAS.get(channel_name, PERSONAS["general"])

        full_prompt = f"{persona}\n\nUser: {prompt}\nOasis:"
        response = model.generate_content(full_prompt)
        text = response.text or "(no reply)"

        # Split long messages into chunks of 2000 characters
        if len(text) > 2000:
            chunks = [text[i:i + 2000] for i in range(0, len(text), 2000)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await interaction.followup.send(chunk)
                else:
                    await interaction.channel.send(chunk)
        else:
            await interaction.followup.send(text)

    except Exception as e:
        await interaction.followup.send(f"⚠️ Error: {e}")

# --- Run bot ---
bot.run(DISCORD_TOKEN)
