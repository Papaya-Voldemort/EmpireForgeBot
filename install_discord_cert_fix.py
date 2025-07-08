import certifi
import ssl
import os

print("🔧 certifi path:", certifi.where())

# Tell Python to use the right certificate bundle
os.environ["SSL_CERT_FILE"] = certifi.where()

# Try connecting to Discord manually
import aiohttp
import asyncio

async def test_ssl():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://discord.com/api/v10") as resp:
            print("✅ HTTPS connection to Discord successful. Status:", resp.status)

asyncio.run(test_ssl())
