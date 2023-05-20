# importing the libraries
import discord
from discord import app_commands
from util import (
    getResponse,
    initializeConversation,
)
import functools
import typing
import asyncio

GUILD_ID = 999999999999999999999 # replace with discord server id
MY_GUILD = discord.Object(id=GUILD_ID)
AI_LOADED = False
BOT_TOKEN = "replace with discord bot token"

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.default()
client = MyClient(intents=intents)

def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper

@to_thread
def get_ai(promt):
    resp = getResponse(promt)
    return resp

# to reload the bot
@to_thread
def start_ai():
    global AI_LOADED
    initializeConversation()
    AI_LOADED = True
    return

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")

@client.tree.command()
async def hello(interaction: discord.Interaction):
    """I'll say hello!"""
    await interaction.response.send_message(f"Hello, {interaction.user.mention}! So, what do we talk about?")

# reloads the bot
@client.tree.command()
@app_commands.default_permissions()
@app_commands.guild_only()
async def start(interaction: discord.Interaction):
    """Reloads/Starts me up."""
    await interaction.response.defer()
    await start_ai()
    embed = discord.Embed(color=discord.colour.Color.yellow(), title="Whew, Refreshed and Reloaded!")
    embed.description = "To start chatting with me, use the `/prompt` command please."
    return await interaction.followup.send(embed=embed)

# sending a prompt
@client.tree.command()
@app_commands.guild_only()
@app_commands.describe(prompt="The prompt you want to send to the AI")
async def prompt(interaction: discord.Interaction, prompt: str):
    """Sends a prompt to me."""
    await interaction.response.defer()
    if not AI_LOADED:
        embed = discord.Embed(
            color=discord.colour.Color.dark_orange(), title="I'm not loaded yet, please try again."
        )
        embed.description = "Please ask the bot owner to reload me using `/start`"
        return await interaction.followup.send(embed=embed)

    resp = await get_ai(prompt)
    # if response is too long (len(resp) > 1024)
    embed = discord.Embed(color=discord.colour.Color.teal(), title=prompt)

    embed.description = resp
    embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    embed.timestamp = interaction.created_at

    return await interaction.followup.send(embed=embed)

# to shut down the bot
@client.tree.command()
@app_commands.guild_only()
@app_commands.default_permissions()
async def shutdown(interaction: discord.Interaction):
    """Shuts me down and I'll go ZZZZZZZ"""
    global AI_LOADED
    AI_LOADED = False
    embed = discord.Embed(color=discord.colour.Color.red(), title="Shutting down and going to sleep...")
    embed.description = "Wake me up again using `/reload`!"
    await interaction.response.send_message(embed=embed)
    # await client.close()

@client.event
async def on_interaction(interaction: discord.Interaction):
    # for unknown commands
    if (
        interaction.type is discord.InteractionType.application_command
        and not interaction.command
    ):
        await interaction.response.send_message("Unknown command.", ephemeral=True)


if __name__ == "__main__":
    client.run(BOT_TOKEN)
