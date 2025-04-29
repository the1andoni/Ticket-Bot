import discord
import sqlite3
from discord.ext import commands
from discord import app_commands

class Autorole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('autorole.db')
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_roles (
                guild_id INTEGER PRIMARY KEY,
                user_role INTEGER,
                bot_role INTEGER
            )
        ''')
        self.conn.commit()
    @commands.Cog.listener()
    async def on_member_join(self, member):
        self.cursor.execute('SELECT user_role, bot_role FROM server_roles WHERE guild_id = ?', (member.guild.id,))
        roles = self.cursor.fetchone()
        
        if roles:
            user_role_id, bot_role_id = roles
            
            if not member.bot and user_role_id:
                user_role = member.guild.get_role(user_role_id)
                if user_role:
                    await member.add_roles(user_role)
                    print(f"Benutzerrolle {user_role.name} wurde dem Mitglied {member.name} zugewiesen.")
                else:
                    print(f"Die gespeicherte Benutzerrollen-ID konnte nicht gefunden werden.")
            
            if member.bot and bot_role_id:
                bot_role = member.guild.get_role(bot_role_id)
                if bot_role:
                    await member.add_roles(bot_role)
                    print(f"Botrolle {bot_role.name} wurde dem Bot {member.name} zugewiesen.")
                else:
                    print(f"Die gespeicherte Botrollen-ID konnte nicht gefunden werden.")
        else:
            print(f"Keine Rollen-IDs in der Datenbank gefunden.")

    async def set_role(self, interaction: discord.Interaction, role_type: str, role: discord.Role):
        if role_type == "user":
            column = "user_role"
        elif role_type == "bot":
            column = "bot_role"
        else:
            await interaction.response.send_message('Ungültiger Rollentyp.', ephemeral=True)
            return

        self.cursor.execute(f'SELECT * FROM server_roles WHERE guild_id = ?', (interaction.guild.id,))
        existing_data = self.cursor.fetchone()

        if existing_data:
            self.cursor.execute(f'UPDATE server_roles SET {column} = ? WHERE guild_id = ?', (role.id, interaction.guild.id))
        else:
            self.cursor.execute(f'INSERT INTO server_roles (guild_id, {column}) VALUES (?, ?)', (interaction.guild.id, role.id))

        self.conn.commit()
        print(f"{role_type.capitalize()}rolle für Server {interaction.guild.name} auf {role.name} gesetzt (ID: {role.id})")
        
        # Überprüfe, ob die gespeicherte Rollen-ID korrekt ist
        stored_role_id = self.cursor.execute(f'SELECT {column} FROM server_roles WHERE guild_id = ?', (interaction.guild.id,)).fetchone()
        if stored_role_id:
            stored_id = stored_role_id[0]
            if stored_id == role.id:
                print(f"{role_type.capitalize()}rollen-ID aus der Datenbank: {role.id}")
            else:
                print(f"Die {role_type.capitalize()}rollen-ID wurde nicht korrekt in der Datenbank gespeichert. Gespeichert: {stored_id}, Erwartet: {role.id}")
        else:
            print(f"Keine {role_type.capitalize()}rollen-ID in der Datenbank gefunden.")
        
        await interaction.response.send_message(f'{role_type.capitalize()}rolle wurde auf {role.name} gesetzt.', ephemeral=True)

    @app_commands.command(name="delete-autorole", description="Löscht eine gesetzte Autorolle")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_autorole(self, interaction: discord.Interaction, role_type: str):
        if role_type == "user":
            column = "user_role"
        elif role_type == "bot":
            column = "bot_role"
        else:
            await interaction.response.send_message('Ungültiger Rollentyp.', ephemeral=True)
            return
        
        self.cursor.execute(f'UPDATE server_roles SET {column} = NULL WHERE guild_id = ?', (interaction.guild.id,))
        self.conn.commit()
        print(f"{role_type.capitalize()}rolle für Server {interaction.guild.name} wurde gelöscht.")
        await interaction.response.send_message(f'{role_type.capitalize()}rolle wurde gelöscht.', ephemeral=True)

    @app_commands.command(name="set-autorole-user", description="Setzt die Autorolle eines Benutzers")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_autorole_user(self, interaction: discord.Interaction, *, role: discord.Role):
        await self.set_role(interaction, "user", role)

    @app_commands.command(name="set-autorole-bot", description="Setzt die Autorolle eines Bots")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_autorole_bot(self, interaction: discord.Interaction, *, role: discord.Role):
        await self.set_role(interaction, "bot", role)

    @app_commands.command(name="show-autoroles", description="Zeigt die Gesetzten Rollen")
    @app_commands.checks.has_permissions(administrator=True)
    async def show_autoroles(self, interaction: discord.Interaction):
        self.cursor.execute('SELECT user_role, bot_role FROM server_roles WHERE guild_id = ?', (interaction.guild.id,))
        roles = self.cursor.fetchone()

        if roles:
            user_role_id, bot_role_id = roles
            user_role_name = interaction.guild.get_role(user_role_id).name if user_role_id else 'Nicht gesetzt'
            bot_role_name = interaction.guild.get_role(bot_role_id).name if bot_role_id else 'Nicht gesetzt'

            embed = discord.Embed(title='Aktuelle AutoRoles', color=discord.Color.blue())
            embed.add_field(name=':adult: Benutzerrolle', value=user_role_name, inline=False)
            embed.add_field(name=':robot: Botrolle', value=bot_role_name, inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message('Es wurden noch keine AutoRoles für diesen Server festgelegt.', ephemeral=True)

def setup(bot):
    bot.add_cog(Autorole(bot))