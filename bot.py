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
        except Exception as e:
            traceback.print_exc()
            return

        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        user_timezone_str = self.db_connection.get_user(message.author.id)[1]
        if user_timezone_str is None:
            return
        timestamp = converter_utils.parse_message(message.content, user_timezone_str)
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
            tag = converter_utils.convert_to_tag(timestamp)
            await reaction.message.channel.send(tag)

        
intents = discord.Intents.default()
intents.message_content = True
client = Client(command_prefix='!', intents=intents)

@client.tree.command(name='set-me', description='Set your timezone')
async def set_me(interaction: discord.Interaction, timezone: str):
    if (not converter_utils.verify_timezone(timezone)):
        await interaction.response.send_message('Invalid timezone format. Please use UTC+/-X', ephemeral=True)
        return
    if (client.db_connection.get_user(interaction.user.id) is not None):
        client.db_connection.delete_user(interaction.user.id)
    client.db_connection.insert_user(interaction.user.id, timezone)
    await interaction.response.send_message(f'Timezone set to {timezone}', ephemeral=True)

@client.tree.command(name='remove-me', description='Remove your timezone')
async def remove_me(interaction: discord.Interaction):
    client.db_connection.delete_user(interaction.user.id)
    await interaction.response.send_message('Timezone removed', ephemeral=True)

print("Starting bot")
client.run(token)
