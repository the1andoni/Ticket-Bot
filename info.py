import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import platform
import psutil
import os


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.bot.user in message.mentions:
            embed = discord.Embed(title="👋 | Bot-Informationen", color=discord.Color.blue())
            embed.add_field(name="⚙️ | Entwickler", value="<@397777058727460875> [YoungGreed]", inline=False)
            embed.add_field(name="💬 | Prefix", value="/", inline=False)
            embed.add_field(name="⏱️ | Uptime", value=self.get_bot_uptime(), inline=False)
            embed.add_field(name="📶 | Ping", value=f"{round(self.bot.latency * 1000)} ms", inline=False)
            embed.add_field(name="🖥️ | Hardware", value=self.get_bot_hardware(), inline=False)
            embed.set_footer(text="Headmanager [CandyMC]", icon_url=self.bot.user.avatar.url)

            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1142916965845971049/1143475401889431572/d699d07b10e8eadcd5edc40de6a105f6.png") #Wenn du einen Link benutzt kannst du attachment://Boticon.png weglassen und in denn "LINK" einfach denn Link einfügen, ansonst oben denn Filenamen angeben denn du oben bei filename hinzugefügt hast und davor attachment:// schreiben

            await message.channel.send(embed=embed)

    def get_bot_uptime(self):
        now = datetime.now(timezone.utc)
        delta = now - self.bot.user.created_at
        Tage = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{Tage} Tage, {hours}:{minutes:02d} Stunden"
        return uptime

    def get_bot_hardware(self):
        system = platform.system()
        if system == "Windows":
            return f"*CPU:* `{psutil.cpu_percent()}%`\n*RAM:* `{psutil.virtual_memory().used >> 20} MB`"
        elif system == "Linux":
            return f"*CPU:* `{psutil.cpu_percent()}%`\n*RAM:* `{psutil.virtual_memory().used >> 20} MB`"
        else:
            return "Unknown"


def setup(bot):
    bot.add_cog(Info(bot))