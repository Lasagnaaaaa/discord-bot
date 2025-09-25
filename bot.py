import discord
import requests
import asyncio
import os
import datetime
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

def demand_to_text(demand_level):
    demand_map = {
        0: "⚪ Unknown",
        1: "🔴 Low",
        2: "🟡 Normal",
        3: "🟢 High"
    }
    return demand_map.get(demand_level, "⚪ Unknown")

class MyClient(discord.Client):
    async def setup_hook(self):
        self.bg_task = asyncio.create_task(self.check_updates())

    async def on_ready(self):
        print(f"✅ Bot connected as {self.user}")

    def fetch_all_values(self):
        url = "https://www.rolimons.com/itemapi/itemdetails"
        response = requests.get(url)
        data = response.json()
        items = {}
        for item_id, details in data["items"].items():
            name = details[0]
            value = details[3]
            demand = details[4]
            items[name] = {
                "value": value,
                "demand": demand,
                "id": item_id
            }
        return items

    async def check_updates(self):
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        last_values = self.fetch_all_values()
        print("📥 Initial values loaded.")

        while not self.is_closed():
            await asyncio.sleep(60)
            current_values = self.fetch_all_values()
            changes = []

            for name, data in current_values.items():
                old_data = last_values.get(name)
                if old_data and old_data["value"] != data["value"]:
                    changes.append((name, old_data["value"], data["value"], data["demand"], data["id"]))

            for name, old, new, demand, item_id in changes:
                rolimons_link = f"https://www.rolimons.com/item/{item_id}"
                image_url = f"https://www.roblox.com/thumbs?assetId={item_id}&type=Asset&width=420&height=420"
                demand_text = demand_to_text(demand)

                if new > old:
                    direction = "📈 Increased"
                    color = discord.Color.green()
                elif new < old:
                    direction = "📉 Decreased"
                    color = discord.Color.red()
                else:
                    direction = "🔄 Changed"
                    color = discord.Color.orange()

                embed = discord.Embed(
                    title=name,
                    color=color,
                    timestamp=datetime.datetime.utcnow()
                )
                embed.add_field(name="Value", value=f"{old} ➡️ {new}", inline=True)
                embed.add_field(name="Change", value=direction, inline=True)
                embed.add_field(name="Demand", value=demand_text, inline=True)
                embed.add_field(name="Link", value=f"[View on Rolimons]({rolimons_link})", inline=False)
                embed.set_thumbnail(url=image_url)
                embed.set_footer(text="Value Bot • Rolimons Tracker")

                await channel.send(embed=embed)
                print(f"📢 Sent update for {name}: {old} ➡️ {new} | Demand: {demand_text}")

            last_values = current_values

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.lower() == "!hello":
            await message.channel.send("Hello! I'm monitoring item values in real time 🔍")

keep_alive()
client = MyClient(intents=intents)
client.run(TOKEN)
