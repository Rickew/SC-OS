from python.helpers import exportSheetData, discord_to_username, single_UID_sync, idrostersanitize, get_scgroup_rank, trello_class_e_search, rotector_check
from discord import Interaction, app_commands, Embed, Member, File
from python.badgegraph import process_user, get_local_path
from traceback import format_exc
from requests import get, post
import data.config as cfg
from roblox import Client
from asyncio import sleep
import threading
import inspect
import roblox
import json

COMMAND_NAME = "user"

GUILD_IDS = [
    588427075283714049, #MF
    653542671100411906, #NTSH
    691298558032478208, #IF
    672480434549948438, #TC
    661593066330914828, #TAG
]

def div_frmt(divs: list):
    return str(divs).strip('[]').replace("'", "")

def dep_ranks(uid: int) -> dict[str,str]:
    ret = {"Nova Corp" : None, "Security Corps" : None, "Red Wolves": None, "Division": None, "Innovation Department" : None, "Regulations Department" : None, "Engineering Department" : None}
    url = "https://groups.roblox.com/v1/users/{userId}/groups/roles"
    try:
        r = get(url=url.replace("{userId}", str(uid))).json()['data']
        for group in r:
            if group['group']['id'] == 4971973: #SC
                ret["Security Corps"] = group['role']['name']
            elif group['group']['id'] == 5144434: #RW
                ret["Red Wolves"] = group['role']['name']
            elif group['group']['id'] == 4971978: #ID
                ret["Innovation Department"] = group['role']['name']
            elif group['group']['id'] == 4971979: #RD
                ret["Regulations Department"] = group['role']['name']
            elif group['group']['id'] == 5508925: #ED
                ret["Engineering Department"] = group['role']['name']
            elif group['group']['id'] == 4965800: #NC
                ret["Nova Corp"] = group['role']['name']
            elif group['group']['id'] in (7606555, 5182772, 33056979, 5714989, 5714988, 5555135, 5458312): #divisional groups
                ret["Division"] = group['group']['name']
    except:
        raise Exception("User Does Not Exist")
    return ret

def infoembed(usr: str, userinfo: dict[str,str], rblxusrid: int, discuser: Member) -> Embed:
    usrlink = f"https://www.roblox.com/users/{rblxusrid}/profile"
    try:
        embed = Embed(title=usr, url=usrlink, color=cfg.embedcolors[userinfo["TFD"]])
    except:
        embed = Embed(title=usr, url=usrlink, color=cfg.embedcolors["Main Force"])

    # first three
    embed.add_field(name="Discord", value=discuser.mention)
    try:
        embed.add_field(name="Division", value=userinfo["TFD"])
    except:
        embed.add_field(name="Division", value="Main Force")
    embed.add_field(name="Rank", value=userinfo["Rank"])

    # next three
    embed.add_field(name="Minutes", value=userinfo["Minutes"])
    embed.add_field(name="Honor", value=userinfo["Honor"])
    try:
        if userinfo["Total Time"] not in ("","-", "_", " "):
            embed.add_field(name="Total Time", value=userinfo["Total Time"])
        else:
            embed.add_field(name="⠀", value="⠀")
    except:
        embed.add_field(name="Total Events", value=userinfo["Total Events"])
    
    # next three
    embed.add_field(name="Quota Check", value=userinfo["Quota"].lower().title())
    embed.add_field(name="Quota Exemption", value=userinfo["Exempt Until"])
    embed.add_field(name="Events", value=userinfo["Events"])

    # next three
    embed.add_field(name="Activity Strikes", value=userinfo["Activity Strikes"])
    embed.add_field(name="Punishments", value=userinfo["Punishments"])
    embed.add_field(name="AC Strike Removal Date", value=userinfo["Activity Strike Removal Date"])
    
    # Last One
    try:
        embed.add_field(name="Notes/Quota Log", value=userinfo["Notes/Quota Log"])
    except:
        embed.add_field(name="Notes", value=userinfo["Notes"])

    # getting user thumbnail
    usrimg = cfg.rbximgurl.replace("{uid}", str(rblxusrid))
    usrimg = get(usrimg).content.decode().split("\",\"")[1].split(":\"")[1].replace("150", "250")
    embed.set_thumbnail(url=usrimg)
    return embed

