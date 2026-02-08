from python.helpers import exportSheetData, discord_to_username, single_UID_sync, get_quota_string, remove_bottom_row, get_scgroup_rank, get_local_path, shift_point_rows
from python.uiclasses import RosterRankSelect, CancelButton, RosterEditButtons
from discord import Interaction, app_commands, Embed, Member
from python.commands.universal.usersuite import infoembed
from gspread.utils import ValueRenderOption
from datetime import datetime as dt
from traceback import format_exc
import data.config as cfg
from gspread import Cell
from re import findall
from json import load
import inspect
import asyncio
import roblox

COMMAND_NAME = "roster"

GUILD_IDS = [
    588427075283714049, #MF
    653542671100411906, #NTSH
    691298558032478208, #IF
    672480434549948438, #TC
    661593066330914828  #TAG
]

async def rosteradd(tree: app_commands.CommandTree, intact: Interaction, user: Member, division: app_commands.Choice[int], rankselect: bool = False, overtime: bool = True, run: bool = False):
    # this is used for more than 1 command
    if not run:
        print(f"{cfg.logstamp()}[Roster add] command ran by {intact.user} in {intact.guild.name}")
        await intact.response.defer(ephemeral=True, thinking=True)
        
    # comuser resolution
    try:
        comuser = discord_to_username([str(intact.user.id)])[0]
    except Exception as e:
        await intact.followup.send(embed=Embed(title="Error", description=e))
    comrank = get_scgroup_rank([comuser])[comuser]['rank']
    # security supervisor + to run this command
    if comrank <= 7:
        await intact.response.send_message("You're group rank is too low to use this command. (SS+)", ephemeral=True)
        return False
    rostersheets, rosters = exportSheetData()
    try:
        comuserinfo = rosters[0].members[comuser]
    except:
        try:
            comuserinfo = rosters[1].members[comuser]
        except:
            if not run:
                await intact.followup.send(embed=Embed(title="Error", description="You're not on the Roster."))
                return
            else:
                raise Exception("You're not on the roster.")
        
    # add bro to IDroster or atleast attempt to.
    try:
        usr = discord_to_username([str(user.id)])[0]
    except Exception as e:
        try:
            await single_UID_sync(tree, discID=user.id)
            usr = discord_to_username([str(user.id)])
        except Exception as e:
            if not run:
                await intact.followup.send(embed=Embed(title="Error", description=e), ephemeral=True)
            else:
                raise e
            return False
        
    
    # load quota settings
    with open(get_local_path("data\\quota.json"), "r") as f:
        quota = load(f)
        f.close()

    # for mainforce additions
    if division.name == "Main Force":

        # some quick division locking
        if comuserinfo["Rank"] not in ("Task Force Leader", "Commander", "Head Commander", "General"):
            await intact.followup.send("Your Rank doesn't allow you to add people to the Main Force Roster.", ephemeral=True)
            return False
        
        if rankselect:
            # selecting ranks
            view = CancelButton()
            if comuserinfo["Rank"] in ("Commander", "Head Commander", "General"):
                editselect = RosterRankSelect(0, 2, 5, False, division.name)
            elif comuserinfo["Rank"] in "Task Force Leader":
                editselect = RosterRankSelect(0, 2, 5, "Security Major", division.name)
            else:
                editselect = RosterRankSelect(0, 2, 5, comuserinfo["Rank"], division.name)
            view.add_item(editselect)
            await intact.followup.send(content=f"Select a Rank.", view=view, ephemeral=True)
            while not editselect.selected:
                if view.cancel:
                    await intact.delete_original_response()
                    return False
                await asyncio.sleep(0.2)
            rank = editselect.selection
        
        # or not selecting a rank
        else:
            rank = "Junior Guard"

        # in any case find the bottom most rank cell
        bottomcell = remove_bottom_row(rostersheets[0], rank)[-1]

        # get the rank quota string
        quotastring = get_quota_string("Main Force", rank).replace("{row}", str(bottomcell.row+1))

        # 3 part process here, we are copying the bottom cell, inserting it, and the new person above it, then deleteing the bottom 
        # cell, api doesn't let me add cells downward, and if I try format settings get fucked up.
        copyrow = rostersheets[0].row_values(bottomcell.row, value_render_option=ValueRenderOption.formula)
        if rank in quota[division.name]['Cycle']['NCOs-COs']:
            # nco/co additions, this is mostly a transfer thing
            shift_point_rows(quota[division.name]['Cycle']['NCOs-COs'], rank, "Add")
        rostersheets[0].insert_row(copyrow, bottomcell.row, value_input_option="USER_ENTERED")

        # if they are on overtime
        if overtime:
            rostersheets[0].insert_row([usr, 0, 0, quotastring, rank, 0, 0, "OVERTIME", 0], bottomcell.row+1, value_input_option="USER_ENTERED")
        else:
            rostersheets[0].insert_row([usr, 0, 0, quotastring, rank, 0, 0, '', 0], bottomcell.row+1, value_input_option="USER_ENTERED")
        bottomrow = remove_bottom_row(rostersheets[0], rank)[-1].row
        rostersheets[0].delete_rows(bottomrow, bottomrow)
    else:
        # if not mainforce, then add to tfd roster.
        # some more division locking, exception to SM+
        try:
            if rosters[1].members[comuser]["TFD"] != division.name and rosters[1].members[comuser]["Rank"] not in ("Task Force Leader", "Commander", "Head Commander", "General"):
                await intact.followup.send("You can't add to a TFD roster that isn't yours.", ephemeral=True)
                return False
        except:
            # mainforce lock, doesn't stop Directorate
            try:
                rosters[0].members[comuser]
                await intact.followup.send("You can't add to TFD rosters.", ephemeral=True)
                return False
            except:
                await intact.followup.send(embed=Embed(title="Error", description="You're not ranked on the roster?"), ephemeral=True)
                return False
        # rank select
        if rankselect:
            view = CancelButton()
            if comuserinfo["Rank"] in ("Commander", "Head Commander", "General"):
                editselect = RosterRankSelect(1, remove_bottom_row(rostersheets[1], division.name)[-1].row, 6, False, division.name)
            else:
                editselect = RosterRankSelect(1, remove_bottom_row(rostersheets[1], division.name)[-1].row, 6, comuserinfo["Rank"], division.name)
            editselect = RosterRankSelect(1, remove_bottom_row(rostersheets[1], division.name)[-1].row, 6, False, division.name)
            view.add_item(editselect)
            await intact.followup.send(content=f"Select a Rank", view=view, ephemeral=True)
            while not editselect.selected:
                if view.cancel:
                    await intact.delete_original_response()
                    return False
                await asyncio.sleep(0.2)
            rank = editselect.selection
        else:
            # default ranks
            if division.name == "Nothing To See Here":
                rank = "Preliminary Operative"
            elif division.name == "The Armed Gentlemen":
                rank = "Sentry"
            elif division.name == "The Crazies":
                rank = "Bambi"
            elif division.name == "Iron Fist":
                rank = "Cadet"
        try:
            switch1 = False
            switch2 = False

            # This is a TFD specfic issue fix for finding the bottom cell
            if rank == "Task Force Leader":
                raise Exception("TFL rank addition needs raise")
            bottomcell = remove_bottom_row(rostersheets[1], rank)[-1]
        except:
            switch2 = True
            ranks = list(quota[division.name].keys())
            ranks.remove("Cycle")
            bottomcell = None
            try:
                i = 1
                while True:
                    rankindex = ranks.index(rank) + i
                    findrank = ranks[rankindex]
                    try:
                        bottomcell = remove_bottom_row(rostersheets[1], findrank)[-1]
                    except: 
                        None
                    if bottomcell:
                        break
                    i+=1
            except:
                bottomcell = rostersheets[1].find(division.name)
                switch1 = True

        # get quota string, insert copy user, then new user and then delete row below newuser
        quotastring = get_quota_string(division.name, rank).replace("{row}", str(bottomcell.row+1))
        copyrow = rostersheets[1].row_values(bottomcell.row, value_render_option=ValueRenderOption.formula)
        if rank in quota[division.name]['Cycle']['NCOs-COs']:
            shift_point_rows(quota[division.name]['Cycle']['NCOs-COs'], rank, "Add")
        rostersheets[1].insert_row(copyrow, bottomcell.row,value_input_option="USER_ENTERED")
        if division.name == "Iron Fist":
            if overtime:
                rostersheets[1].insert_row([usr, 0, 0, 0, quotastring, rank, division.name, 0, "OVERTIME", 0, 0], bottomcell.row+1 ,value_input_option="USER_ENTERED")
            else:
                rostersheets[1].insert_row([usr, 0, 0, 0, quotastring, rank, division.name, 0, None, 0, 0], bottomcell.row+1 ,value_input_option="USER_ENTERED")
        else:
            if overtime:
                rostersheets[1].insert_row([usr, 0, None, 0, quotastring, rank, division.name, 0, "OVERTIME", 0, 0], bottomcell.row+1 ,value_input_option="USER_ENTERED")
            else:
                rostersheets[1].insert_row([usr, 0, None, 0, quotastring, rank, division.name, 0, None, 0, 0], bottomcell.row+1 ,value_input_option="USER_ENTERED")
        
        # this is more fixes for the TFD stuff, makes sure that the rows and all get deleted.
        if switch2 and not switch1:
            bottomrow = remove_bottom_row(rostersheets[1], ranks[rankindex])[-1].row
            rostersheets[1].delete_rows(bottomrow, bottomrow)
        elif switch1:
            toprow = rostersheets[1].find(division.name).row
            rostersheets[1].delete_rows(toprow, toprow)
        else:
            bottomrow = remove_bottom_row(rostersheets[1], rank)[-1].row
            rostersheets[1].delete_rows(bottomrow, bottomrow)
    
    # this is confirmation logs if it's an add and not a transfer. 
    if not run:
        embed = Embed(title=f"User Added to {division.name} Roster", description=f"User Added: {usr}\nRank: {rank}\nOvertime? {overtime}", color=cfg.embedcolors[division.name])
        await intact.edit_original_response(view=None, embed=embed)
        embed.description = f"User Added to {division.name} Roster by {intact.user.mention}\n{embed.description}"
        embed.set_author(name=f"{comuser} > {user}")
        if intact.guild_id != 588427075283714049 and division.name == "Main Force":
            await tree.client.get_guild(588427075283714049).get_channel(588438540090736657).send(embed=embed)
        await tree.client.get_guild(cfg.server_ids[division.name]).get_channel(cfg.logchannel_ids[division.name]).send(embed=embed)
    return True

