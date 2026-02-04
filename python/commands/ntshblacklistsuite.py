from roblox.partials.partialuser import RequestedUsernamePartialUser as RequestedUsernamePartialUser
from discord import app_commands, Interaction, Embed, Message
from python.helpers import exportSheetData, discord_to_username
from traceback import format_exc
import data.config as cfg
import inspect


COMMAND_NAME = "ntshblacklist"

GUILD_IDS = [
    653542671100411906 #NTSH
]

def setup(tree: app_commands.CommandTree):
    # ntsh blacklist group
    ntshblsuite = app_commands.Group(name="ntshblacklist", description="NTSH Blacklist Management", guild_only=True, guild_ids=GUILD_IDS)
    tree.add_command(ntshblsuite)


    # Adds a blacklist to the NTSH Blacklist Embed, also the ability to edit the blacklists already on the roster.
    # - NTSH Command
    # - Rank Locked
    @ntshblsuite.command(name="add", description="Blacklist a player or Appeal a blacklist.")
    @app_commands.describe(user="Select a user. Case Sensitive!")
    @app_commands.describe(length="Give the blacklist a length.")
    @app_commands.describe(length="Enter a custom length if you selected 'Custom'")
    @app_commands.describe(reason="Enter a reason for the blacklist.")
    @app_commands.describe(auth="This is an Edit Option - The Person Who Appealed The Blacklist.")
    @app_commands.choices(length=[
        app_commands.Choice(name="Permanent", value=1),
        app_commands.Choice(name="Until After Next Tryout", value=2),
        app_commands.Choice(name="2 Tryouts", value=3),
        app_commands.Choice(name="Custom", value=4)])
    async def add(intact: Interaction, user: str, reason: str, length: app_commands.Choice[int], custom: str = None, auth: str = None):
        try:
            # channel = intact.guild.get_channel(1321713301851476048)
            # embed = Embed(title="Official Blacklists from NTSH", description="By default, anyone who is blacklisted from SC/RW is also blacklisted from NTSH.", color=0x862620)
            # embed.set_thumbnail(url=cfg.NTSH_LOGO)
            # await channel.send("**Blacklisted, Ex-communicated personnel, members, and any other players from entering this Task Force Detachment.**\nMessage kept as tribute to JellyGuys1234, our first DI.", embed=embed)
            # return
            await intact.response.defer(thinking=True, ephemeral=True)

            comuser = discord_to_username([str(intact.user.id)])[0]
            roster = exportSheetData()[1][1]
            comuserinfo = roster.members[comuser]

            if comuserinfo["Rank"] == "Task Force Leader" and auth:
                authorization = auth
            else:
                authorization = comuser

            
            print(f"Blacklist Add Command ran by {intact.user} in {intact.guild.name}")
            message: Message = [message async for message in intact.guild.get_channel(1321713301851476048).history(limit=1, oldest_first=True)][0]
            if not length:
                await intact.followup.send("Must enter a length for the blacklist.", ephemeral=True)
                return
            if not reason:
                await intact.followup.send("Must enter a reason for the blacklist.", ephemeral=True)
                return
            if length.name == "Custom" and not custom:
                await intact.followup.send("Must enter a custom length if you select custom!", ephemeral=True)
                return
            index = None
            blacklists = []
            # loads blacklists
            for embed in message.embeds:
                for field in embed.fields:
                    blacklists.append(field.name)
            
            # find if they're in the list
            if f"`{user}`" in blacklists:
                index = blacklists.index(f"`{user}`")
            elif f"`{user}` APPEALED" in blacklists:
                index = blacklists.index(f"`{user}` APPEALED")
            if index != None:
                if comuserinfo["Rank"] != "Task Force Leader" or comuserinfo["TFD"] != "Directorate":
                    intact.followup.send("You can't edit this person's blacklist", ephemeral=True)
                    return
                
                blacklists:list[dict] = []
                for embed in message.embeds:
                    blacklists.append(embed.to_dict())
                # this gets the index of the list and the index of the field at the same fucking time
                i = 0
                while index > 24:
                    i += 1
                    index %= 24
                # remove the appealed part if there is one
                blacklists[i]['fields'][index]['name'] = f"`{user}`"
                
                #update reason
                if reason and custom:
                    blacklists[i]['fields'][index]['value'] = f"```ansi\n[0;37m{reason}\n\n[0;30mLength:[0;31m {custom}\n[0;33mIssued By: [0;34m{authorization}```"
                if reason and not custom:
                    blacklists[i]['fields'][index]['value'] = f"```ansi\n[0;37m{reason}\n\n[0;30mLength:[0;31m {length.name}\n[0;33mIssued By: [0;34m{authorization}```"
                
                # going back to embeds from dicts
                y = 0
                for y in range(len(blacklists)):
                    blacklists[y] = Embed().from_dict(blacklists[y])
            # new blacklist
            else:
                blacklists:list[Embed] = []
                for embed in message.embeds:
                    blacklists.append(embed)

                # add to a blacklist embed
                i = 0
                for embed in blacklists:
                    if len(embed.fields) < 25:
                        if custom:
                            embed.add_field(name=f"`{user}`", value=f"```ansi\n[0;37m{reason}\n\n[0;30mLength:[0;31m {custom}\n[0;33mIssued By: [0;34m{authorization}```", inline=False)
                        else:
                            embed.add_field(name=f"`{user}`", value=f"```ansi\n[0;37m{reason}\n\n[0;30mLength:[0;31m {length.name}\n[0;33mIssued By: [0;34m{authorization}```", inline=False)
                        i = -1
                        
                # if that mf full make a new embed
                if i == 0:
                    embed = Embed(title="Official Blacklists from NTSH", description="By default, anyone who is blacklisted from SC/RW is also blacklisted from NTSH.", color=0x862620)
                    embed.set_thumbnail(cfg.ntsh_logo)
                    blacklists.append(embed)
            # edit the message
            await message.edit(embeds=blacklists)
            await intact.followup.send("Done!", ephemeral=True)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][NTSH Blacklist{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"{cfg.logstamp()}[NTSH Blacklist {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)


    # Marks the blacklist as appealed.
    # - NTSH Command
    # - Rank Locked
    @ntshblsuite.command(name="appeal", description="Appeal a Blacklist.")
    @app_commands.describe(user="The user you want to remove from the blacklists.")
    @app_commands.describe(auth="This is an Edit Option - The Person Who Appealed The Blacklist.")
    async def appeal(intact: Interaction, user: str, auth: str = None):
        try:
            # channel = intact.guild.get_channel(1321713301851476048)
            # embed = Embed(title="Official Blacklists from NTSH", description="By default, anyone who is blacklisted from SC/RW is also blacklisted from NTSH.", color=0x862620)
            # embed.set_thumbnail(url=cfg.NTSH_LOGO)
            # await channel.send("**Blacklisted, Ex-communicated personnel, members, and any other players from entering this Task Force Detachment.**\nMessage kept as tribute to JellyGuys1234, our first DI.", embed=embed)
            # return
            await intact.response.defer(thinking=True, ephemeral=True)

            comuser = discord_to_username([str(intact.user.id)])[0]
            roster = exportSheetData()[1][1]
            comuserinfo = roster.members[comuser]

            if comuserinfo["Rank"] == "Task Force Leader" and auth:
                authorization = auth
            else:
                authorization = comuser
            
            print(f"Blacklist Appeal Command ran by {intact.user} in {intact.guild.name}")
            message: Message = [message async for message in intact.guild.get_channel(1321713301851476048).history(limit=1, oldest_first=True)][0]
            
            blacklists = []
            index = None
            message: Message = [message async for message in intact.guild.get_channel(1321713301851476048).history(limit=1, oldest_first=True)][0]
            for embed in message.embeds:
                for field in embed.fields:
                    blacklists.append(field.name)
            if f"`{user}`" in blacklists:
                index = blacklists.index(f"`{user}`")
            elif f"`{user}` APPEALED" in blacklists:
                await intact.followup.send("This user is already appealed!", ephemeral=True)
                return
            if index != None:
                if comuserinfo["Rank"] not in ("Task Force Leader", "Detachment Instructor") or comuserinfo["TFD"] != "Directorate":
                    intact.followup.send("You can't edit this person's blacklist", ephemeral=True)
                    return
                blacklists:list[dict] = []
                for embed in message.embeds:
                    blacklists.append(embed.to_dict())
                i = 0
                while index > 24:
                    i += 1
                    index %= 24
                blacklists[i]['fields'][index]['name'] = f"`{user}` APPEALED"
                blacklists[i]['fields'][index]['value'] = blacklists[i]['fields'][index]['value'].rstrip("```")
                blacklists[i]['fields'][index]['value'] = f"{blacklists[i]['fields'][index]['value']}\n[0;31mAppealed By: [0;34m{authorization}```"

                y = 0
                for y in range(len(blacklists)):
                    blacklists[y] = Embed().from_dict(blacklists[y])
                await message.edit(embeds=blacklists)
            await intact.followup.send("Done!", ephemeral=True)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][NTSH Blacklist{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"{cfg.logstamp()}[NTSH Blacklist {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)



    @ntshblsuite.command(name="remove", description="TFL Only, can remove a blacklist log.")
    @app_commands.describe(user="The user you want to remove from the blacklists.")
    async def remove(intact: Interaction, user: str):
        try:
            comuser = discord_to_username([str(intact.user.id)])[0]
            roster = exportSheetData()[1][1]
            comuserinfo = roster.members[comuser]
            print(f"Blacklist Appeal Command ran by {intact.user} in {intact.guild.name}")
            if "Task Force Leader" != comuserinfo["Rank"]:
                intact.response.send_message("You're not authorized to use this command.", ephemeral=True)
                return
            message: Message = [message async for message in intact.guild.get_channel(1321713301851476048).history(limit=1, oldest_first=True)][0]
            blacklists = []
            for embed in message.embeds:
                for field in embed.fields:
                    blacklists.append(field.name)
            try:
                if f"`{user}`" in blacklists:
                        index = blacklists.index(f"`{user}`")
                elif f"`{user}` APPEALED" in blacklists:
                    index = blacklists.index(f"`{user}` APPEALED")
                i = 0
                while index > 24:
                    i += 1
                    index %= 24
                message.embeds[i].remove_field(index)
                await message.edit(embeds=message.embeds, content=message.content)
                await intact.response.send_message("Done!", ephemeral=True)
            except:
                await intact.response.send_message("This person is not blacklisted!", ephemeral=True)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][NTSH Blacklist{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"{cfg.logstamp()}[NTSH Blacklist {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    

    print(f"{cfg.logstamp()}[Setup]{cfg.Success} NTSH Blacklist command group setup complete")