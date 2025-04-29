import discord
import asyncio
import json
import datetime
import psutil
import youtube_dl

from discord.ext import commands
from discord import app_commands
from music import MusicView

intents = discord.Intents.default()
intents.voice_states = True
bot = commands.Bot(command_prefix=".!", intents =intents)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def test(self, ctx, arg):
        await ctx.reply("Ich bin nur ein Test, du Opfer")

#USERINFO BEFEHL
    @app_commands.command(name="mitglieder_info", description="Gibt dir Infos über einen Nutzer")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        user = member or interaction.user
        date_format = "%a, %d %b %Y %I:%M %p"
        embed = discord.Embed(color=0xdfa3ff, description=user.mention)
        embed.set_author(name=str(user), icon_url=user.avatar.url)
        embed.set_thumbnail(url=user.avatar.url)
        embed.add_field(name="Joined", value=user.joined_at.strftime(date_format))
        members = sorted(interaction.guild.members, key=lambda m: m.joined_at)
        embed.add_field(name="Join position", value=str(members.index(user) + 1))
        embed.add_field(name="Registered", value=user.created_at.strftime(date_format))
        if len(user.roles) > 1:
            role_string = ' '.join([r.mention for r in user.roles][1:])
            embed.add_field(name="Roles [{}]".format(len(user.roles) - 1), value=role_string, inline=False)
        perm_string = ', '.join([str(p[0]).replace("_", " ").title() for p in user.guild_permissions if p[1]])
        embed.add_field(name="Guild permissions", value=perm_string, inline=False)
        embed.set_footer(text='ID: ' + str(user.id))
        await interaction.response.send_message(embed=embed, ephemeral=True)


#Rolle Vergeben Befehl
    @app_commands.command(name="rolle_vergeben", description="Vergibt eine Rolle an einen Nutzer")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def vergebe_rolle(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        await interaction.response.send_message(f"Die Rolle {role.name} wurde an {member.display_name} vergeben.", ephemeral=True)
        print(f"Rolle {role.name} was given to {member.display_name}")
    

#Rolle entfernen Befehl
    @app_commands.command(name="rolle_entfernen", description="Entfernt einem Nutzer eine Rolle")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rolle_entfernen(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"Die Rolle {role.name} wurde erfolgreich entfernt.", ephemeral=True)
            print(f"Role {role.name} was removed from {member.display_name}")
        else:
            await interaction.response.send_message(f"{member.mention} hat die Rolle {role.name} nicht.", ephemeral=True)

#NACHRICHT LÖSCHEN BEFEHL
    @app_commands.command(name="nachricht_löschen", description="Löscht Nachrichten")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def deletemessage(self, interaction: discord.Interaction, number: int, member: discord.Member = None):
        try:
            delete_counter = 0
            await interaction.response.send_message("Wird gemacht.", ephemeral=True)
            async for message in interaction.channel.history():
                if message.author == member or member is None:
                    await message.delete()
                    delete_counter += 1
                    if delete_counter == number:
                        break
                    await asyncio.sleep(1)
        except discord.app_commands.errors.MissingPermissions as e:
            error_message = f"{interaction.user.mention} fehlen die Rechte für diesen Befehl."
            print(error_message)  # Ausgabe in der Bot-Konsole
            await interaction.response.send_message(error_message, ephemeral=True)


#Music Radio Befehl 
    @app_commands.command(name="radio",description="Spielt Radiosender ab")
    async def music(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=MusicView(), ephemeral=True)

#Commands Syncen
    @app_commands.command(name="sync_commands",description="Synchronisiert die Command.py mit der Discord API")
    @app_commands.checks.has_role("🧑‍💻Dev")
    async def sync_commands(self, interaction: discord.Interaction):
        try :
            synced = bot.commands.update()
            await interaction.response.send_message(f"Commands have been synced", ephemeral=True)
            print(f"Synced {synced} command(s)")
        except Exception as e:
            print(e)


# Bot Info Befehl
    @app_commands.command(name="botinfo", description="Shows Infos about the Bot")
    async def botinfo(self, interaction: discord.Interaction):
        # Berechne genutzten RAM
        process = psutil.Process()
        ram_usage = process.memory_full_info().rss / 1024 ** 2  # in MB umrechnen

        # Berechne die Uptime seit dem letzten Reboot (Start)
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())

        embed = discord.Embed(title=":information_source: BOT INFORMATION :information_source:", color=0xf82c00)
        embed.add_field(name="Developer(s)", value="YoungGreed", inline=False)
        embed.add_field(name="Bot version", value="v1_5", inline=False)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=False)
        embed.add_field(name="Bot RAM usage", value=f"{ram_usage:.2f} MB", inline=False)
        embed.add_field(name="Built with", value="Python", inline=False)
        embed.add_field(name="This bot was created on (MM/DD/YYYY)", value="07/01/2023 16:28", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

#Einladungslink senden
    @app_commands.command(name="einladungslink", description="Sendet den Einladungslink für den Bot")
    async def einladungslink(self,interaction: discord.Interaction):
        await interaction.response.send_message(f"*Bitte beachte das der Bot über den Rollen stehen muss die er vergeben darf.* Einladungslink:https://discord.com/oauth2/authorize?client_id=1127168100094181448&permissions=37368853167217&scope=bot", ephemeral=True)
        print("Einladungslink gesendet")
    
async def setup(bot):
    await bot.add_cog(Commands(bot))


#CHANGELOG
#V1_0 Addet Slash Command (delete Message)
#V1_1 Addet Slash Command (let me say something)
#V1_2 Addet Slash Command (User Info)
#V1_3 Addet Slash Command (Add/Remove Role)
#1_4 Addet Radio Command
#1_5 Addet Slash COmmands Show Bot Info, Addet Einladungslink senden (Bot)
#1_6 Addet Private Channel

