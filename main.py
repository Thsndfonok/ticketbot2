import discord
from discord.ext import commands, tasks
import itertools
import asyncio
from flask import Flask
from threading import Thread
import os
import re

app = Flask('')

@app.route('/')
def home():
    return "Bot működik!", 200

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
    
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 🎮 Státusz rotátor lista
statusok = itertools.cycle([
    discord.Game("🎮 Játékban: developed by thsnd"),
    discord.Streaming(name="élőben Twitch-en", url="https://twitch.tv/thsndboss"),
    discord.Activity(type=discord.ActivityType.listening, name="🎵 Spotify"),
    discord.Activity(type=discord.ActivityType.watching, name="👀 YouTube videók")
])

@bot.event
async def on_ready():
    print(f"{bot.user} bejelentkezett!")
    status_valtoztato.start()

@tasks.loop(seconds=60)
async def status_valtoztato():
    await bot.change_presence(activity=next(statusok))

# 🎫 Ticket gombok
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Support", style=discord.ButtonStyle.blurple, custom_id="ticket_support")
    async def support_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "support")

    @discord.ui.button(label="Buy", style=discord.ButtonStyle.green, custom_id="ticket_buy")
    async def buy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "buy")

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        owner_role = discord.utils.get(guild.roles, name="・Owner")
        coowner_role = discord.utils.get(guild.roles, name="・Co-Owner")
        if owner_role:
            overwrites[owner_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        if coowner_role:
            overwrites[coowner_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel_name = f"ticket-{ticket_type}-{interaction.user.name}".replace(" ", "-").lower()
        channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)

        await channel.send(
            f"🎫 Helló {interaction.user.mention}, itt a te `{ticket_type}` ticketed! Egy moderátor hamarosan válaszol.",
            view=CloseButton()
        )

        await interaction.response.send_message(f"✅ Ticket létrehozva: {channel.mention}", ephemeral=True)

# 🔒 Close gomb
class CloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = interaction.user
        guild = interaction.guild
        channel = interaction.channel

        owner_role = discord.utils.get(guild.roles, name="・Owner")
        coowner_role = discord.utils.get(guild.roles, name="・Co-Owner")

        if not (owner_role in author.roles or coowner_role in author.roles):
            await interaction.response.send_message("❌ Nincs jogosultságod lezárni ezt a ticketet.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Ticket lezárása...")
        await asyncio.sleep(3)
        await channel.delete()

# 📩 Ticketpanel parancs
@bot.command()
async def ticketpanel(ctx):
    view = TicketView()
    await ctx.send("🎫 Válassz egy opciót a ticket nyitásához:", view=view)

# 🟢 Bot indítása
keep_alive()
client.run(os.getenv("TOKEN"))
