import os
import json
import discord
from discord import app_commands
from dotenv import load_dotenv
import google.generativeai as genai

# --- Load environment variables ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Configure Gemini ---
genai.configure(api_key=GEMINI_API_KEY)
DEFAULT_MODEL = "gemini-2.5-pro"  # Highest-tier Gemini model as of 2025

# --- Persona utilities ---
def load_personas():
    if not os.path.exists("personas.json"):
        with open("personas.json", "w") as f:
            json.dump({
                "default": {
                    "name": "Default",
                    "system_instruction": "You are a helpful, creative assistant.",
                    "temperature": 0.7,
                    "model": DEFAULT_MODEL
                },
                "by_channel": {}
            }, f, indent=2)
    with open("personas.json", "r") as f:
        return json.load(f)

def save_personas(data):
    with open("personas.json", "w") as f:
        json.dump(data, f, indent=2)

personas = load_personas()

def persona_for_channel(channel_id: int):
    return personas.get("by_channel", {}).get(str(channel_id), personas["default"])

# --- Gemini call ---
def call_gemini(prompt: str, system_instruction: str = "", temperature: float = 0.7) -> str:
    try:
        model = genai.GenerativeModel(
            model_name=DEFAULT_MODEL,
            system_instruction=system_instruction or None,
            generation_config={"temperature": temperature}
        )
        response = model.generate_content(prompt)
        text = (response.text or "").strip()
        return text if text else "⚠️ Gemini returned an empty response."
    except Exception as e:
        return f"❌ Gemini error: {e}"

# --- Discord setup ---
intents = discord.Intents.default()
intents.message_content = True

class GeminiBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        await self.tree.sync()

bot = GeminiBot()

# --- Commands ---

@bot.tree.command(name="ping", description="Check if the bot is alive.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! 🏓 (Online and running Gemini 2.5 Pro)", ephemeral=True)

@bot.tree.command(name="ask", description="Ask the Gemini 2.5 Pro model a question.")
@app_commands.describe(prompt="Your question or request for the AI")
async def ask(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(thinking=True)
    persona = persona_for_channel(interaction.channel_id)
    reply = call_gemini(
        prompt,
        persona.get("system_instruction", ""),
        persona.get("temperature", 0.7)
    )
    if len(reply) > 1900:
        reply = reply[:1900] + "\n\n…(truncated)"
    await interaction.followup.send(reply)

@bot.tree.command(name="persona_set", description="Set or customize this channel's personality.")
@app_commands.describe(
    name="A short label for the persona",
    system_instruction="Describe how the bot should act in this channel.",
    temperature="Creativity level (0–1, optional)"
)
async def persona_set(interaction: discord.Interaction, name: str, system_instruction: str, temperature: float = 0.7):
    personas.setdefault("by_channel", {})
    personas["by_channel"][str(interaction.channel_id)] = {
        "name": name,
        "system_instruction": system_instruction,
        "temperature": temperature,
        "model": DEFAULT_MODEL
    }
    save_personas(personas)
    await interaction.response.send_message(f"✅ Persona for this channel set to **{name}**", ephemeral=True)

@bot.tree.command(name="persona_show", description="Show the active persona for this channel.")
async def persona_show(interaction: discord.Interaction):
    p = persona_for_channel(interaction.channel_id)
    msg = (
        f"**Persona:** {p.get('name','(unnamed)')}\n"
        f"**Temperature:** {p.get('temperature')}\n"
        f"**Model:** {p.get('model')}\n"
        f"**Behavior:**\n> {p.get('system_instruction','(none)')}"
    )
    await interaction.response.send_message(msg, ephemeral=True)

# --- Run bot ---
bot.run(DISCORD_TOKEN)
