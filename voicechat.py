import discord
import asyncio
from discord.ext import commands
from discord import app_commands


intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True

class Voicechat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.private_channels = {}  # Dictionary zur Verfolgung der privaten Kanäle
        # Warte auf den Bot-Start
        bot.loop.create_task(self.delete_empty_private_channels())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel.name == "Voice Erstellen":
            # Erstellt einen privaten Sprachkanal und fügt das Mitglied hinzu
            category = after.channel.category
            overwrites = {
                category.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True),
                self.bot.user: discord.PermissionOverwrite(read_messages=True)  # Bot-Berechtigung hinzufügen
            }
            voice_channel = await category.create_voice_channel(f"Privater Kanal {member.display_name}", overwrites=overwrites)
            await member.move_to(voice_channel)
            self.private_channels[member.id] = voice_channel


    async def update_channel_permissions(self, member_id, read_messages):
        voice_channel = self.private_channels.get(member_id)
        if voice_channel:
            overwrites = voice_channel.overwrites
            overwrites[voice_channel.guild.default_role].update(read_messages=read_messages)
            await voice_channel.edit(overwrites=overwrites)

    @app_commands.command(name="voice-hide", description="Blende den Channel für andere aus")
    async def voicehide(self, interaction: discord.Interaction):
        await self.update_channel_permissions(interaction.user.id, read_messages=False)
        await interaction.response.send_message("Dein privater Kanal ist jetzt unsichtbar.", ephemeral=True)

    @app_commands.command(name="voice-reveal", description="Macht den Channel öffentlich für *jeden* User")
    async def voicereveal(self, interaction: discord.Interaction):
        await self.update_channel_permissions(interaction.user.id, read_messages=True)
        await interaction.response.send_message("Dein privater Kanal ist jetzt sichtbar.", ephemeral=True)

    @app_commands.command(name="voice-rename", description="Damit kannst du deinen Kanal umbenennen")
    async def kanelumbenennen(self, interaction: discord.Interaction, *, name: str):
        voice_channel = self.private_channels.get(interaction.user.id)
        if voice_channel:
            await voice_channel.edit(name=name)
            await interaction.response.send_message(f"Der Name deines privaten Kanals wurde zu '{name}' geändert.",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("Du bist in keinem privaten Kanal.", ephemeral=True)

    @app_commands.command(name="voice-limit", description="Ändert das Limit der Nutzer im Kanal")
    async def voicelimit(self, interaction: discord.Interaction, limit: int):
        voice_channel = self.private_channels.get(interaction.user.id)
        if voice_channel:
            await voice_channel.edit(user_limit=limit)
            await interaction.response.send_message(f"Das Limit deines privaten Kanals wurde auf {limit} geändert.",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message("Du bist in keinem privaten Kanal.", ephemeral=True)

    @app_commands.command(name="voice-transfer", description="Überträgt den Besitzer des Kanals an einen anderen Nutzer")
    async def voicetransfer(self, interaction: discord.Interaction, member: discord.Member):
        voice_channel = self.private_channels.get(interaction.user.id)
        if voice_channel:
            print("Current Overwrites:", voice_channel.overwrites)
            if member.voice and member.voice.channel == voice_channel:
                overwrites = voice_channel.overwrites
                everyone_overwrite = overwrites.get(voice_channel.guild.default_role)
                
                if interaction.user in overwrites:
                    overwrites[interaction.user].update(manage_channels=False, manage_permissions=False)
                else:
                    overwrites[interaction.user] = discord.PermissionOverwrite(manage_channels=False, manage_permissions=False)
                    
                if member not in overwrites:
                    overwrites[member] = discord.PermissionOverwrite(manage_channels=True, manage_permissions=True)
                else:
                    overwrites[member].update(manage_channels=True, manage_permissions=True)
                
                if everyone_overwrite is not None:
                    overwrites[voice_channel.guild.default_role] = everyone_overwrite
                
                try:
                    await voice_channel.edit(overwrites=overwrites)
                    await interaction.response.send_message(f"Der Eigentümer des Kanals wurde auf {member.display_name} übertragen.",
                                                            ephemeral=True)
                except discord.NotFound as e:
                    print("Error:", e)
                    await interaction.response.send_message("Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.",
                                                            ephemeral=True)
            else:
                await interaction.response.send_message("Der angegebene Nutzer muss im selben Voice-Kanal sein, um den Eigentümer zu übertragen.",
                                                        ephemeral=True)
        else:
            await interaction.response.send_message("Du bist in keinem privaten Kanal.", ephemeral=True)


    @app_commands.command(name="voice-kick", description="Wirft einen Nutzer aus dem Kanal")
    async def voicekick(self, interaction: discord.Interaction, member: discord.Member):
        voice_channel = self.private_channels.get(interaction.user.id)
        if voice_channel:
            if member.voice and member.voice.channel == voice_channel:
                await member.move_to(None)
                await interaction.response.send_message(f"{member.display_name} wurde aus dem Kanal geworfen.", ephemeral=True)
            else:
                await interaction.response.send_message(f"{member.display_name} ist nicht im selben Voice-Kanal.", ephemeral=True)
        else:
            await interaction.response.send_message("Du bist in keinem privaten Kanal.", ephemeral=True)

    @app_commands.command(name="voice-ban", description="Bannt einen Nutzer aus dem Kanal")
    async def voiceban(self, interaction: discord.Interaction, member: discord.Member):
        voice_channel = self.private_channels.get(interaction.user.id)
        if voice_channel:
            if member.voice and member.voice.channel == voice_channel:
                await member.move_to(None)  # Entferne den Benutzer aus dem Sprachkanal
                overwrites = voice_channel.overwrites
                if member in overwrites:
                    overwrites[member].update(read_messages=False)
                else:
                    overwrites[member] = discord.PermissionOverwrite(read_messages=False)
                await voice_channel.edit(overwrites=overwrites)
                await interaction.response.send_message(f"{member.display_name} wurde aus dem Kanal gebannt.", ephemeral=True)
            else:
                await interaction.response.send_message(f"{member.display_name} ist nicht im selben Voice-Kanal.", ephemeral=True)
        else:
            await interaction.response.send_message("Du bist in keinem privaten Kanal.", ephemeral=True)

    @app_commands.command(name="voice-delete", description="Löscht deinen privaten Kanal sofort")
    async def voicedelete(self, interaction: discord.Interaction):
        voice_channel = self.private_channels.get(interaction.user.id)
        if voice_channel:
            await voice_channel.delete()
            del self.private_channels[interaction.user.id]
            await interaction.response.send_message("Dein privater Kanal wurde gelöscht.", ephemeral=True)
        else:
            await interaction.response.send_message("Du bist in keinem privaten Kanal.", ephemeral=True)

    @app_commands.command(name="voice-clean", description="Löscht alle leeren privaten Voice-Kanäle")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def voiceclean(self, interaction: discord.Interaction):
        empty_channels = [channel for channel in self.private_channels.values() if len(channel.members) == 0]
        for channel in empty_channels:
            await channel.delete()
            del self.private_channels[next(key for key, value in self.private_channels.items() if value == channel)]

        await interaction.response.send_message("Alle leeren privaten Voice-Kanäle wurden gelöscht.", ephemeral=True)

    async def delete_empty_private_channels(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            empty_channels = [channel for channel in self.private_channels.values() if len(channel.members) == 0]
            for channel in empty_channels:
                await channel.delete()
                del self.private_channels[
                    next(key for key, value in self.private_channels.items() if value == channel)]
            await asyncio.sleep(300)  # 300 Sekunden (5 Minuten) warten, bevor erneut nach leeren Kanälen gesucht wird


def setup(bot):
    bot.add_cog(Voicechat(bot))