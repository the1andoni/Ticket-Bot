import json
import discord
import asyncio
import sqlite3

from discord.ext import commands
from discord.ext.tasks import loop


from commands import Commands
from voicechat import Voicechat
from log import Log
from reaction_roles import ReactionRoles
from autorole import Autorole
from ticketsystem import TicketCog
from info import Info



intents = discord.Intents.default()
intents.typing = False
intents.members = True
intents.presences = False
intents.message_content = True

bot = commands.Bot(command_prefix=".!", intents=intents)

@bot.event
async def on_ready():
    activity = discord.Game(name="/help")
    await bot.change_presence(activity=activity, status=discord.Status.dnd)
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')
    await bot.add_cog(Commands(bot)) 
    await bot.add_cog(Voicechat(bot))
    await bot.add_cog(Log(bot))
    await bot.add_cog(ReactionRoles(bot))
    await bot.add_cog(Autorole(bot))
    await bot.add_cog(Info(bot))
    await bot.add_cog(TicketCog(bot))
    try :
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message):
    await bot.process_commands(message)



with open("config.json") as config_file:
    config = json.load(config_file)

if __name__ == "__main__":
    bot.run(config["discord_token"])


#CHANGELOG
#V1_0 Addet Slash Command (delete Message)
#V1_1 Addet Slash Command (let me say something)
#V1_2 Addet Slash Command (User Info)
#V1_3 Addet Slash Command (Add/Remove Role)
#V1_4 Addet Radio Command
#V1_5 Addet Bot Info Command, Addet Einladungslink Command
#V1_6 Addet Privat Channels
#V1_7 Addet XP System
#V1_7_1 Optimize the Autorole.py
#V1_8 Ready for Release