async def time(tree: app_commands.CommandTree, intact: Interaction, addsub: app_commands.Choice[int], users: str, amount: float):
        print(f"{cfg.logstamp()}[Roster quickedit][time] command ran by {intact.user} in {intact.guild.name}")
        await intact.response.defer(thinking=True, ephemeral=True)
        resultsembed = Embed(title="Errors")

        # parse uids
        uidinput: list[str] = findall(r'<@(\d+)>',users)
        uids = []
        for uid in uidinput:
            uids.append(uid.replace("@", "").replace("<", "").replace(">", ""))
        # print(uids)

        # parse uids into Roblox usernames
        users = discord_to_username(uids)
        # print(uids)

        #quick addition/subtraction parse
        if addsub.value == 2:
            realamount = 0 - amount
        else:
            realamount = float(amount)
            
        # export sheets
        rostersheets, rosters = exportSheetData()
        updcells = [[], []]
        try:
            comuser = discord_to_username([str(intact.user.id)])[0]
        except Exception as e:
            await intact.followup.send(embed=Embed(title="Error", description=e))
        try:
            division = rosters[1].members[comuser]["TFD"]
        except:
            division = "Main Force"
        upddivs = []
        auditembed = Embed(title=f"{amount} Minutes {addsub.name}ed to Users", description=f"Minutes added by: {intact.user.mention}", color=cfg.embedcolors[division])
        # get cells, update values
        for i in range(0, len(users)):
            try: # try to make a cell from the MF roster
                updcells[0].append(
                    Cell(
                        rosters[0].members[users[i]]["Row"], 
                        rosters[0].headers["Minutes"],
                        float(rosters[0].members[users[i]]["Minutes"])+realamount))
                auditembed.add_field(name=users[i], value=f"{rosters[0].members[users[i]]['Minutes']} -> {float(rosters[0].members[users[i]]['Minutes'])+realamount} Time")
            except:
                try:
                    updcells[1].append(
                    Cell(
                        rosters[1].members[users[i]]["Row"], 
                        rosters[1].headers["Minutes"],
                        float(rosters[1].members[users[i]]["Minutes"])+realamount))
                    auditembed.add_field(name=users[i], value=f"{rosters[1].members[users[i]]['Minutes']} -> {float(rosters[1].members[users[i]]['Minutes'])+realamount} Time")
                except:
                    resultsembed.add_field(name="UIDError", value=f"User <@{uids[i]}> not on roster")
                if rosters[1].members[users[i]]["TFD"] not in upddivs:
                    upddivs.append(rosters[1].members[users[i]]["TFD"])

        # print(udcells)
        # update the cells
        for cell in updcells[0]:
            rostersheets[0].update_cells([cell])
        for cell in updcells[1]:
            rostersheets[1].update_cells([cell])
        if len(resultsembed.fields) > 0:
            await intact.followup.send("Done!", embed=resultsembed, ephemeral=True)
            await intact.followup.send(embed=resultsembed)
        else:
            await intact.followup.send("Done!", ephemeral=True)
        if intact.message.reference:
            await intact.followup.send(embed=resultsembed)

        # sending logs
        if len(updcells) > 0:
            for div in upddivs:
                await tree.client.get_guild(cfg.server_ids[div]).get_channel(cfg.logchannel_ids[div]).send(embed=auditembed.set_author(name=f"{comuser}"))
            await tree.client.get_guild(588427075283714049).get_channel(588438540090736657).send(embed=auditembed.set_author(name=f"{comuser}"))
        return True

