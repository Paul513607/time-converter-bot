import traceback
import discord
from discord.ext import commands
from discord import app_commands
import dotenv
import os
from database.connection import Connection
from convert import converter_utils

dotenv.load_dotenv()
token = os.getenv('TOKEN')

class Client(commands.Bot):
    db_connection: Connection

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):

        try:
            self.db_connection = Connection(
                os.getenv('DB_NAME'),
                os.getenv('DB_USER'),
                os.getenv('DB_PASSWORD'),
                os.getenv('DB_HOST'),
                os.getenv('DB_PORT')
            )

            guild = discord.Object(id=os.getenv('GUILD_ID'))

            self.tree.add_command(convert_to_timestamp)
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            traceback.print_exc()
            return

        print(f'Logged on as {self.user}!')

    async def on_message(self, message): 
        if message.author == self.user:
            return
        user = self.db_connection.get_user(message.author.id)
        if user is None:
            return
        user_timezone_str = user[1]
        timestamp = converter_utils.parse_message(message.content, user_timezone_str)
        if timestamp != -1:
            self.db_connection.insert_message(message.id, timestamp)

intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix='!', intents=intents)

# GUILD_ID = None 
GUILD_ID = discord.Object(id=os.getenv('GUILD_ID'))

@client.tree.command(name='set-me', description='Set your timezone', guild=GUILD_ID)
async def set_me(interaction: discord.Interaction, timezone: str):
    if (not converter_utils.verify_timezone(timezone)):
        await interaction.response.send_message('Invalid timezone format. Please use UTC+/-X', ephemeral=True)
        return
    if (client.db_connection.get_user(interaction.user.id) is not None):
        client.db_connection.delete_user(interaction.user.id)
    client.db_connection.insert_user(interaction.user.id, timezone)
    await interaction.response.send_message(f'Timezone set to {timezone}', ephemeral=True)

@client.tree.command(name='remove-me', description='Remove your timezone', guild=GUILD_ID)
async def remove_me(interaction: discord.Interaction):
    client.db_connection.delete_user(interaction.user.id)
    await interaction.response.send_message('Timezone removed', ephemeral=True)

@client.tree.command(name='help', description='Check how you can use this bot', guild=GUILD_ID)
async def help(interaction: discord.Interaction):
    message = """
**Timestamp Bot**
This bot can convert time references in messages to timestamps.
Use /set-me <timezone> to set your timezone. (e.g. /set-me Europe/London)
Use /remove-me to remove your timezone.

What will the bot detect?
- Relative time: "in X hours", "in X minutes", "in Xh", "in X min"
- Relative time: "X hours ago", "X minutes ago", "Xh ago", "X min ago"
- 12-hour format: "HH AM/PM" or "HH:MM AM/PM"
- 24-hour format: "HH:MM" or "at HH"
"""
    await interaction.response.send_message(message, ephemeral=True)

@app_commands.context_menu(name="Convert to Timestamp")
@app_commands.guilds(GUILD_ID)
async def convert_to_timestamp(interaction: discord.Interaction, message: discord.Message):
    message = client.db_connection.get_message(message.id)
    if message is None:
        await interaction.response.send_message("Message not found.", ephemeral=True)
        return
    
    timestamp = message[1]
    tag = converter_utils.convert_to_tag(timestamp)
    await interaction.response.send_message(tag, ephemeral=True)


print("Starting bot")
client.run(token)
