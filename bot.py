import discord
import requests
import asyncio
import os
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

ASSET_TYPE_MAP = {
    8: "Hat",
    41: "Gear",
    42: "Face",
    43: "T-Shirt",
    44: "Shirt",
    45: "Pants",
    50: "Back Accessory",
    51: "Front Accessory",
    52: "Hair Accessory",
    53: "Hat Accessory",
    54: "Face Accessory",
    55: "Neck Accessory",
    56: "Shoulder Accessory",
    57: "Waist Accessory"
}

def get_asset_type(item_id):
    try:
        url = f"https://api.roblox.com/marketplace/productinfo?assetId={item_id}"
        response = requests.get(url)
        data = response.json()
        asset_type_id = data.get("AssetTypeId")
        return ASSET_TYPE_MAP.get(asset_type_id, "Unknown")
    except Exception as e:
        print(f"Error fetching asset type for {item_id}: {e}")
        return "Unknown"

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
            items[name] = {
                "value": value,
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
                    changes.append((name, old_data["value"], data["value"], data["id"]))

            for name, old, new, item_id in changes:
                rolimons_link = f"https://www.rolimons.com/item/{item_id}"
                image_url = f"https://www.rolimons.com/thumbs/{item_id}.png"
                asset_type = get_asset_type(item_id)

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
                    title=f"{name}",
                    description=(
                        f"**Value:** {old} ➡️ {new}\n"
                        f"**Change:** {direction}\n"
                        f"**Type:** {asset_type}\n"
                        f"[View on Rolimons]({rolimons_link})"
                    ),
                    color=color
                )
                embed.set_thumbnail(url=image_url)
                await channel.send(embed=embed)

                print(f"📢 Sent update for {name}: {old} ➡️ {new}")

            last_values = current_values

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.lower() == "!hello":
            await message.channel.send("Hello! I'm monitoring item values in real time 🔍")

keep_alive()
client = MyClient(intents=intents)
client.run(TOKEN)



