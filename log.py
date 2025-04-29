import discord
from discord.ext import commands
import sqlite3
from datetime import datetime, timezone
from discord import app_commands


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_log_channel_id = None
        self.conn = sqlite3.connect('log_channels.db')  # Datenbankverbindung
        self.cursor = self.conn.cursor()

        # Erstelle die Tabelle, wenn sie noch nicht existiert
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS log_channels (
                            server_id INTEGER PRIMARY KEY,
                            channel_id INTEGER
                            )''')
        self.conn.commit()

        # Tabelle nur erstellen, wenn sie nicht existiert
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS users (member_id TEXT PRIMARY KEY, xp INTEGER DEFAULT 0, guild_id TEXT)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS ignored_channels (channel_id TEXT PRIMARY KEY)")
        self.conn.commit()
        # Füge das Feld total_xp hinzu, falls es noch nicht existiert
        try:
            self.cursor.execute("SELECT total_xp FROM users LIMIT 1")
        except sqlite3.OperationalError:
            self.cursor.execute("ALTER TABLE users ADD COLUMN total_xp INTEGER DEFAULT 0")
            self.conn.commit()

        # Lade die Log-Kanal-IDs für jeden Server aus der Datenbank
        self.log_channels = self.load_log_channels()

    def load_log_channels(self):
        self.cursor.execute("SELECT server_id, channel_id FROM log_channels")
        rows = self.cursor.fetchall()
        return {row[0]: row[1] for row in rows}

    def set_log_channel(self, server_id, channel_id):
        self.cursor.execute("INSERT OR REPLACE INTO log_channels (server_id, channel_id) VALUES (?, ?)", (server_id, channel_id))
        self.conn.commit()

    # Befehl: /set-log-channel [Channel]
    @app_commands.command(name="set-log-channel", description="Setze den Kanal, in dem die Logs gesendet werden sollen.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_log_channel_command(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.set_log_channel(interaction.guild.id, channel.id)
        self.log_channels[interaction.guild.id] = channel.id  # Update the log_channels dictionary
        await interaction.response.send_message(f"Der Kanal {channel.mention} wurde als BotLog-Kanal für diesen Server festgelegt.", ephemeral=True)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        # Channel-Erstellung protokollieren
        if isinstance(channel, discord.TextChannel) and channel.guild and channel.guild.id in self.log_channels:
            log_channel_id = self.log_channels[channel.guild.id]
            embed = discord.Embed(
                title=':pencil:Textchannel erstellt',
                description=f'Neuer Textkanal erstellt: {channel.mention}',
                color=discord.Color.green()
            )
            embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")}')
            await self.bot.get_channel(log_channel_id).send(embed=embed)

        elif isinstance(channel, discord.VoiceChannel) and channel.guild and channel.guild.id in self.log_channels:
            log_channel_id = self.log_channels[channel.guild.id]
            embed = discord.Embed(
                title=':microphone2:Voicechannel erstellt',
                description=f'Neuer Sprachkanal erstellt: {channel.name}',
                color=discord.Color.green()
            )
            embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")}')
            await self.bot.get_channel(log_channel_id).send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        # Kanallöschung protokollieren
        if isinstance(channel, discord.TextChannel) and channel.guild and channel.guild.id in self.log_channels:
            log_channel_id = self.log_channels[channel.guild.id]
            embed = discord.Embed(
                title=':wastebasket:Textchannel gelöscht',
                description=f'Ein Textkanal wurde gelöscht: {channel.mention}',
                color=discord.Color.red()
            )
            embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")}')
            await self.bot.get_channel(log_channel_id).send(embed=embed)

        elif isinstance(channel, discord.VoiceChannel) and channel.guild and channel.guild.id in self.log_channels:
            log_channel_id = self.log_channels[channel.guild.id]
            embed = discord.Embed(
                title=':wastebasket:Voicechannel gelöscht',
                description=f'Ein Sprachkanal wurde gelöscht: {channel.name}',
                color=discord.Color.red()
            )
            embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")}')
            await self.bot.get_channel(log_channel_id).send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Überprüfe, ob die Mitgliedsänderung im gleichen Server stattgefunden hat wie der Log-Kanal
        if before.guild.id in self.log_channels:
            log_channel_id = self.log_channels[before.guild.id]
            member = after  # Korrekter Parametername ist "after"
            
            if len(before.roles) < len(after.roles):
                added_roles = [role for role in after.roles if role not in before.roles]
                if added_roles:
                    role_mentions = ', '.join(role.mention for role in added_roles)
                    embed = discord.Embed(
                        title=':crossed_swords:Rollen vergeben',
                        description=f'{after.mention} hat folgende Rollen erhalten: {role_mentions}',
                        color=discord.Color.blue()
                    )
                    embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")} | Member ID: {member.id}')
                    if after.avatar:
                        embed.set_thumbnail(url=after.avatar.url)
                    await self.bot.get_channel(log_channel_id).send(embed=embed)
            
            if len(before.roles) > len(after.roles):
                removed_roles = [role for role in before.roles if role not in after.roles]
                if removed_roles:
                    role_mentions = ', '.join(role.mention for role in removed_roles)
                    embed = discord.Embed(
                        title=':crossed_swords:Rollen entfernt',
                        description=f'{after.mention} hat folgende Rollen verloren: {role_mentions}',
                        color=discord.Color.red()
                    )
                    embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")} | Member ID: {member.id}')
                    if after.avatar:
                        embed.set_thumbnail(url=after.avatar.url)
                    await self.bot.get_channel(log_channel_id).send(embed=embed)
            
            if before.nick != after.nick:
                embed = discord.Embed(
                    title=':exclamation: Nickname geändert',
                    description=f'{after.mention} hat den Nicknamen von **{before.nick if before.nick else "keinem"}** zu **{after.nick if after.nick else "keinem"}** geändert.',
                    color=discord.Color.purple()
                )
                embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")} | Member ID: {member.id}')
                if after.avatar:
                    embed.set_thumbnail(url=after.avatar.url)
                await self.bot.get_channel(log_channel_id).send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Sprachchannelbeitritt protokollieren
        if before.channel != after.channel and member.guild:
            log_channel_id = self.log_channels.get(member.guild.id)
            if log_channel_id:
                if after.channel:
                    embed = discord.Embed(
                        title='Sprachchannel beigetreten',
                        description=f'{member.mention} ist dem Sprachkanal {after.channel.mention} beigetreten.',
                        color=discord.Color.green() 
                    )
                    embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")} | Member ID: {member.id}')
                    if member.avatar:
                        embed.set_thumbnail(url=member.avatar.url)
                    await self.bot.get_channel(log_channel_id).send(embed=embed)
                else:
                    embed = discord.Embed(
                        title='Sprachchannel verlassen',
                        description=f'{member.mention} hat den Sprachkanal {before.channel.mention} verlassen.',
                        color=discord.Color.red()
                    )
                    embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")} | Member ID: {member.id}')
                    if member.avatar:
                        embed.set_thumbnail(url=member.avatar.url)
                    await self.bot.get_channel(log_channel_id).send(embed=embed)


    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Überprüfe, ob der Mitgliederbeitritt im gleichen Server stattgefunden hat wie der Log-Kanal
        if member.guild.id in self.log_channels:
            # Mitglied beigetreten protokollieren
            embed = discord.Embed(
                title=':inbox_tray:Mitglied beigetreten',
                description=f'{member.mention} ist dem Server beigetreten.',
                color=discord.Color.green()
            )
            embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")} | Member ID: {member.id}')

            # Berechne die Zeitdifferenz seit der Kontoerstellung
            account_age = datetime.utcnow().replace(tzinfo=timezone.utc) - member.created_at
            embed.add_field(name='Account erstellt', value=f'{account_age.days} Tage, {account_age.seconds // 3600} Stunden, {account_age.seconds % 3600 // 60} Minuten', inline=False)

            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            await self.bot.get_channel(self.log_channels[member.guild.id]).send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Überprüfe, ob der Mitgliederaustritt im gleichen Server stattgefunden hat wie der Log-Kanal
        if member.guild.id in self.log_channels:
            log_channel_id = self.log_channels[member.guild.id]
            # Mitglied verlassen protokollieren
            embed = discord.Embed(
                title=':outbox_tray:Mitglied verlassen',
                description=f'{member.mention} hat den Server verlassen.',
                color=discord.Color.red()
            )
            embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")} | Member ID: {member.id}')
            if member.avatar:
                embed.set_thumbnail(url=member.avatar.url)
            await self.bot.get_channel(log_channel_id).send(embed=embed)
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        if role.guild.id in self.log_channels:
            log_channel_id = self.log_channels[role.guild.id]
            color = role.color
            hoisted = role.hoist
            mentionable = role.mentionable

            # Farbe, Hochgezogen und Erwähnbar in lesbaren Text umwandeln
            color_str = f'#{color.value:06x}'
            hoisted_str = 'Ja' if hoisted else 'Nein'
            mentionable_str = 'Ja' if mentionable else 'Nein'

            # Rolle hinzugefügt protokollieren
            embed = discord.Embed(
                title=':crossed_swords:Rolle erstellt',
                description=f'Die Rolle {role.mention} wurde erstellt.',
                color=discord.Color.green()
            )
            embed.add_field(name='Farbe', value=color_str, inline=True)
            embed.add_field(name='Hochgezogen', value=hoisted_str, inline=True)
            embed.add_field(name='Erwähnbar', value=mentionable_str, inline=True)
            embed.add_field(name='Berechtigungen', value=', '.join(perm for perm, value in role.permissions), inline=False)
            embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")}')
            await self.bot.get_channel(log_channel_id).send(embed=embed)


    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if role.guild.id in self.log_channels:
            log_channel_id = self.log_channels[role.guild.id]
            # Rolle gelöscht protokollieren
            embed = discord.Embed(
                title=':wastebasket:Rolle gelöscht',
                description=f'Die Rolle **{role.name}** wurde entfernt.',
                color=discord.Color.red()
            )
            # Farbe, Hochgezogen und Erwähnbar in lesbaren Text umwandeln
            color_str = f'#{role.color.value:06x}'
            hoisted_str = 'Ja' if role.hoist else 'Nein'
            mentionable_str = 'Ja' if role.mentionable else 'Nein'
            
            embed.add_field(name='Farbe', value=color_str, inline=True)
            embed.add_field(name='Hochgezogen', value=hoisted_str, inline=True)
            embed.add_field(name='Erwähnbar', value=mentionable_str, inline=True)
            embed.add_field(name='Berechtigungen', value=', '.join(perm for perm, value in role.permissions), inline=True)
            embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")}')
            await self.bot.get_channel(log_channel_id).send(embed=embed)
        
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        # Überprüfe, ob die Rolle im gleichen Server stattgefunden hat wie der Log-Kanal
        if after.guild.id in self.log_channels:
            log_channel_id = self.log_channels[after.guild.id]
            # Berechtigungsänderungen protokollieren
            if before.permissions != after.permissions:
                added_perms = [perm for perm in after.permissions if perm not in before.permissions]
                removed_perms = [perm for perm in before.permissions if perm not in after.permissions]
                if added_perms or removed_perms:
                    added_str = ", ".join(perm[0] for perm in added_perms)
                    removed_str = ", ".join(perm[0] for perm in removed_perms)

                    embed = discord.Embed(
                        title=':pencil:Rollenberechtigungen aktualisiert',
                        description=f'Die Berechtigungen für die Rolle {after.mention} wurden aktualisiert.',
                        color=discord.Color.blue()
                    )
                    if added_perms:
                        embed.add_field(name='Hinzugefügte Berechtigungen', value=added_str, inline=False)
                    if removed_perms:
                        embed.add_field(name='Entfernte Berechtigungen', value=removed_str, inline=False)

                    # Weitere Felder für die Rollenupdate-Protokollierung hinzufügen
                    embed.add_field(name='Farbe', value=f'#{after.color.value:06x}', inline=True)
                    embed.add_field(name='Hochgezogen', value='Ja' if after.hoist else 'Nein', inline=True)
                    embed.add_field(name='Erwähnbar', value='Ja' if after.mentionable else 'Nein', inline=True)

                    embed.set_footer(text=f'Datum: {datetime.now().strftime("%d.%m.%Y")} Uhrzeit: {datetime.now().strftime("%H:%M:%S")}')
                    await self.bot.get_channel(log_channel_id).send(embed=embed)


# Füge die Cog dem Bot hinzu
async def setup(bot):
    await bot.add_cog(Log(bot))