def setup(tree: app_commands.CommandTree):
    usersuite = app_commands.Group(name="user", description="User Functions Suite, includes User info Views, BCGs, and other functions.", guild_ids=GUILD_IDS, guild_only=True)
    tree.add_command(usersuite)

    # displays user info for themselves or someone else
    # - Universal Command
    @usersuite.command(name="info", description="View your info or another user's info.")
    @app_commands.describe(user="The user who's info you want to display.")
    async def info(intact: Interaction, user: Member = None):
        try:
            print(f"[User info] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            try:
                if user:
                    usr = discord_to_username([str(user.id)])[0]
                    embeduser = user
                else:
                    usr = discord_to_username([str(intact.user.id)])[0]
                    embeduser = intact.user
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error", description=e), ephemeral=True)
                return
            rosters = exportSheetData()[1]
            try:
                userinfo = rosters[0].members[usr]
            except:
                try:
                    userinfo = rosters[1].members[usr]
                except:
                    await intact.followup.send(embed=Embed(title="Error", description="User is not on the Roster."), ephemeral=True)
                    return
            rblxuser = await Client().get_user_by_username(usr)
            embed = infoembed(usr, userinfo, rblxuser.id, embeduser)
            if intact.channel.name == "bot-commands":
                await intact.followup.send(embed=embed, ephemeral=False)
            else:
                await intact.followup.send(embed=embed, ephemeral=True)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[User {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)


    # This is a developer command, and should only really need to be used by the dev, however if access is needed, it has an enabled users list, which will allow the use of the command.
    # - Universal Command
    # - ID Locked
    enabled_users = [280185838393098241]
    @usersuite.command(name="syncuids", description="Polls, overwrites and syncs UIDs for Discord and Roblox in the Bot's internal database.")
    @app_commands.describe(user="The user you would like to sync.")
    async def syncuid(intact: Interaction, user: Member):
        try:
            if intact.user.id not in enabled_users:
                await intact.response.send_message("You're not allowed to run this command.")
                return
            print(f"[User syncuid] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(ephemeral=True, thinking=True)
            try:
                await single_UID_sync(tree, discID=user.id)
                await intact.followup.send(embed=Embed(title="User UIDs Updated", description=f"UIDs updated for: {user.mention}"), ephemeral=True)
                await idrostersanitize(intact=intact)
                return
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error with UID sync", description=e), ephemeral=True)
                await idrostersanitize(intact=intact)
                return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[User {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
        

    # This is an officer command used to show discrempancies in membership of users, between the group, discord, and roster.
    # - Universal Command
    # - Rank Locked
    @usersuite.command(name="discrempancy", description="Calculates and ouputs the user discrempancy between discord, group, and roster.")
    async def memdiscr(intact: Interaction):
        try:
            print(f"User Discrempancy Command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(ephemeral=True, thinking=True)
            if intact.guild_id != 588427075283714049:
                await intact.followup.send("This command can only be used in the Main SC Server.")
            # rank locking
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error", description=e))
            rank = get_scgroup_rank([comuser])[comuser]['rank']
            if rank < 7:
                await intact.followup.send("You're not a high enough rank to use this command.", ephemeral=True)
                return

            # get members of SC roblox group
            scgroup = await roblox.Client().get_group(4971973)
            members = scgroup.get_members()
            groupmembers: list[Member] = await members.flatten()

            # get roles and then role members for all the users in the SC discord
            roles = [833102255687335936, 833102254839169075, 833102254055358484, 904545012484804639, 833102251227873361, 833102252335693835, 833102252016140358, 833102250431873025, 833102249562996797, 833102249126264912, 1239749502639017984]
            discordmembers = []
            for i in range(0, len(roles)):
                # translate roles into member lists, and append member lists
                roles[i] = intact.guild.get_role(roles[i]).members
                discordmembers += roles[i]

            # translate member lists to IDs to usernames
            discorduids = []
            for mem in discordmembers:
                discorduids.append(str(mem.id))
            discordusernames = discord_to_username(discorduids)

            # get roster members names
            rosters = exportSheetData()[1]
            rostermembers: list[str] = []
            for mem in rosters[0].members:
                rostermembers.append(mem)
            for mem in rosters[1].members:
                rostermembers.append(mem)

            # start combining all the users into one to make one big list
            # parse out the discrempancies as you go.
            combinedusers = {}
            recruits = {}
            discrempancies = {"Unverified" : [], "Discrempancies" : {}}
            # recruits [rblxgroup, dicsord]
            # combinedusers [ rblxgroup, discord, roster]
            for mem in groupmembers:
                # if it a recruit is a special case, else they are in the rblx group
                if mem.role.name == "Recruit":
                    recruits.update({mem.name : [True, False, "N/A - Recruit"]})
                else:
                    combinedusers.update({mem.name : [True, False, False]})
            for mem in rostermembers:
                # if they are already in the list, mark them down as in the discord, else
                # add them to the list with only discord marked
                try:
                    combinedusers[mem][2] = True
                except:
                    combinedusers.update({mem : [False, False, True]})
            
            # doing discord users last
            for i in range(0, len(discordusernames)):
                # if they are unverified its an extra special case, gets its own thing
                if "Error" in discordusernames[i]:
                    discrempancies["Unverified"].append(f"{discordmembers[i].mention}")
                else:
                    try:
                        # if they are already in the list, mark the verified discord user as "yes thet are in the server"
                        combinedusers[discordusernames[i]][1] = True
                    except:
                        # exception: if the user is not in that list, they might be a recruit
                        try:
                            recruits[discordusernames[i]][1] = True
                        except:
                            # special exception, they are probably a recruit, and are in the discord, but not on roster or in group yet somehow?
                            combinedusers.update({discordusernames[i] : [False, True, "False - Potential Recruit"]})
            
            # combined the normal users and recruits into 1 list
            for mem in combinedusers:
                discrempancies["Discrempancies"].update({mem : combinedusers[mem]})
            for mem in recruits:
                discrempancies["Discrempancies"].update({mem : recruits[mem]})
            # special unverified embed for them
            # parse for formatting, looks better on discord.
            unverstring = ""
            for mem in discrempancies["Unverified"]:
                unverstring += f"{mem} "
            unverifiedembed = Embed(title="Unverified With Bloxlink", description=unverstring)
            
            # Special ignoring on discrempancy because guh
            ignore_list = ["ApplicationManagerNC", "Fishthegamer112", "MetatableIndex", "DrRhovus"]
            for name in ignore_list:
                try:
                    discrempancies["Discrempancies"].pop(name)
                except:
                    None

            # start making the discrempancy list
            try:
                # this one is for embeds with fields, it has a max of 25. 
                # this could be used a bit more if the discrempancy list was broken up a bit more categorically.
                # if the list is more than 25, the embed should error, causing this to be rerun as a string.
                i = 0
                retembed = Embed(title="Discremapncy Check Results", url="https://www.roblox.com/communities/configure?id=4971973#!/members")
                for mem in discrempancies["Discrempancies"]:
                # if any values are false, then there is an issue, add em to the list.
                    if not discrempancies["Discrempancies"][mem][0] or not discrempancies["Discrempancies"][mem][1] or not discrempancies["Discrempancies"][mem][2]:
                        i+=1
                        retembed.add_field(name=f"**{mem}**", value=
                            f"- Group: {discrempancies['Discrempancies'][mem][0]}\n"
                            f"- Discord: {discrempancies['Discrempancies'][mem][1]}\n"
                            f"- Roster: {discrempancies['Discrempancies'][mem][2]}", inline=True)
                    if i == 3:
                        i = 0
                while i != 3:
                    retembed.add_field(name="", value="", inline=True)
                    i+=1    
                    
                await intact.followup.send(embeds=[unverifiedembed, retembed], ephemeral=True)
                return
            except:
                retstring = ""
                for mem in discrempancies["Discrempancies"]:
                    # if any values are false, then there is an issue, add em to the list.
                    if not discrempancies["Discrempancies"][mem][0] or not discrempancies["Discrempancies"][mem][1] or not discrempancies["Discrempancies"][mem][2]:
                        retstring += f"**{mem}**\n- Group: {discrempancies['Discrempancies'][mem][0]}"
                        retstring += f"\n- Discord: {discrempancies['Discrempancies'][mem][1]}"
                        retstring += f"\n- Roster: {discrempancies['Discrempancies'][mem][2]}\n"
                try:
                    await intact.followup.send("Done!", embeds=[unverifiedembed, Embed(title="Discrempancies", description=retstring, url="https://www.roblox.com/communities/configure?id=4971973#!/members")], ephemeral=True)
                except:
                    # exception: list is too long, get rid of bold characters (4 characters per name)
                    retstring = retstring.replace("**", "")
                try:
                    await intact.followup.send("Done!", embeds=[unverifiedembed, Embed(title="Discrempancies", description=retstring, url="https://www.roblox.com/communities/configure?id=4971973#!/members")], ephemeral=True)
                except:
                    # exception: list is too long, get rid of - characters (7 characters per name gone now)
                    retstring.replace("\n- ", "\n")
                try:
                    await intact.followup.send("Done!", embeds=[unverifiedembed, Embed(title="Discrempancies", description=retstring, url="https://www.roblox.com/communities/configure?id=4971973#!/members")], ephemeral=True)
                except:
                    # exception: list is still too long, gonna print it to the console, but can't send it in 1 messsage and I can't be bothered to fix that.
                    await intact.followup.send("List is too long to send you're cooked.", ephemeral=True)
                    print(retstring)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[User {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    

    # This command is mostly meant for use by TFDs to do a simple, yet decent background check on users trying to join either mid tryout, or post tryout. This command is far from an exhaustive background check, see details below.
    # - Universal Command
    # - Rank Locked
    @usersuite.command(name="bgc", description="Does a comprehensive background check on a user.")
    @app_commands.describe(user="Roblox username of the person you want to run a BGC on.")
    @app_commands.describe(user="Roblox username of the person you want to run a BGC on.")
    async def bgc(intact: Interaction, user: str, badgegraph: bool = False):
        try:
            await intact.response.defer(thinking=True)
            print(f"[User bgc] command used by {intact.user} in {intact.guild.name}")
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="You're uids are not synced."))
                return
            rank = get_scgroup_rank([comuser])[comuser]['rank']
            if rank < 8:
                await intact.followup.send("You're not allowed to run this command.")
                return
            try:
                uid = post(url="https://users.roblox.com/v1/usernames/users", json={"usernames" : [user], "excludeBannedUsers" : True}).json()["data"][0]["id"]
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error", description=e))
                return
            rblxuser = await roblox.Client().get_user_by_username(user)
            backoff = 10
            while True:
                r = get(url=f"https://users.roproxy.com/v1/users/{uid}/username-history", params={"limit": 100, "sortOrder": "Desc"})
                if r.status_code == 429:
                    print("backing off, too hot:", backoff, "seconds")
                    sleep(backoff)
                    backoff+=10
                else:
                    pusername = [x['name'] for x in r.json()['data']]
                try:
                    while True:
                        try:
                            pusername.remove(user)
                        except:
                            break
                    break
                except Exception as e:
                    print(f"[User bgc] getting rate limited on prior usernames")
            creationdate = rblxuser.created
            dispname = rblxuser.display_name
            if badgegraph:
                badgethread = threading.Thread(daemon=True, target=process_user, args=[user])
                badgethread.start()

            embeds = []
            rotectorembed = rotector_check(uid)
            embeds.append(rotectorembed)
            
            moreinfo = Embed(title="Extra User Info", color=0xa80303, url=f"https://www.roblox.com/users/{uid}/profile")
            moreinfo.add_field(name="User Creation Date", value=creationdate.strftime(r'%b %d, %Y'))
            moreinfo.add_field(name="Previous Usernames", value=div_frmt(pusername))
            moreinfo.add_field(name="Display Name", value=dispname)
            embeds.append(moreinfo)

            ncgroupsembed = Embed(title="Nova Department Ranks", color=0xa80303)
            ncranks = dep_ranks(uid)
            for rank in ncranks:
                if ncranks:
                    if rank == "Security Corps" and ncranks[rank]:
                        ncgroupsembed.add_field(name=rank, value=ncranks[rank])
                    elif rank == "Red Wolves" and ncranks[rank]:
                        ncgroupsembed.add_field(name=rank, value=ncranks[rank])
                    elif rank not in ("Security Corps", "Red Wolves"):
                        ncgroupsembed.add_field(name=rank, value=ncranks[rank])
            embeds.append(ncgroupsembed)
            bansembed = Embed(title="Class - E History", color=0xa80303, url="https://trello.com/b/E9nodzRk/class-e-board")
            bans = trello_class_e_search(user)
            if len(bans) > 0:
                string = ""
                for ban in bans:
                    labels = ""
                    for i in ban['approvals']:
                        labels+=f"{i},"
                    string += f"[{ban['name']}]({ban['url']}) - {labels}\n"
                bansembed.add_field(name=user, value=string)
            if pusername:
                for name in pusername:
                    bans = trello_class_e_search(name)
                    if len(bans) > 0:
                        string = ""
                        for ban in bans:
                            labels = ""
                            for i in ban['approvals']:
                                labels+=f"{i},"
                            string += f"[{ban['name']}]({ban['url']}) - {labels}\n"
                        bansembed.add_field(name=name, value=string)
            if len(bansembed.fields) <= 0:
                bansembed.description = "Clean, No Class - E History"
            embeds.append(bansembed)

            blacklistembed = Embed(title="SC/RW Blacklist History", color=0xa80303, url="https://docs.google.com/spreadsheets/d/1L2TZQ4K67krGmwnSVJdzoed2iOTh8CUwRqa_TsiwZMk/")
            cells = cfg.blacklistroster.findall(query=user)
            for cell in cells:
                values = cfg.blacklistroster.row_values(cell.row)
                blacklistembed.add_field(name=user, value=f"**Type:** {values[2]}\n**Completed:** {values[3]}\n**Reason:** {values[4]}\n**Approved By:** {values[6]}")
            for name in pusername:
                cells = cfg.blacklistroster.findall(query=name)
                for cell in cells:
                    values = cfg.blacklistroster.row_values(cell.row)
                    blacklistembed.add_field(name=name, value=f"**Type:** {values[2]}\n**Completed:** {values[3]}\n**Reason:** {values[4]}\n**Approved By:** {values[6]}")
            if len(blacklistembed.fields) <= 0:
                blacklistembed.description = "Clean, No SC/RW Blacklist History."
            embeds.append(blacklistembed)
            if badgegraph:
                while badgethread.is_alive():
                    await sleep(2)
                badgethread.join()
                try:
                    file = File(get_local_path(f"data/badgegraphs/BadgeGraph-{uid}.png"),filename="graph.png")
                    badgeembed = Embed(title="Badge Graph (Alt Detection Assistance)", color=0xa80303, url="https://devforum.roblox.com/t/free-alt-detection-badge-history-graph-180k-uses/3546351")
                    badgeembed.set_image(url=f"attachment://graph.png")
                    embeds.append(badgeembed)
                    await intact.followup.send(content=f"Background Check for: {user}", embeds=embeds, file=file)
                except:
                    badgeembed = Embed(title="Badge Graph (Alt Detection Assistance)", description="Users Iventory is Private, Canot View Badges.", color=0xa80303, url="https://devforum.roblox.com/t/free-alt-detection-badge-history-graph-180k-uses/3546351")
            else:
                await intact.followup.send(content=f"Background Check for: {user}", embeds=embeds)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[User {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)


    # This is used to switch the username of a person on the roster, and to hopefully sync their new id with the bot.
    # - Universal Command
    # - Rank Locked
    @usersuite.command(name="nametransfer", description="Change a name on the roster. (User Name Change/Account Transfer)")
    @app_commands.describe(currentuser="The current userame.")
    @app_commands.describe(newuser="The new userame.")
    async def change(intact: Interaction, currentuser: str, newuser: str):
        try:
            await intact.response.defer(thinking=True, ephemeral=True)
            print(f"User Name Transfer Command ran by {intact.user} in {intact.guild.name}")
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="You're uids are not synced.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                return
            rank = get_scgroup_rank([comuser])[comuser]['rank']
            if rank < 8:
                await intact.followup.send("You're not allowed to use this command.")
                return
            
            # user uid sync
            try:
                await single_UID_sync(tree, rblxuser=newuser)
                await intact.followup.send(embed=Embed(title="User UIDs Updated", description=f"UIDs updated for: {newuser}"), ephemeral=True)
                await idrostersanitize(intact=intact)
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error with UID sync", description=e), ephemeral=True)
                await idrostersanitize(intact=intact)
                return
            
            rostersheets, rosters = exportSheetData(True)
            try:
                index = 0
                userinfo = rosters[index].members[currentuser]
            except:
                try:
                    index = 1
                    userinfo = rosters[index].members[currentuser]
                except:
                    await intact.followup.send(embed=Embed(title="Error", description="User not on the roster.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                    return
            rostersheets[index].update_cell(userinfo["Row"], 1, newuser)
            with open(get_local_path("data\\totaltimes.json"), "r") as f:
                times = json.load(f)
                f.close()
            try:
                times.update({newuser : times[currentuser]})
                with open(get_local_path("data\\totaltimes.json"), "r") as f:
                    json.dump(times, f, indent=2)
                    f.close()
            except:
                None
            await intact.followup.send(embed=Embed(title="Username Changed On Roster", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]).add_field(name="Username Transfer", value=f"{currentuser} -> {newuser}"))    
            await intact.guild.get_channel(cfg.logchannel_ids[cfg.serverid_to_name[str(intact.guild_id)]]).send(embed=Embed(title="Username Changed On Roster", description=f"Name changed by {intact.user.mention}", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]).add_field(name="Username Transfer", value=f"{currentuser} -> {newuser}").set_author(name=f"{currentuser} -> {newuser}"))
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[User {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    
    print(f"[Setup]{cfg.Success} User command group setup complete")
