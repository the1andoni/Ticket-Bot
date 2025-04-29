import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('reaction_roles.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reaction_roles (
                message_id INTEGER,
                emoji TEXT,
                role_id INTEGER,
                PRIMARY KEY (message_id, emoji)
            )
        ''')
        self.conn.commit()
    
    async def not_manage_roles(self, interaction):
        await interaction.response.send_message('Du hast keine Berechtigung, Rollen zu verwalten.', ephemeral=True)

    @app_commands.command(name="reaction-roles-add", description="fügt eine neue Reaktionsrolle hinzu")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reaction_role_add(self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):
        try:
            message_id = int(message_id)
            message = await self.bot.get_channel(interaction.channel_id).fetch_message(message_id)
            await message.add_reaction(emoji)
            self.cursor.execute('INSERT INTO reaction_roles VALUES (?, ?, ?)', (message_id, emoji, role.id))
            self.conn.commit()
            await interaction.response.send_message('Reaktion-Rolle hinzugefügt!', ephemeral=True)
        except (discord.HTTPException, ValueError):
            await interaction.response.send_message('Fehler beim Hinzufügen der Reaktion oder ungültige Message ID.', ephemeral=True)

    @app_commands.command(name="reaction-role-remove", description="Entfernt eine Reaktionsrolle")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def reaction_role_remove(self, interaction: discord.Interaction, message_id: str, emoji: str):
        try:
            message_id = int(message_id)
            self.cursor.execute('DELETE FROM reaction_roles WHERE message_id = ? AND emoji = ?', (message_id, emoji))
            self.conn.commit()
            await interaction.response.send_message('Reaktion-Rolle entfernt!', ephemeral=True)
        except ValueError:
            await interaction.response.send_message('Ungültige Message ID.', ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.member.bot:
            message_id = payload.message_id
            emoji = str(payload.emoji)
            self.cursor.execute('SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?', (message_id, emoji))
            role_id = self.cursor.fetchone()
            if role_id:
                role = payload.member.guild.get_role(role_id[0])
                await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        message_id = payload.message_id
        emoji = str(payload.emoji)
        self.cursor.execute('SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?', (message_id, emoji))
        role_id = self.cursor.fetchone()
        if role_id:
            role = guild.get_role(role_id[0])
            await member.remove_roles(role)

def setup(bot):
    bot.add_cog(ReactionRoles(bot))