async def multifunction(tree: app_commands.CommandTree, option, intact: Interaction, addsub: app_commands.Choice[int], users: str, amount: int):
    print(f"{cfg.logstamp()}[Roster quickedit][{option.lower()}] command ran by {intact.user} in {intact.guild.name}")
    await intact.response.defer(thinking=True, ephemeral=True)
    resultsembed = Embed(title="Errors")

    # parse uids
    uidinput: list[str] = findall(r'<@(\d+)>',users)
    uids = []
    for uid in uidinput:
        uids.append(uid.replace("@", "").replace("<", "").replace(">", ""))
    # print(uids)
    # parse uids into Roblox usernames
    users = discord_to_username(uids)
    # print(users)

    #quick addition/subtraction parse
    if addsub.value == 2:
        realamount = 0 - amount
    else:
        realamount = float(amount)
        
    # export sheets
    rostersheets, rosters = exportSheetData()
    updcells = [[], []]
    try:
        comuser = discord_to_username([str(intact.user.id)])[0]
    except Exception as e:
        await intact.followup.send(embed=Embed(title="Error", description=e))
    try:
        division = rosters[1].members[comuser]["TFD"]
    except:
        division = "Main Force"
    upddivs = []
    auditembed = Embed(title=f"{realamount} {option} {addsub.name}ed to Users", description=f"{option} added by: {intact.user.mention}", color=cfg.embedcolors[division])
    # get cells, update values
    for i in range(0, len(users)):
        try: # try to make a cell from the MF roster
            updcells[0].append(
                Cell(
                    rosters[0].members[users[i]]["Row"], 
                    rosters[0].headers[option],
                    float(rosters[0].members[users[i]][option])+realamount))
            auditembed.add_field(name=users[i], value=f"{rosters[0].members[users[i]][option]} -> {float(rosters[0].members[users[i]][option])+realamount} {option}")
        except:
            try:
                updcells[1].append(
                Cell(
                    rosters[1].members[users[i]]["Row"], 
                    rosters[1].headers[option],
                    float(rosters[1].members[users[i]][option])+realamount))
                auditembed.add_field(name=users[i], value=f"{rosters[1].members[users[i]][option]} -> {float(rosters[1].members[users[i]][option])+realamount} {option}")
            except:
                resultsembed.add_field(name="UIDError", value=f"User <@{uids[i]}> not on roster")
                continue
            if rosters[1].members[users[i]]["TFD"] not in upddivs:
                upddivs.append(rosters[1].members[users[i]]["TFD"])
