from python.uiclasses import ApprAckDeny, ApproveDenyHit, InacApprDeny
from python.helpers import runIDsync, get_local_path
from discord import Intents, Object, Message
from python.backendconsole import backend
from discord.ext import commands
import data.config as cfg
import threading
import json
import time

bot = commands.Bot(command_prefix="!?!?!", intents=Intents.all())
thread = threading.Thread(target=runIDsync, args=[bot], daemon=True)
consolethread = threading.Thread(target=backend, args=[bot.tree], daemon=True)

@bot.event
async def on_message(message: Message):
    # activity record shtuff
    try:
        # if the message is in main SC activity record and send by the metaOS bot
        if message.guild.id == 588427075283714049 and message.channel.id == 618536300860932134:
            
            # Make sure it has their total time - should have END in the author name
            if "END" in message.embeds[0].author.name:

                # parse name
                user = message.embeds[0].author.name.replace("SESSION END", "").strip().strip("()")
                print(f"{user=}")

                # parse total time
                totaltime = int(message.embeds[0].fields[1].value.replace("minute(s)", "").strip())
                print(f"{totaltime=}")

                # update the db
                with open(get_local_path("data/totaltimes.json"), "r") as f:
                    totaltimes:dict = json.load(f)
                    f.close()
                with open(get_local_path("data/totaltimes.json"), "w") as f:
                    try:
                        totaltimes[user] = totaltime
                    except:
                        totaltimes.update({user : totaltime})
                    json.dump(totaltimes, f, indent=2)
                    f.close()
    except:
        None



@bot.event
async def on_ready():

    # import global commands and suites
    import python.commands.universal.usersuite as usersuite
    import python.commands.universal.quotasuite as QuotaSuite
    import python.commands.universal.shopitems as shopitems
    import python.commands.universal.rosterfuncsuite as RosterFuncSuite
    import python.commands.ntshblacklistsuite as ntshbl
    import python.commands.ntshhitsuite as HitSuite
    import python.commands.universal.inactivitysuite as InacSuite
    import python.commands.mfpointssuite as MFPointsSuite

    # import guild commands
    import python.commands.update as update
    import python.commands.honorshop as shop
    import python.commands.coupon as coupon
    import python.commands.universal.strike as Strike
    
    globalcommands = [usersuite.setup,
                      QuotaSuite.setup,
                      RosterFuncSuite.setup,
                      HitSuite.setup,
                      ntshbl.setup,
                      shopitems.setup,
                      InacSuite.setup,
                      MFPointsSuite.setup
                      ]
    
    guildcommands = [shop, coupon, Strike]
    
    guilds = []
    print(f"[Setup] Starting")

    # adding persistant buttons
    bot.add_view(ApprAckDeny())
    bot.add_view(ApproveDenyHit())
    bot.add_view(InacApprDeny())
    print(f"[Setup]{cfg.Success} Persistant views added")
    
    # registering the globals
    for x in globalcommands:
        x(bot.tree)
    print(f"[Setup]{cfg.Success} Global commands setup")
    
    # register guild commands
    for x in guildcommands:
        for gid in x.GUILD_IDS:
            x.setup(bot.tree, guild=Object(id=gid))
            if gid not in guilds:
                guilds.append(gid)
    print(f"[Setup]{cfg.Success} Guild commands setup")

    # Sync global commands
    await bot.tree.sync()
    print(f"[Setup]{cfg.Success} Global command sync")

    # Sync guild commands
    for gid in guilds:
        await bot.tree.sync(guild=Object(id=gid))
        print(f"[Setup]{cfg.Success} Synced guild commands for {gid}: {bot.get_guild(gid).name}")

    print(f"[Setup]{cfg.Success} Finished")
    # thread.start()
    consolethread.start()

while True:
    try:
        bot.run(cfg.BOTTOKEN)
        break
    except KeyboardInterrupt:
        break
    except:
        time.sleep(5)