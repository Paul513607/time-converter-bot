import discord
from discord.ext import commands
from discord import app_commands
import dotenv
import os
from convert.converter import Converter
from database.connection import Connection

dotenv.load_dotenv()
token = os.getenv('TOKEN')

class Client(commands.Bot):
    message_converter: Converter
    db_connection: Connection

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        try:
            self.message_converter = Converter()
            self.db_connection = Connection(
                os.getenv('DB_NAME'),
                os.getenv('DB_USER'),
                os.getenv('DB_PASSWORD'),
                os.getenv('DB_HOST'),
                os.getenv('DB_PORT')
            )

            guild = discord.Object(id=os.getenv('GUILD_ID'))
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to {guild.id}")
        except Exception as e:
            print(f"Error initializing bot: {e}")
            return

        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        user_timezone_str = self.db_connection.get_user(message.author.id)[1]
        if user_timezone_str is None:
            return
        timestamp = self.message_converter.parse_message(message.content, user_timezone_str)
        if timestamp != -1:
            self.db_connection.insert_message(message.id, timestamp)
            await message.add_reaction('🕒')

    async def on_reaction_add(self, reaction, user):
        if user == self.user:
            return

        if reaction.emoji == '🕒':
            message_id = reaction.message.id
            message = self.db_connection.get_message(message_id)
            if message is None:
                return
            
            timestamp = message[1]
            tag = self.message_converter.convert_to_tag(timestamp)
            await reaction.message.channel.send(tag)

        
intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix='!', intents=intents)

GUILD_ID = discord.Object(id=os.getenv('GUILD_ID'))

@client.tree.command(name='set-me', description='Set your timezone', guilds=[GUILD_ID])
async def set_me(interaction: discord.Interaction, timezone: str):
    if (not client.message_converter.verify_timezone(timezone)):
        await interaction.response.send_message('Invalid timezone format. Please use UTC+/-X', ephemeral=True)
        return
    if (client.db_connection.get_user(interaction.user.id) is not None):
        client.db_connection.delete_user(interaction.user.id)
    client.db_connection.insert_user(interaction.user.id, timezone)
    await interaction.response.send_message(f'Timezone set to {timezone}', ephemeral=True)

@client.tree.command(name='remove-me', description='Remove your timezone', guilds=[GUILD_ID])
async def remove_me(interaction: discord.Interaction):
    client.db_connection.delete_user(interaction.user.id)
    await interaction.response.send_message('Timezone removed', ephemeral=True)

client.run(token)