# print(udcells)
    # update the cells
    for cell in updcells[0]:
        rostersheets[0].update_cells([cell])
    for cell in updcells[1]:
        rostersheets[1].update_cells([cell])
    if len(resultsembed.fields) > 0:
        await intact.followup.send("Done!", embed=resultsembed, ephemeral=True)
        await intact.followup.send(embed=resultsembed)
    else:
        await intact.followup.send("Done!", ephemeral=True)
    
    # sending logs
    if len(updcells) > 0:
        for div in upddivs:
            await tree.client.get_guild(cfg.server_ids[div]).get_channel(cfg.logchannel_ids[div]).send(embed=auditembed.set_author(name=f"{comuser}"))
        await tree.client.get_guild(588427075283714049).get_channel(588438540090736657).send(embed=auditembed.set_author(name=f"{comuser}"))
    return True

def setup(tree: app_commands.CommandTree):
    # roster command group
    roster = app_commands.Group(name="roster", description="Roster Management", guild_ids=GUILD_IDS, guild_only=True)
    tree.add_command(roster)


    # This command allows the user to edit the minutes/honor/event cells on the roster in bulk, mostly for use after events as rewards for attending, but also serves as a single
    # - Universal Command
    # - Rank Locked
    @roster.command(name="quickedit", description="Quick edit the Minutes/Events/Honor of multiple SC at once.")
    @app_commands.describe(users="The users you want to edit.")
    @app_commands.choices(addsub=[app_commands.Choice(name="Add", value=1), app_commands.Choice(name="Subtract", value=2)])
    @app_commands.choices(option=[app_commands.Choice(name="Minutes", value=1), app_commands.Choice(name="Events", value=2), app_commands.Choice(name="Honor", value=3)])
    @app_commands.describe(addsub="Select to Add or Subtract x amount from which ever option is slected to/from the user.")
    @app_commands.describe(option="The value you want to edit.")
    @app_commands.choices(addsub=[app_commands.Choice(name="Minutes", value=1), app_commands.Choice(name="Events", value=2), app_commands.Choice(name="Honor", value=3)])
    async def quickedit(intact: Interaction, option: app_commands.Choice[int], addsub: app_commands.Choice[int], users: str, amount: float):
        try:
            if option.value == 1:
                # doing time
                await time(tree, intact, addsub, users, amount)
            elif option.value == 2:
                # doing events
                await multifunction(tree, 'Events', intact, addsub, users, amount)
            elif option.value == 3:
                # doing honor
                await multifunction(tree, 'Honor', intact, addsub, users, amount)
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Roster {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Roster {inspect.currentframe().f_code.co_name}][{option.name}]{cfg.Error}", i.jump_url)


    # This command adds a user to the roster, with optional rank selection, and OVERTIME notice
    # - Universal Command
    # - Rank Locked
    # - Bloxlink Integration
    @roster.command(name="add", description="Add a new SC to the Roster.")
    @app_commands.describe(user="The user you want to add to the roster.")
    @app_commands.describe(rankselect="Allows you to add a rank to them on the roster easily.")
    @app_commands.describe(overtime="Grants amnesty from quota for the given cycle, toggled On by default.")
    @app_commands.choices(division=[
        app_commands.Choice(name="Main Force", value=1),
        app_commands.Choice(name="The Crazies", value=2),
        app_commands.Choice(name="The Armed Gentlemen", value=3),
        app_commands.Choice(name="Iron Fist", value=4),
        app_commands.Choice(name="Nothing To See Here", value=5)])
    async def add(intact: Interaction, user: Member, division: app_commands.Choice[int], rankselect: bool = False, overtime: bool = True):
        try:
            ret = await rosteradd(tree, intact, user, division, rankselect, overtime)
            return ret
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Roster {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Roster {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    

    # Deletes a user from the roster.
    # - Universal Command
    # - Rank Locked
    @roster.command(name="delete", description="Delete an SC member from the Roster.")
    @app_commands.describe(user="The user you want to delete from the roster.")
    async def delete(intact: Interaction, user: str):
        try:
            print(f"{cfg.logstamp()}[Roster delete] command ran by {intact.user} in {intact.guild.name}")
            # some quick command rank locking and comuser resolution
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error", description=e))
            comrank = get_scgroup_rank([comuser])[comuser]['rank']
            if comrank <= 7:
                # security supervisor+ to run this command
                await intact.response.send_message("You're group rank is too low to use this command. (SS+)", ephemeral=True)
                return False
            await intact.response.defer(ephemeral=True, thinking=True)
            rostersheets, rosters = exportSheetData()

            # find bro
            index = 0
            cell = rostersheets[index].find(user)
            if not cell:
                index = 1
                cell = rostersheets[index].find(user)
                if not cell:
                    await intact.followup.send(embed=Embed(title="Error", description=f"User {user} is not on the roster."), ephemeral=True)
                    return
            
            # log bluds data like the government
            if not index:
                division = "Main Force"
            else:
                division = rosters[index].members[user]["TFD"]
            rank = rosters[index].members[user]["Rank"]
            acstrike = rosters[index].members[user]["Activity Strikes"]
            punishments = rosters[index].members[user]["Punishments"]
            with open(get_local_path("data\\quota.json"), "r") as f:
                quota = load(f)
            if rank in quota[division]['Cycle']["NCOs-COs"]:
                shift_point_rows(quota[division]['Cycle']["NCOs-COs"], rank, "Delete")

            # delete bro - makes sure the keep atleast 1 rank/division cell in between the sections
            if division == "Main Force":
                if len(remove_bottom_row(rostersheets[index], rank)) == 1:
                    rostersheets[index].insert_row(["-", 0, 0, "INCOMPLETE", rank, 0, 0, "", 0, 0], cell.row)
                    rostersheets[index].delete_rows(cell.row+1, cell.row+1)
                else:
                    rostersheets[index].delete_rows(cell.row, cell.row)
            else:
                if len(remove_bottom_row(rostersheets[index], division)) == 1:
                    rostersheets[index].insert_row(["-", 0, "_", 0, "INCOMPLETE", "", division, 0, "", 0, 0], cell.row)
                    rostersheets[index].delete_rows(cell.row+1, cell.row+1)
                else:
                    rostersheets[index].delete_rows(cell.row, cell.row)

            # logs
            embed = Embed(title=f"User deleted from {division} Roster.", description=f"User: {user}\nDivision: {division}\nRank: {rank}\nActivity Strikes: {acstrike}\nPunishments: {punishments}", color=cfg.embedcolors[division])
            if intact:
                await intact.followup.send(embed=embed, ephemeral=True)
                embed.title = f"User Deleted from {division} Roster by {intact.user.mention}"
                await tree.client.get_guild(588427075283714049).get_channel(588438540090736657).send(embed=embed.set_author(name=f"{comuser} > {user}"))
                await tree.client.get_guild(cfg.server_ids[division]).get_channel(cfg.logchannel_ids[division]).send(embed=embed.set_author(name=f"{comuser} > {user}"))
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Roster {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Roster {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)


    # Transfers a user from 1 roster to another.
    # - Universal Command
    # - Rank Locked
    @roster.command(name="transfer", description="Transfer a user from 1 division roster to another.")
    @app_commands.describe(user="The user you want to transfer.")
    @app_commands.describe(overtime="Grants amnesty from quota for the given cycle, toggled On by default.")
    @app_commands.choices(transferto=[
        app_commands.Choice(name="Main Force", value=1),
        app_commands.Choice(name="The Crazies", value=2),
        app_commands.Choice(name="The Armed Gentlemen", value=3),
        app_commands.Choice(name="Iron Fist", value=4),
        app_commands.Choice(name="Nothing To See Here", value=5)])
    async def transfer(intact: Interaction, user: Member, transferto: app_commands.Choice[int], overtime: bool = True):
        try:
            print(f"{cfg.logstamp()}[Roster transfer] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            # should do some ranklocking here
            # unsure if this is needed though, I think roster_add takes care of all of it anyway.

            # get information about the user being transfered
            rostersheets, rosters = exportSheetData(True)
            try:
                usr = discord_to_username([str(user.id)])[0]
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error", description=e), ephemeral=True)
                return
            index = 0
            try:
                userinfo = rosters[index].members[usr]
                prediv = "Main Force"
            except:
                index = 1
                try:
                    userinfo = rosters[index].members[usr]
                    prediv = userinfo["TFD"]
                except:
                    await intact.followup.send(embed=Embed(title="Error", description="User is not on the roster to be transfered."), ephemeral=True)
                    return
            
            # quick checks
            if not index and transferto.name == "Main Force":
                await intact.followup.send(embed=Embed(title="Error", description="User is already in Main Force"), ephemeral=True)
                return
            elif index and userinfo["TFD"] == transferto.name:
                await intact.followup.send(embed=Embed(title="Error", description=f"User is already in {transferto.name}"), ephemeral=True)
                return
            
            # attempts to add to new roster, delete from old roster
            with open(get_local_path("data\\quota.json"), "r") as f:
                quota = load(f)
            try:
                rostersheets[index].delete_rows(userinfo["Row"], userinfo["Row"])
                await rosteradd(tree, intact, user, transferto, True, overtime, True)
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error", description=e), ephemeral=True)
                return False
            
            # makes sure it worked
            rosters = exportSheetData(True)[1]
            try:
                upduserinfo = rosters[0].members[usr]
                postdiv = "Main Force"
                index = 0
            except:
                try:
                    upduserinfo = rosters[1].members[usr]
                    postdiv = upduserinfo["TFD"]
                    index = 1
                except:
                    await intact.followup.send(embed=Embed(title="Error", description="User was not transfered."), ephemeral=True)
                    return
            newrow = upduserinfo["Row"]
            rostersheets[index].update_cells([Cell(newrow, rosters[index].headers["Minutes"], userinfo["Minutes"]), Cell(newrow, rosters[index].headers["Honor"], userinfo["Honor"])], value_input_option="USER_ENTERED")
            
            # sending logs
            embed = Embed(title="User Transfered", description=f"User Transfered: {usr}\n{prediv} -> {postdiv}\n{userinfo['Rank']} -> {upduserinfo['Rank']}\nOvertime? {overtime}", color=cfg.embedcolors[postdiv])
            await intact.edit_original_response(content="Done!", view=None, embed=embed)
            embed.description = f"User Transfered by {intact.user.mention}\n{embed.description}"
            embed.set_author(name=f"{discord_to_username([str(intact.user.id)])} > {user}")
            if prediv != "Main Force" and postdiv != "Main Force":
                await tree.client.get_guild(588427075283714049).get_channel(588438540090736657).send(embed=embed)
            await tree.client.get_guild(cfg.server_ids[postdiv]).get_channel(cfg.logchannel_ids[postdiv]).send(embed=embed)
            embed.color = cfg.embedcolors[prediv]
            await tree.client.get_guild(cfg.server_ids[prediv]).get_channel(cfg.logchannel_ids[prediv]).send(embed=embed)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Roster {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Roster {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)


    # allows the editing of the rest of the user cells on the roster, such as activity strikes, removing strikes, editing the notes cell, and marking manual quotas
    # - Universal Command
    # - Rank Locked
    @roster.command(name="edit", description="Edit a user on the Roster.")
    async def edit(intact: Interaction, user: Member):
        try:
            print(f"{cfg.logstamp()}[Roster edit] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)

            # get division
            division = cfg.serverid_to_name[str(intact.guild_id)]

            # comuser resolution
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="Your uids are not synced.", color=cfg.embedcolors[division]))
                return
            rostersheets, rosters = exportSheetData()
            try:
                comuserinfo = rosters[0].members[comuser]
            except:
                try:
                    comuserinfo = rosters[1].members[comuser]
                except:
                    await intact.followup.send(embed=Embed(title="Error", description="You are not on the roster."))
            
            # rank lock
            comrank = get_scgroup_rank([comuser])[comuser]['rank']
            if comrank < 8:
                await intact.followup.send(embed=Embed(title="Error", description="You're not allowed to use this command.", color=cfg.embedcolors[division]))
            try:
                usr = discord_to_username([str(user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="User's uids are not synced.", color=cfg.embedcolors[division]))
                return
            
            # susing the index
            if division == "Main Force":
                index = 0
            else:
                index = 1
            
            # user resolution
            try:
                userinfo = rosters[index].members[usr]
                rblxid = (await roblox.Client().get_user_by_username(usr)).id
            except:
                await intact.followup.send(embed=Embed(title="Error", description="User is not on the Roster.", color=cfg.embedcolors[division]))
                return
            
            # loading quota settings
            with open(get_local_path("data\\quota.json"), "r") as f:
                quota = load(f)
                f.close()

            # user edit menu
            while True:
                guiembed = infoembed(usr, userinfo, rblxid, user)
                if quota[division][userinfo["Rank"]]["Type"] == "Manual":
                    view = RosterEditButtons(usr, division, rosters[index], rostersheets[index], True)
                else:
                    view = RosterEditButtons(usr, division, rosters[index], rostersheets[index], False)
                await intact.edit_original_response(embed=guiembed, view=view)
                ind = await view.wait()

                if ind:
                    await intact.delete_original_response()
                    return
                
                if view.done:
                    await intact.delete_original_response()
                    break

                elif view.adqs:
                    # adding a quota strike, this only runs if it's the first quota strike and a removal date is needed
                    if division != "Main Force":
                        date = dt.fromtimestamp((quota[division]["Cycle"]["End"]))
                    else:
                        date = dt.fromtimestamp((quota[division]["Cycle"]["End"] - quota[division]["Cycle"]["Interval"] + 2592000)) # 1 month
                    rostersheets[index].update_cell(userinfo["Row"], rosters[index].headers["Activity Strike Removal Date"], date.strftime(r'%m/%d/%Y'))
                    userinfo["Activity Strike Removal Date"] = date.strftime(r'%m/%d/%Y')
                    await intact.guild.get_channel(cfg.logchannel_ids[division]).send(embed=Embed(color=cfg.embedcolors[division] ,title="Activity Strike Added", description=f"Activity Strike Added to `{usr}` by {intact.user.mention}").add_field(name="Activity Strikes", value=f"0 -> {userinfo['Activity Strikes']}").add_field(name="Removal Date", value=userinfo['Activity Strike Removal Date']).set_author(name=f"{comuser} > {user}"))
                    continue

                elif view.rank:
                    # rank changing, this code is so fucked, but it works, and it's like, semi efficient.
                    view = CancelButton()
                    if division == "Main Force":
                        if userinfo["Rank"] in ("Task Force Leader"):
                            rankselect = RosterRankSelect(0, 2, 5, "Security Major", division)
                        else:
                            rankselect = RosterRankSelect(0, 2, 5, comuserinfo["Rank"], division)
                    else:
                        rankselect = RosterRankSelect(1, remove_bottom_row(rostersheets[1], division)[-1].row, 6, comuserinfo["Rank"], division)
                    view.add_item(rankselect)
                    await intact.edit_original_response(view=view)

                    x = 1
                    while not rankselect.selected and not view.cancel:
                        await asyncio.sleep(1)
                        x+=1
                        if x >= 100:
                            await intact.delete_original_response()
                            return
                        
                    if view.cancel:
                        continue

                    elif rankselect.selection != userinfo["Rank"]:
                        # if the rank has in fact been changed
                        if rankselect.selection in quota[division]['Cycle']['NCOs-COs'] and division == "Main Force":
                            # if shifting points is needed.
                            ncoranks = cfg.NCOroster.col_values(col=14)
                            ncoranks.remove("Roster Ranks")
                            coranks = cfg.cfg.COroster.col_values(col=19)
                            coranks.remove("Roster Ranks")
                            try: # nco -> nco
                                if ncoranks.index(rankselect.selection) and ncoranks.index(userinfo["Rank"]):
                                    shift_point_rows(quota[division]['Cycle']['NCOs-COs'], userinfo["Rank"], "Del")
                                    shift_point_rows(quota[division]['Cycle']['NCOs-COs'], rankselect.selection, "Add")
                            except:
                                None
                            try: # co -> co
                                if coranks.index(rankselect.selection) and coranks.index(userinfo["Rank"]):
                                    shift_point_rows(quota[division]['Cycle']['NCOs-COs'], userinfo["Rank"], "Del")
                                    shift_point_rows(quota[division]['Cycle']['NCOs-COs'], rankselect.selection, "Add")
                            except:
                                None
                            try: # nco -> co
                                if coranks.index(rankselect.selection) and ncoranks.index(userinfo["Rank"]):
                                    shift_point_rows(quota[division]['Cycle']['NCOs-COs'], userinfo["Rank"], "Del")
                                    shift_point_rows(quota[division]['Cycle']['NCOs-COs'], rankselect.selection, "Add")
                            except:
                                None
                            try: # co -> nco
                                if ncoranks.index(rankselect.selection) and coranks.index(userinfo["Rank"]):
                                    shift_point_rows(quota[division]['Cycle']['NCOs-COs'], userinfo["Rank"], "Del")
                                    shift_point_rows(quota[division]['Cycle']['NCOs-COs'], rankselect.selection, "Add")
                            except:
                                try: # nco/co -> non
                                    if ncoranks.index(userinfo["Rank"]) or coranks.index(userinfo["Rank"]):
                                        shift_point_rows(quota[division]['Cycle']['NCOs-COs'], userinfo["Rank"], "Del")
                                except: # non -> nco/co
                                    shift_point_rows(quota[division]['Cycle']['NCOs-COs'], rankselect.selection, "Add")

                        # onto the actual ranking        
                        ranks = list(quota[division].keys())
                        ranks.remove("Cycle")

                        if division != "Main Force" and rankselect.selection == ranks[-1]:
                            # this is the special TFL sequence
                            usercopyrow = rostersheets[index].row_values(userinfo["Row"], value_render_option=ValueRenderOption.formula)
                            rostersheets[index].delete_rows(userinfo["Row"], userinfo["Row"])
                            newrow = rostersheets[index].find(division).row
                            rostersheets[index].insert_row(usercopyrow, newrow, value_input_option="USER_ENTERED")
                            quotastring = get_quota_string(division, rankselect.selection).replace("{row}", str(newrow))
                            try:
                                rostersheets[index].update_cells([Cell(newrow, rosters[index].headers["Quota"], quotastring), Cell(newrow, rosters[index].headers["Rank"], rankselect.selection), Cell(newrow, rosters[index].headers["Total Events"], f"=0+I{newrow}")], value_input_option="USER_ENTERED")
                            except:
                                rostersheets[index].update_cells([Cell(newrow, rosters[index].headers["Quota"], quotastring), Cell(newrow, rosters[index].headers["Rank"], rankselect.selection)], value_input_option="USER_ENTERED")
                        
                        elif ranks.index(rankselect.selection) > ranks.index(userinfo["Rank"]):
                            # promotion
                            usercopyrow = rostersheets[index].row_values(userinfo["Row"], value_render_option=ValueRenderOption.formula)
                            try:
                                i = ranks.index(rankselect.selection)
                                while True:
                                    try:
                                        newrow = remove_bottom_row(rostersheets[index], ranks[i])[-1].row
                                        copyrow = rostersheets[index].row_values(newrow, value_render_option=ValueRenderOption.formula)
                                        break
                                    except Exception as e:
                                        if "find any cells" in e.args[0]:
                                            i+=1
                                        else:
                                            print(e)
                                            raise
                            except Exception as e:
                                usercopyrow = rostersheets[index].row_values(userinfo["Row"], value_render_option=ValueRenderOption.formula)
                                rostersheets[index].delete_rows(userinfo["Row"], userinfo["Row"])
                                newrow = rostersheets[index].find(division).row
                                rostersheets[index].insert_row(usercopyrow, newrow, value_input_option="USER_ENTERED")
                                quotastring = get_quota_string(division, rankselect.selection).replace("{row}", str(newrow))
                                try:
                                    rostersheets[index].update_cells([Cell(newrow, rosters[index].headers["Quota"], quotastring), Cell(newrow, rosters[index].headers["Rank"], rankselect.selection), Cell(newrow, rosters[index].headers["Total Events"], f"=0+I{newrow}")], value_input_option="USER_ENTERED")
                                except:
                                    rostersheets[index].update_cells([Cell(newrow, rosters[index].headers["Quota"], quotastring), Cell(newrow, rosters[index].headers["Rank"], rankselect.selection)], value_input_option="USER_ENTERED")
                            rostersheets[index].delete_rows(userinfo["Row"], userinfo["Row"])
                            rostersheets[index].insert_rows([copyrow, usercopyrow], newrow, value_input_option="USER_ENTERED")
                            rostersheets[index].delete_rows(newrow+2, newrow+2)
                            newrow = newrow+1
                            quotastring = get_quota_string(division, rankselect.selection).replace("{row}", str(newrow))
                            try:
                                rostersheets[index].update_cells([Cell(newrow, rosters[index].headers["Quota"], quotastring), Cell(newrow, rosters[index].headers["Rank"], rankselect.selection), Cell(newrow, rosters[index].headers["Total Events"], f"=0+I{newrow}")], value_input_option="USER_ENTERED")
                            except:
                                rostersheets[index].update_cells([Cell(newrow, rosters[index].headers["Quota"], quotastring), Cell(newrow, rosters[index].headers["Rank"], rankselect.selection)], value_input_option="USER_ENTERED")
                        
                        elif ranks.index(rankselect.selection) < ranks.index(userinfo["Rank"]):
                            # demotion
                            usercopyrow = rostersheets[index].row_values(userinfo["Row"], value_render_option=ValueRenderOption.formula)
                            try:
                                i = ranks.index(rankselect.selection)
                                while True:
                                    try:
                                        newrow = remove_bottom_row(rostersheets[index], ranks[i])[-1].row-1
                                        rostersheets[index].delete_rows(userinfo["Row"], userinfo["Row"])
                                        copyrow = rostersheets[index].row_values(newrow, value_render_option=ValueRenderOption.formula)
                                        break
                                    except Exception as e:
                                        if "find any cells" in e.args[0]:
                                            i+=1
                                        else:
                                            print(e)
                                            raise
                            except:
                                newrow = remove_bottom_row(rostersheets[index], division)[-1].row
                            rostersheets[index].insert_rows([copyrow, usercopyrow], newrow, value_input_option="USER_ENTERED")
                            rostersheets[index].delete_rows(newrow+2, newrow+2)
                            newrow = newrow+1
                            quotastring = get_quota_string(division, rankselect.selection).replace("{row}", str(newrow))
                            try:
                                rostersheets[index].update_cells([Cell(newrow, rosters[index].headers["Quota"], quotastring), Cell(newrow, rosters[index].headers["Rank"], rankselect.selection), Cell(newrow, rosters[index].headers["Total Events"], f"=0+I{newrow}")], value_input_option="USER_ENTERED")
                            except:
                                rostersheets[index].update_cells([Cell(newrow, rosters[index].headers["Quota"], quotastring), Cell(newrow, rosters[index].headers["Rank"], rankselect.selection)], value_input_option="USER_ENTERED")
                        
                        # sending a log and re-getting the rosters
                        await intact.guild.get_channel(cfg.logchannel_ids[division]).send(embed=Embed(color=cfg.embedcolors[division], title="Rank Changed", description=f"{user.mention}'s rank has been changed by {intact.user.mention}").add_field(name="Rank", value=f"{userinfo['Rank']} -> {rankselect.selection}").set_author(name=f"{comuser} > {user}"))
                        rostersheets, rosters = exportSheetData()
                        userinfo = rosters[index].members[usr]
                    continue

                elif view.mrkqta:
                    # marking quota if it's manual type
                    if quota[division][userinfo["Rank"]]["Type"] == "Manual":
                        if userinfo["Quota"] == "EXEMPT":
                            continue
                        elif userinfo["Quota"] == "COMPLETED":
                            rostersheets[index].cell(userinfo["Row"], rosters[index].headers["Quota"], "INCOMPLETE")
                            userinfo["Quota"] = "INCOMPLETE"
                        elif userinfo["Quota"] == "INCOMPLETE":
                            rostersheets[index].cell(userinfo["Row"], rosters[index].headers["Quota"], "COMPLETED")
                            userinfo["Quota"] = "COMPLETED"
                    continue
                continue
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Roster {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Roster {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
        
    print(f"{cfg.logstamp()}[Setup]{cfg.Success} Roster command group setup complete")
