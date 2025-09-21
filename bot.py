import discord
import requests
import asyncio
import os
from dotenv import load_dotenv

# Carica variabili da .env (solo in locale)
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

class MyClient(discord.Client):
    async def setup_hook(self):
        # Avvio il task periodico quando il bot è pronto
        self.bg_task = asyncio.create_task(self.check_updates())

    async def on_ready(self):
        print(f"✅ Bot connesso come {self.user}")

    def fetch_all_values(self):
        """Scarica tutte le value da Rolimons"""
        url = "https://www.rolimons.com/itemapi/itemdetails"
        response = requests.get(url)
        data = response.json()
        items = {}
        for item_id, details in data["items"].items():
            name = details[0]
            value = details[3]
            items[name] = {
                "value": value,
                "id": item_id
            }
        return items

    async def check_updates(self):
        """Controlla ogni 1 minuto se ci sono cambi di value"""
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        last_values = self.fetch_all_values()
        print("📥 Valori iniziali caricati.")

        while not self.is_closed():
            await asyncio.sleep(60)
            current_values = self.fetch_all_values()
            changes = []

            for name, data in current_values.items():
                old_data = last_values.get(name)
                if old_data and old_data["value"] != data["value"]:
                    changes.append((name, old_data["value"], data["value"], data["id"]))

            if changes:
                for name, old, new, item_id in changes:
                    embed = discord.Embed(
                        title=f"🔄 {name}",
                        description=f"**Value cambiato:** {old} ➡️ {new}",
                        color=discord.Color.orange()
                    )
                    image_url = f"https://www.rolimons.com/thumbs/{item_id}.png"
                    embed.set_thumbnail(url=image_url)
                    await channel.send(embed=embed)
                print(f"📢 {len(changes)} cambi trovati e inviati.")
            else:
                print("ℹ️ Nessun cambiamento trovato.")

            last_values = current_values

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.lower() == "!ciao":
            await message.channel.send("Ciao! Sto monitorando tutte le value 🔍")

# Avvio del bot
client = MyClient(intents=intents)
client.run(TOKEN)
