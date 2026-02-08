from python.helpers import exportSheetData, get_local_path, get_scgroup_rank, discord_to_username, remove_bottom_row, get_quota_string, send_dm
from python.uiclasses import YesorNo, QuotaEdit, CycleEdit, RankQuotaEdit, RosterRankSelect, CancelorBack
from python.helpers import username_to_discord_id as user_to_uid
from discord import Interaction, app_commands, Embed, Member
from gspread import Cell, Worksheet
from asyncio import run as asyncrun
from traceback import format_exc
from datetime import datetime
import data.config as cfg
from asyncio import sleep
import inspect
import json

now = datetime.now

COMMAND_NAME = "quota"

GUILD_IDS = [
    588427075283714049, #MF
    653542671100411906, #NTSH
    691298558032478208, #IF
    672480434549948438, #TC
    661593066330914828  #TAG
]

# checks an IN for validity
def check_notice(date, quota):
    try:
        intdate = int(datetime.strptime(date, r'%m/%d/%Y').timestamp())
    except:
        raise Exception("{user}'s Exemption Cell caused an cfg.Error")

    if intdate > quota["Cycle"]["Start"] + (quota["Cycle"]["Interval"]/2):
        return True
    else:
        return False

# these are quota reset functions, this is the closest thing to logic that I 
# felt like actually doing, because a bunch of them are different in slight ways.
# I didn't want to do all that logic so I just ctrl+c ctrl+v and changed minor 
# things per function.  
def NTSH(userinfo: dict, headers: dict, quota: dict, user: Member):
    updcells = []
    # basic cells that will get updated no matter what
    updcells.append(Cell(userinfo["Row"], headers["Minutes"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Honor"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Events"], 0))
    
    # Handle Inac Notice/OVERTIME
    if userinfo["Exempt Until"] != "":
        try:
            # try block is to catch the datetime cfg.Error from misconfigured exemption cells
            
            # handle overtime
            if userinfo["Exempt Until"] == "OVERTIME":
                # update exemption cell & return
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                if quota[userinfo['Rank']]["Type"] == "Manual":
                    updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
                return updcells, "Overtime"
            # if not overtime, check the IN
            elif check_notice(userinfo["Exempt Until"], quota):
                intdate = int(datetime.strptime(userinfo["Exempt Until"], r'%m/%d/%Y').timestamp())
                # is it valid into the next cycle?
                if intdate <= quota["Cycle"]["Start"]:
                    # nope
                    # update the cell
                    updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                    # attempt to remove IN role
                    try:
                        asyncrun(user.remove_roles(user.get_role(777273067511611422)))
                    except:
                        None
                    if quota[userinfo['Rank']]["Type"] == "Manual":
                        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))      
                return updcells, "Exempt"
            # else, update the exempt cell, but change the quota based on the usual req and proceed as usual
            else:
                # attempt removing the IN Role for fun
                try:
                    asyncrun(user.remove_roles(user.get_role(777273067511611422)))
                except:
                    None
                if quota[userinfo['Rank']]['Type'] == "Manual":
                    return None, "Manual Reset Needed"
                elif userinfo['Minutes'] < quota[userinfo['Rank']]['Time'] or userinfo['Events'] < quota[userinfo['Rank']]['Event']:
                    userinfo["Quota"] = "INCOMPLETE"
                else:
                    userinfo['Quota'] = "COMPLETE"
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
        except Exception as e:
            print(e)
            return None, "Manual Reset Needed"
    
    if quota[userinfo['Rank']]["Type"] == "Manual":
        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
    # Handle INCOMPLETE
    if userinfo["Quota"] == "INCOMPLETE":
        # 2nd strike is a exile
        if int(userinfo["Activity Strikes"]) == 2 and int(userinfo["Punishments"]) == 1:
            # remove all roles
            for role in user.roles:
                try:
                    if ("Medal", "Star", "Finest") not in role.name:
                        asyncrun(user.remove_roles(role.id))
                except:
                    continue
            try:
                asyncrun(user.add_roles(user.guild.get_role(773221920485015552)))
            except Exception as e:
                print(f"{cfg.logstamp()}[Quota reset][NTSH]{cfg.Error} removing role from {user}:", e)
            updcells.append(Cell(userinfo['Row'], headers["Punishments"], 2))
            return updcells, "Incomplete - Exile"
        # 2nd AC strike
        elif int(userinfo["Activity Strikes"]) == 1:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "Incomplete - 2nd Activity Strike"
        # 1st Strike
        elif int(userinfo["Activity Strikes"]) == 2:
            # update cells
            updcells.append(Cell(userinfo['Row'], headers["Activity Strikes"], 0))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], ""))
            updcells.append(Cell(userinfo['Row'], headers["Punishments"], 1))
            # attempt to add striked role
            try:
                user.add_roles(user.guild.get_role(759756623484289044))
            except:
                None
            return updcells, "Incomplete - Strike Given"
        # 1st AC strike
        else:
            # update cells & return
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "Incomplete - 1st Activity Strike"
        
    # Handle COMPLETE
    elif userinfo["Quota"] == "COMPLETED":
        # check for activity strikes to remove them
        if int(userinfo["Activity Strikes"]) > 0:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], ""))
            updcells.append(Cell(userinfo['Row'], headers['Activity Strikes'], int(userinfo["Activity Strikes"])-1))
        # check to see if they will still have AC strikes
        if int(userinfo["Activity Strikes"])-1 > 0:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
        return updcells, "Complete"
    return None, "Issue - Hit Bottom"

def MF(userinfo: dict, headers: dict, quota: dict, user: Member):
    updcells = []
    # basic cells that will get updated no matter what
    updcells.append(Cell(userinfo["Row"], headers["Minutes"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Honor"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Events"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Total Events"], f'=I{userinfo["Row"]}+{userinfo["Events"]}'))
    # Handle Inac Notice/OVERTIME
    if userinfo["Exempt Until"] != "" or userinfo['Quota'] == "EXEMPT":
        try:
            # try block is to catch the datetime cfg.Error from misconfigured exemption cells
            
            # handle overtime
            if userinfo["Exempt Until"] == "OVERTIME":
                # update exemption cell & return
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                if quota[userinfo['Rank']]["Type"] == "Manual":
                    updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
                return updcells, "Overtime (Exempt)"
            # if not overtime, check the IN
            elif check_notice(userinfo["Exempt Until"], quota):
                intdate = int(datetime.strptime(userinfo["Exempt Until"], r'%m/%d/%Y').timestamp())
                # is it valid into the next cycle?
                if intdate < quota["Cycle"]["Start"]:
                    # nope
                    # update the cell and return
                    updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                    if quota[userinfo['Rank']]["Type"] == "Manual":
                        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
                return updcells, "Exempt"
            else:
                # else, update the exempt cell, but change the quota based on the usual req and proceed as usual
                if quota[userinfo['Rank']]['Type'] == "Manual":
                    return None, "Manual Reset Needed"
                elif userinfo['Minutes'] < quota[userinfo['Rank']]['Time'] or userinfo['Events'] < quota[userinfo['Rank']]['Event']:
                    userinfo["Quota"] = "INCOMPLETE"
                else:
                    userinfo['Quota'] = "COMPLETE"
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
        except Exception as e:
            print(e)
            return None, "Manual Reset Required"
        
    if quota[userinfo['Rank']]["Type"] == "Manual":
        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
    # Handle INCOMPLETE
    if userinfo["Quota"] == "INCOMPLETE":
        # if user is reaching max strikes
        if int(userinfo["Activity Strikes"])+1 == 3:
            # update cells & return
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + 2592000)).strftime(r'%m/%d/%Y'))) # one month from issuence
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "Incomplete - Demotion Punishment"
        # else buisness as normal
        else:
            # update cells & return
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + 2592000)).strftime(r'%m/%d/%Y'))) # one month from issuence
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "Incomplete"
    # Handle COMPLETE
    elif userinfo["Quota"] == "COMPLETED":
        # check for activity strikes to remove them
        if int(userinfo["Activity Strikes"]) > 0:
            try: # if this fucks oh well
                intdate = int(datetime.strptime(userinfo["Activity Strike Removal Date"], r'%m/%d/%Y').timestamp())
            except:
                return None, "Manual Reset Required"
            if intdate < quota["Cycle"]["End"]:
                # if it's been a month, get that bad boy gone
                updcells.append(Cell(userinfo['Row'], headers['Activity Strikes'], int(userinfo["Activity Strikes"])-1))
                # check to see if they will still have AC strikes
                if int(userinfo["Activity Strikes"])-1 > 0:
                    updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + 2592000)).strftime(r'%m/%d/%Y')))
                else:
                    updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], '=""'))
        return updcells, "Complete"
    return None, "Issue"

def TAG(userinfo: dict, headers: dict, quota: dict, user: Member):
    updcells = []
    # basic cells that will get updated no matter what
    updcells.append(Cell(userinfo["Row"], headers["Minutes"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Honor"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Events"], 0))
    if quota[userinfo['Rank']]["Type"] == "Manual":
        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
    # Handle Inac Notice/OVERTIME
    if userinfo["Exempt Until"] != "" or userinfo['Quota'] == "EXEMPT":
        try:
            # try block is to catch the datetime cfg.Error from misconfigured exemption cells
            
            # handle overtime
            if userinfo["Exempt Until"] == "OVERTIME":
                # update exemption cell & return
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                if quota[userinfo['Rank']]["Type"] == "Manual":
                    updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
                return updcells, "Overtime (Exempt)"
            # if not overtime, check the IN
            elif check_notice(userinfo["Exempt Until"], quota):
                intdate = int(datetime.strptime(userinfo["Exempt Until"], r'%m/%d/%Y').timestamp())
                # is it valid into the next cycle?
                if intdate < quota["Cycle"]["Start"]:
                    # nope
                    if quota[userinfo['Rank']]["Type"] == "Manual":
                        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
                    # update the cell and return
                    updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                return updcells, "Exempt"
            else:
                # else, update the exempt cell, but change the quota based on the usual req and proceed as usual
                if quota[userinfo['Rank']]['Type'] == "Manual":
                    return None, "Manual Reset Needed"
                elif userinfo['Minutes'] < quota[userinfo['Rank']]['Time'] or userinfo['Events'] < quota[userinfo['Rank']]['Event']:
                    userinfo["Quota"] = "INCOMPLETE"
                else:
                    userinfo['Quota'] = "COMPLETE"
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
        except Exception as e:
            print(e)
            return None, "Manual Reset Required"
    # manual check
    if quota[userinfo['Rank']]["Type"] == "Manual":
        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
    # Handle INCOMPLETE
    if userinfo["Quota"] == "INCOMPLETE":
        # if sentry hits 2 strikes
        if int(userinfo["Activity Strikes"])+1 == 2 and userinfo['Rank'] == "Sentry":
            # update cells & return
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "2nd Activity Strike - Exile"
        # if anyone else hits 3 strikes
        elif int(userinfo["Activity Strikes"])+1 == 2:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "3rd Activity Strike - Exile"
        # else buisness as normal
        else:
            # update cells & return
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "Incomplete"
    # Handle COMPLETE
    elif userinfo["Quota"] == "COMPLETED":
        # check for activity strikes to remove them
        if int(userinfo["Activity Strikes"]) > 0:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], ""))
            updcells.append(Cell(userinfo['Row'], headers['Activity Strikes'], int(userinfo["Activity Strikes"])-1))
        # check to see if they will still have AC strikes
        if int(userinfo["Activity Strikes"])-1 > 0:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
        return updcells, "Complete"
    return None, "Issue"

def TC(userinfo: dict, headers: dict, quota: dict, user: Member):
    updcells = []
    # basic cells that will get updated no matter what
    updcells.append(Cell(userinfo["Row"], headers["Minutes"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Honor"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Events"], 0))
    # Handle Inac Notice/OVERTIME
    if userinfo["Exempt Until"] != "" or userinfo['Quota'] == "EXEMPT":
        try:
            # try block is to catch the datetime cfg.Error from misconfigured exemption cells
            
            # handle overtime
            if userinfo["Exempt Until"] == "OVERTIME":
                # update exemption cell & return
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                if quota[userinfo['Rank']]["Type"] == "Manual":
                    updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
                return updcells, "Overtime (Exempt)"
            # if not overtime, check the IN
            elif check_notice(userinfo["Exempt Until"], quota):
                intdate = int(datetime.strptime(userinfo["Exempt Until"], r'%m/%d/%Y').timestamp())
                # is it valid into the next cycle?
                if intdate < quota["Cycle"]["Start"]:
                    # nope
                    # update the cell and return
                    updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                    if quota[userinfo['Rank']]["Type"] == "Manual":
                        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
                return updcells, "Exempt"
            else:
                # else, update the exempt cell, but change the quota based on the usual req and proceed as usual
                if quota[userinfo['Rank']]['Type'] == "Manual":
                    return None, "Manual Reset Needed"
                elif userinfo['Minutes'] < quota[userinfo['Rank']]['Time'] or userinfo['Events'] < quota[userinfo['Rank']]['Event']:
                    userinfo["Quota"] = "INCOMPLETE"
                else:
                    userinfo['Quota'] = "COMPLETE"
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
        except Exception as e:
            print(e)
            return None, "Manual Reset Required"
        
    if quota[userinfo['Rank']]["Type"] == "Manual":
        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))    
    # Handle INCOMPLETE
    if userinfo["Quota"] == "INCOMPLETE":
        # if user is reaching max strikes
        if int(userinfo["Activity Strikes"])+1 == 3:
            # update cells & return
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "3rd Activity Strike - Exile"
        # else buisness as normal
        else:
            # update cells & return
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "Incomplete"
    # Handle COMPLETE
    elif userinfo["Quota"] == "COMPLETED":
        # check for activity strikes to remove them
        if int(userinfo["Activity Strikes"]) > 0:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], ""))
            updcells.append(Cell(userinfo['Row'], headers['Activity Strikes'], int(userinfo["Activity Strikes"])-1))
        # check to see if they will still have AC strikes
        if int(userinfo["Activity Strikes"])-1 > 0:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
        return updcells, "Complete"
    return None, "Issue"

def IF(userinfo: dict, headers: dict, quota: dict, user: Member):
    updcells = []
    # basic cells that will get updated no matter what
    updcells.append(Cell(userinfo["Row"], headers["Minutes"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Honor"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Events"], 0))
    updcells.append(Cell(userinfo["Row"], headers["Total Time"], float(userinfo["Minutes"]) + float(userinfo["Total Time"])))
    # Handle Inac Notice/OVERTIME
    if userinfo["Exempt Until"] != "" or userinfo['Quota'] == "EXEMPT":
        try:
            # try block is to catch the datetime cfg.Error from misconfigured exemption cells
            
            # handle overtime
            if userinfo["Exempt Until"] == "OVERTIME":
                # update exemption cell & return
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                if quota[userinfo['Rank']]["Type"] == "Manual":
                    updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
                return updcells, "Overtime (Exempt)"
            # if not overtime, check the IN
            elif check_notice(userinfo["Exempt Until"], quota):
                intdate = int(datetime.strptime(userinfo["Exempt Until"], r'%m/%d/%Y').timestamp())
                # is it valid into the next cycle?
                if intdate < quota["Cycle"]["Start"]:
                    # nope
                    # update the cell and return
                    updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
                    if quota[userinfo['Rank']]["Type"] == "Manual":
                        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
                return updcells, "Exempt"
            else:
                # else, update the exempt cell, but change the quota based on the usual req and proceed as usual
                if quota[userinfo['Rank']]['Type'] == "Manual":
                    return None, "Manual Reset Needed"
                elif userinfo['Minutes'] < quota[userinfo['Rank']]['Time'] or userinfo['Events'] < quota[userinfo['Rank']]['Event']:
                    userinfo["Quota"] = "INCOMPLETE"
                else:
                    userinfo['Quota'] = "COMPLETE"
                updcells.append(Cell(userinfo["Row"], headers["Exempt Until"], ""))
        except Exception as e:
            print(e)
            return None, "Manual Reset Required"
        
    if quota[userinfo['Rank']]["Type"] == "Manual":
        updcells.append(Cell(userinfo["Row"], headers["Quota"], "INCOMPLETE"))
    # Handle INCOMPLETE
    if userinfo["Quota"] == "INCOMPLETE":
        # if user is reaching max strikes
        if int(userinfo["Activity Strikes"])+1 == 2:
            # update cells & return
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "2nd Activity Strike - Exile"
        # else buisness as normal
        else:
            # update cells & return
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
            updcells.append(Cell(userinfo["Row"], headers["Activity Strikes"], int(userinfo["Activity Strikes"])+1))
            return updcells, "Incomplete"
    # Handle COMPLETE
    elif userinfo["Quota"] == "COMPLETED":
        # check for activity strikes to remove them
        if int(userinfo["Activity Strikes"]) > 0:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], ""))
            updcells.append(Cell(userinfo['Row'], headers['Activity Strikes'], int(userinfo["Activity Strikes"])-1))
        # check to see if they will still have AC strikes
        if int(userinfo["Activity Strikes"])-1 > 0:
            updcells.append(Cell(userinfo["Row"], headers["Activity Strike Removal Date"], datetime.fromtimestamp((quota["Cycle"]["End"] + quota["Cycle"]["Interval"])).strftime(r'%m/%d/%Y')))
        return updcells, "Complete"
    return None, "Issue"

# gets the diffs for the current vs amended settings
def get_diffs(quota, untouched):
    diffs = {}
    for x in quota:
        for y in quota[x]:
            for z in quota[x][y]:
                if quota[x][y][z] != untouched[x][y][z]:
                    try:
                        diffs[x]
                        try:
                            diffs[x][y].update({z : quota[x][y][z]})

                        except:
                            diffs[x].update({y : {z : quota[x][y][z]}})
                    except:
                        diffs.update({x : {y : {z : quota[x][y][z]}}})
    return diffs

# checks for main force promotion requirements for a user
def check_promo(username: str, rank: str, events: int):
    with open(get_local_path("data\\promotionreq.json"), "r") as f:
        req = json.load(f)
        f.close()
    with open(get_local_path("data\\totaltimes.json"), "r") as f:
        times = json.load(f)
        f.close()
    try:
        if times[username] >= req[rank]["Total Time"] and int(events) >= req[rank]["Total Events"]:
            return True
    except:
        None
    return False
    

def setup(tree: app_commands.CommandTree):
    # quota command group
    quota = app_commands.Group(name="quota", description="Quota Management", guild_ids=GUILD_IDS, guild_only=True)
    tree.add_command(quota)

    # Settings command for most quota settings in the bot's DB. This includes, a list of NCOs/COs, minutes/events/points quota for all ranks, the ability to switch between
    @quota.command(name="settings", description="Edit the quota for a rank in your division.")
    async def settings(intact: Interaction):
        try:
            print(f"{cfg.logstamp()}[Quota settings] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            
            # check division lock
            division = cfg.serverid_to_name[str(intact.guild_id)]
            if division == "Main Force":
                index = 0
            else:
                index = 1
            rostersheets, rosters = exportSheetData()
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error", description=e))

            # rank lock check - This one is for later
            grouprank = get_scgroup_rank([comuser])
            comrankname = grouprank[comuser]['name']
            if comrankname == "Security Major":
                comrankname = None
            else:
                comrankname = rosters[index]
            comrank = grouprank[comuser]['rank']

            # actual rank lock check
            if division == "Main Force" and comrank < 9:
                await intact.followup.send("You're not a high enough rank to use this command.")
                return
            elif comrank < 8:
                await intact.followup.send("You're not a high enough rank to use this command.")
                return
            
            # load up 2 copies for diffs of the quota
            with open(get_local_path("data\\quota.json"), "r") as f:
                quota = json.load(f)
                f.close()
            with open("data\\quota.json", "r") as f:
                untouched = json.load(f)
                f.close()

            # start the interface
            view = QuotaEdit()
            await intact.followup.send("Select an option to change.", view=view)
            while True:
                # settings menu!!
                diffs = get_diffs(quota, untouched)
                ind = await view.wait()
                if ind:
                    return
                if view.cancel:
                    await intact.delete_original_response()
                    return
                elif view.save:
                    break
                await view.wait()
                # cycle menu
                if view.cycletime:
                    # only mainforce is allowed to use points fuck TFD's that shit will make me have a stroke rewriting this
                    if division == "Main Force":
                        points = True
                    else:
                        points = False
                    view = CycleEdit(quota=quota[division]['Cycle'], points=points, save=bool(len(diffs)))
                    while not view.back and not view.cancel and not view.save:
                        diffs = get_diffs(quota, untouched)

                        # this is for embeds
                        if quota[division]['Cycle']['Interval'] == 604800:
                            interval = "Weekly"
                        else:
                            interval = "Bi-Weekly"
                        if quota[division]['Cycle']['Points']:
                            points = "Enabled"
                        else:
                            points = "Disabled"

                        # formatting NCO/CO list
                        ncoscos = ""
                        for x in quota[division]['Cycle']["NCOs-COs"]:
                            ncoscos += f"`{x}`  "

                        view = CycleEdit(quota=quota[division]['Cycle'], points=points, save=bool(len(diffs)))
                        await intact.edit_original_response(view=view, content=None,embed=Embed(title=f"Quota Cycle Settings For: {division}", description=f"**Cycle Start:**\n<t:{quota[division]['Cycle']['Start']}:d>\n**Cycle End:**\n<t:{quota[division]['Cycle']['End']}:d>\n**Interval:**\n`{interval}`\n**Points:**\n`{points}`\n**NCOs & COs:**\n{ncoscos}", color=cfg.embedcolors[division]))
                        ind = await view.wait()
                        if ind:
                            return
                        
                        if view.selection == "Fix":
                            # all this does is set the cycle to the current week (or bi-week)
                            compdate = now().timestamp()
                            while compdate < quota[division]['Cycle']['Start'] or compdate > quota[division]['Cycle']['End']:
                                if compdate < quota[division]['Cycle']['Start']:
                                    quota[division]['Cycle']['Start'] -= quota[division]['Cycle']['Interval']
                                    quota[division]['Cycle']['End'] -= quota[division]['Cycle']['Interval']
                                elif compdate > quota[division]['Cycle']['End']:
                                    quota[division]['Cycle']['Start'] += quota[division]['Cycle']['Interval']
                                    quota[division]['Cycle']['End'] += quota[division]['Cycle']['Interval']
                            continue

                        elif view.selection == "Interval":
                            # this changes the cycle setting for weekly/bi-weekly
                            if view.userenteredvalue < 1209600:
                                quota[division]['Cycle'][view.selection] = view.userenteredvalue
                                quota[division]['Cycle']['End'] -= quota[division]['Cycle']['Interval']
                            else:
                                quota[division]['Cycle']['End'] += quota[division]['Cycle']['Interval']
                                quota[division]['Cycle'][view.selection] = view.userenteredvalue
                            continue

                        elif view.selection == "addsubrank":
                            # this is for main force, ish, but basically just adds a rank to the list of NCOs/COs
                            view = CancelorBack()
                            if division == "Main Force":
                                select = RosterRankSelect(0,2,5, None, division)
                            else:
                                select = RosterRankSelect(1, remove_bottom_row(rostersheets[1], division)[-1].row, 6, None, division)
                            view.add_item(select)
                            await intact.edit_original_response(content="Select a Rank, Cancel, or Go Back", view=view)
                            x = 0
                            while not select.selected and not view.back and not view.cancel:
                                await sleep(1)
                                x += 1
                                if x >= 100:
                                    return
                                
                            if view.back:
                                continue

                            elif view.cancel:
                                await intact.delete_original_response()
                                return
                            
                            # this actually adds the rank to the list of NCOs/COs
                            editrank = select.selection
                            if editrank not in quota[division]['Cycle']['NCOs-COs']:
                                quota[division]['Cycle']['NCOs-COs'].append(editrank)
                            else:
                                quota[division]['Cycle']['NCOs-COs'].remove(editrank)
                                if quota[division][editrank]["String"] not in ("1", "2"):
                                    try:
                                        quota[division][editrank]["String"].strip("NCO")
                                    except:
                                        try:
                                            quota[division][editrank]["String"].strip("CO")
                                        except:
                                            None
                            continue

                        elif view.selection == "Points":
                            # turns on points for NCOs/COs
                            if division != "Main Force":
                                continue
                            quota[division]['Cycle'][view.selection] = view.userenteredvalue
                            if not view.userenteredvalue:
                                for x in quota[division]:
                                    if x == "Cycle":
                                        continue
                                    if quota[division][x]["String"] not in ("1", "2"):
                                        try:
                                            quota[division][editrank]["String"].strip("NCO")
                                        except:
                                            try:
                                                quota[division][editrank]["String"].strip("CO")
                                            except:
                                                None
                            continue

                    if view.cancel:
                        await intact.delete_original_response()
                        return
                    
                    elif view.back:
                        diffs = get_diffs(quota, untouched)
                        view = QuotaEdit(save=bool(len(diffs)))
                        await intact.edit_original_response(content="Select an option to change.", view=view, embed=None)
                        continue

                    elif view.save:
                        break
                    
                            
                # rank changing menu
                elif view.rankquota:
                    view =  CancelorBack()
                    if division == "Main Force":
                        select = RosterRankSelect(0,2,5, comrankname, division)
                    else:
                        select = RosterRankSelect(1, remove_bottom_row(rostersheets[1], division)[-1].row, 6, comrankname, division)
                    view.add_item(select)
                    await intact.edit_original_response(content="Select a Rank, Cancel, or Go Back", view=view)

                    x = 0
                    while not select.selected and not view.back and not view.cancel:
                        await sleep(1)
                        x += 1
                        if x >= 100:
                            return
                        
                    if view.cancel:
                        await intact.delete_original_response()
                        return
                    
                    if view.back:
                        diffs = get_diffs(quota, untouched)
                        view = QuotaEdit(save=bool(len(diffs)))
                        await intact.edit_original_response(content="Select an option to change.", view=view)
                        continue

                    editrank = select.selection
                    view = RankQuotaEdit(quota=quota[division][editrank], save=bool(len(diffs)))
                    while not view.cancel and not view.back and not view.save:
                        diffs = get_diffs(quota, untouched)
                        
                        # this is for the embeds
                        if quota[division][editrank]['Event'] == 99:
                            events = "Disabled"
                        else:
                            events = quota[division][editrank]['Event']
                        if quota[division][editrank]["Time"] == 0:
                            minutes = "Disabled"
                        else:
                            minutes = quota[division][editrank]['Time']
                        if "1" in quota[division][editrank]["String"]:
                            andor = "Complete Either"
                        else:
                            andor = "Complete Both"
                        if quota[division][editrank]['Points'] == 0 or not quota[division]['Cycle']['Points']:
                            points = "Disabled"
                        else:
                            points = quota[division][editrank]['Points']
                        
                        view = RankQuotaEdit(quota=quota[division][editrank], points=quota[division]['Cycle']['Points'], save=bool(len(diffs)))
                        await intact.edit_original_response(view=view, content=None,embed=Embed(title=f"Quota Settings for Rank: {select.selection}", description=f"**Type:**\n`{quota[division][select.selection]['Type']}`\n**Events Quota:**\n`{events}`\n**Minutes Quota:**\n`{minutes}`\n**Both or Either:**\n`{andor}`\n**Points Quota:**\n`{points}`", color=cfg.embedcolors[division]))
                        ind = await view.wait()
                        if ind:
                            return
                        
                        if view.selection in ("Time", "Event"):
                            # changing time and event values
                            try:
                                # this is input sanitization
                                if int(view.userenteredvalue) > 0:
                                    None
                            except:
                                continue
                            try:
                                if view.selection == "Event" and int(view.userenteredvalue) == 0:
                                    # this is disabling events, which forces the change of quota strings to make events "optional"
                                    quota[division][editrank][view.selection] = 99
                                    # makes sure NCO and Officer quota strings are changed aswell
                                    if "O" in quota[division][editrank]['String']:
                                        quota[division][editrank]['String'] = quota[division][editrank]['String'].replace("2", "1")
                                    else:
                                        quota[division][editrank]['String'] = "1"
                                else:
                                    quota[division][editrank][view.selection] = int(view.userenteredvalue)
                            except:
                                None
                            continue
                        
                        # changing the string to make it be minutes AND events is not allowed, discord responce doesn't
                        # allow me to parse this and send a modal for a value to set events to
                        elif view.selection == "String" and quota[division][editrank]["Event"] == 99 and "1" in quota[division][editrank]['String']:
                            continue

                        elif view.selection == "Points" and quota[division]['Cycle'][view.selection]:
                            # changes points number
                            try:
                                # this is input sanitization
                                if int(view.userenteredvalue) > 0:
                                    None
                            except:
                                continue
                            if editrank not in quota[division]['Cycle']['NCOs-COs']:
                                continue

                            elif int(view.userenteredvalue) > 0:
                                for mem in rosters[index].members:
                                    if rosters[index].members[mem]["Rank"] == editrank:
                                        rankval = get_scgroup_rank([mem])
                                        rankval = rankval[mem]['rank']
                                        if rankval < 8:
                                            quota[division][editrank]['String'] = f"NCO{quota[division][editrank]['String']}"
                                        else:
                                            quota[division][editrank]['String'] = f"OFFICER{quota[division][editrank]['String']}"
                                quota[division][editrank][view.selection] = int(view.userenteredvalue)

                            elif int(view.userenteredvalue) == 0:
                                try:
                                    quota[division][editrank]['String'] = quota[division][editrank]['String'].strip("NCO")
                                except:
                                    try:
                                        quota[division][editrank]['String'] = quota[division][editrank]['String'].strip("OFFICER")
                                    except:
                                        None
                                quota[division][editrank][view.selection] = int(view.userenteredvalue)
                            continue

                        elif view.selection:
                            # quota string change, supports the NCO/Officer strings
                            if view.selection == "String" and "O" in quota[division][editrank]["String"]:
                                if view.userenteredvalue == "1":
                                    quota[division][editrank]['String'] = quota[division][editrank]['String'].replace("2", "1")
                                else:
                                    quota[division][editrank]['String'] = quota[division][editrank]['String'].replace("1", "2")
                            else:
                                quota[division][editrank][view.selection] = view.userenteredvalue
                            continue
                            
                    if view.cancel:
                        await intact.delete_original_response()
                        return
                    
                    if view.back:
                        diffs = get_diffs(quota, untouched)
                        view = QuotaEdit(save=bool(len(diffs)))
                        await intact.edit_original_response(content="Select an option to change.", view=view, embed=None)
                        continue

                    if view.save:
                        break
                
                # division wide quota edit
                elif view.divquota:
                    # getting first rank values
                    div: dict[str,str|int] = {"Type" : None, "Time" : None, "Event" : None, "String" : None}
                    for x in quota[division]:
                        if x == "Cycle":
                            continue
                        for y in quota[division][x]:
                            div[y] = quota[division][x][y]
                        break
                    # test first rank against every other, for differences
                    for x in quota[division]:
                        if x == "Cycle":
                            continue
                        for y in quota[division][x]:
                            if div[y] != quota[division][x][y]:
                                div[y] = "Mixed"

                    view = RankQuotaEdit(quota=div, save=bool(len(diffs)))
                    while not view.cancel and not view.back and not view.save:
                        diffs = get_diffs(quota, untouched)
                        
                        # this is for the embeds
                        if div["Event"] == 99:
                            events = "Disabled"
                        else:
                            events = div["Event"]
                        if div["Time"] == 0:
                            minutes = "Disabled"
                        else:
                            minutes = div['Time']
                        if div["String"] == "1":
                            andor = "Complete Either"
                        elif div["String"] == "2":
                            andor = "Complete Both"
                        else:
                            andor = div["String"]
                        
                        view = RankQuotaEdit(quota=div, save=bool(len(diffs)))
                        await intact.edit_original_response(view=view, content=None,embed=Embed(title=f"Division Wide Quota Settings for {division}", description=f"**Type:**\n`{div['Type']}`\n**Events Quota:**\n`{events}`\n**Minutes Quota:**\n`{minutes}`\n**Both or Either:**\n`{andor}`", color=cfg.embedcolors[division]))
                        ind = await view.wait()
                        if ind:
                            return
                        # changes the time/event value for all ranks
                        if view.selection in ("Time", "Event"):
                            try:
                                # input parsing
                                if int(view.userenteredvalue) > 0:
                                    None
                            except:
                                continue
                            try:
                                if view.selection == "Event" and int(view.userenteredvalue) == 0:
                                    div[view.selection] = 99
                                    div['String'] = "1"
                                    for x in quota[division]:
                                        if x == "Cycle":
                                            continue
                                        quota[division][x][view.selection] = div[view.selection]
                                        if quota[division][x]['Points'] > 0:
                                            try:
                                                quota[division][x]["String"].replace("2", div["String"])
                                            except:
                                                None
                                        else:
                                            quota[division][x]["String"] = div["String"]
                                else:
                                    div[view.selection] = int(view.userenteredvalue)
                                    for x in quota[division]:
                                        if x == "Cycle":
                                            continue
                                        quota[division][x][view.selection] = div[view.selection]
                            except:
                                None
                            continue
                        
                        elif view.selection:
                            if view.selection == "String" and quota[division][editrank]["Event"] == 99 and quota[division][editrank]['String'] == "1":
                                continue
                            div[view.selection] = view.userenteredvalue
                            for x in quota[division]:
                                if x == "Cycle":
                                    continue
                                quota[division][x][view.selection] = div[view.selection]
                            continue

                    if view.cancel:
                        await intact.delete_original_response()
                        return
                    
                    if view.back:
                        diffs = get_diffs(quota, untouched)
                        view = QuotaEdit(save=bool(len(diffs)))
                        await intact.edit_original_response(content="Select an option to change.", view=view, embed=None)
                        continue

                    if view.save:
                        break

            # if we are saing shit
            if view.save:
                diffs = get_diffs(quota, untouched)
                auditembed = Embed(title=f"Settings for {division} Quota changed",description=f"Quota Settings Changed By: {intact.user.mention}", color=cfg.embedcolors[division])
                # this is for embeds
                try:
                    if diffs[division]["Cycle"]['Interval'] < 1209600:
                        oldint = "Bi-Weekly"
                        newint = "Weekly"
                    else:
                        oldint = "Weekly"
                        newint = "Bi-Weekly"
                except:
                    None

                for x in diffs[division]:
                    string = ""
                    if x == "Cycle":
                        try:
                            diffs[division][x]['Start']
                            try:
                                diffs[division][x]['Interval']
                                auditembed.add_field(name="Cycle Settings Changed", value=f"Cycle Timing Fixed to Current Week/Bi-Week\n<t:{untouched[division][x]['Start']}:d> - <t:{untouched[division][x]['End']}:d> -> <t:{diffs[division][x]['Start']}:d> - <t:{diffs[division][x]['End']}:d>\nInterval Changed: `{oldint} -> {newint}`", inline=False)
                            except:
                                auditembed.add_field(name="Cycle Settings Changed", value=f"Cycle Timing Fixed to Current Week/Bi-Week\n<t:{untouched[division][x]['Start']}:d> - <t:{untouched[division][x]['End']}:d> -> <t:{diffs[division][x]['Start']}:d> - <t:{diffs[division][x]['End']}:d>", inline=False)
                        except:
                            try:
                                diffs[division][x]['Interval']
                                auditembed.add_field(name="Cycle Settings Changed", value=f"Interval Changed:\n`{oldint}` -> `{newint}`", inline=False)
                            except:
                                None
                        continue

                    for z in diffs[division][x]:
                        if z == "String":
                            if diffs[division][x][z] == "2":
                                string += "Time & Event Quota:\n`Complete Both Time AND Event(s)`\n"
                            else:
                                string += "Time & Event Quota:\n`Complete Either Time OR Event(s)`\n"
                            continue
                        elif z == "Type":
                            string += f"Quota Type:\n`{untouched[division][x][z]}` -> `{diffs[division][x][z]}`\n"
                        else:
                            try:
                                if untouched[division][x][z] == 0 or untouched[division][x][z] == 99:
                                    string += f"{z} Quota:\n`Disabled` -> `{diffs[division][x][z]}`\n"
                                else:
                                    raise
                            except:
                                string += f"{z} Quota:\n`{untouched[division][x][z]}` -> `{diffs[division][x][z]}`\n"
                    auditembed.add_field(name=f"{x} Quota Changed:", value=string, inline=False)
                await intact.edit_original_response(content="Saved!", embed=None, view=None)

                # save changed here
                with open(get_local_path("data\\quota.json"), "w") as f:
                    json.dump(quota, f, indent=2)
                    f.close()

                # push changes to roster
                cells: dict[list] = {}
                try:
                    diffs[division].pop("Cycle")
                except:
                    None
                # this makes the changes to the roster for any quota string changes done
                diffs = diffs[division]
                for user in rosters[index].members:
                    mem = rosters[index].members[user]
                    if mem['Rank'] in diffs.keys():
                        quota = get_quota_string(division, mem["Rank"])
                        try:
                            if quota:
                                cells[mem['Rank']].append(Cell(mem['Row'], rosters[index].headers["Quota"], quota.replace("{row}", str(mem["Row"]))))
                            else:
                                cells[mem['Rank']].append(Cell(mem['Row'], rosters[index].headers["Quota"], mem["Quota"]))
                        except:
                            if quota:
                                cells.update({mem['Rank'] : [Cell(mem['Row'], rosters[index].headers["Quota"], quota.replace("{row}", str(mem["Row"])))]})
                            else:
                                cells.update({mem['Rank'] : [Cell(mem['Row'], rosters[index].headers["Quota"], mem["Quota"])]})

                # sends the cell changes
                for x in cells:
                    rostersheets[index].update_cells(cells[x], value_input_option="USER_ENTERED")

            # send log         
            await intact.guild.get_channel(cfg.logchannel_ids[division]).send(embed=auditembed.set_author(name=f"{comuser}"))
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Quota {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Quota {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
        


    # Reset's a division's roster, and sends the reset statistics to a channel in that server.
    # - Universal Command
    # - Server Based
    # - Rank Locked
    # - Time Locked
    # - Division Locked (Disabled atm)
    @quota.command(name="reset", description="Perform a quota reset on your division's roster.")
    async def reset(intact: Interaction):
        try:
            print(f"{cfg.logstamp()}[Quota reset] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            with open(get_local_path("data\\quota.json"), "r") as f:
                quota = json.load(f)
                f.close()

            # sus out the correct roster to reset based on the server it's used in
            if intact.guild_id == 588427075283714049:
                division = "Main Force"
                rosterfunc = MF
                channel_id = [1465124824199205027]
            elif intact.guild_id == 653542671100411906:
                division = "Nothing To See Here"
                rosterfunc = NTSH
                channel_id = [1339847596977688626]
            elif intact.guild_id == 661593066330914828:
                division = "The Armed Gentlemen"
                rosterfunc = TAG
                channel_id = [1250483435873632300, 661599627312627753]
            elif intact.guild_id == 672480434549948438:
                division = "The Crazies"
                rosterfunc = TC
                channel_id = [688073006937014355]
            elif intact.guild_id == 691298558032478208:
                division = "Iron Fist"
                rosterfunc = IF
                channel_id = [1462550079201214669]

            rostersheets, rosters = exportSheetData()

            # comuser resolution
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error", description=e))
            embeddict: dict[str, list[str]] = {}

            if division == "Main Force":
                index = 0
                # rank lock, time check, and confirmation prompt here
                # try:
                #     if comuserinfo["TFD"] != "Directorate":
                #         await intact.followup.send("You can't reset a Roster that isn't yours.")
                #         return
                # except:
                #     None
                comrank = get_scgroup_rank([comuser])
                if comrank[comuser]['rank'] < 9: # if user is not captain+
                    await intact.followup.send("You're rank is not high enough to run this command.", ephemeral=True)
                    return
                
                if int(quota[division]["Cycle"]["End"]) - 10800 > int(datetime.now().timestamp()):
                    await intact.followup.send(f"You cannot reset the roster yet, you must wait until at least <t:{quota[division]['Cycle']['End']-10000}:t> to reset the Roster.", ephemeral=True)
                    return
                
                # confirmation prompt
                view = YesorNo()
                await intact.followup.send("Are you sure you want to reset the roster?", view=view)
                await view.wait()

                if view.no:
                    await intact.delete_original_response()
                    return
                
                elif view.yes:
                    await intact.edit_original_response(content="Reset in Progress, Please Wait.", view=None)

                # defining this because main force's roster is seperated by ranks, and the in between rows are protected, bulk updates will get stopped by those protected cells
                cells = {"Junior Guard": [], "Guard": [], "Experienced Guard": [], "Senior Guard": [], "Master Guard": [], "Security Supervisor": [], "Captain": [], "Security Major": []}

                for user in rosters[0].members:
                    # get userinfo, run the appropriate roster command, and update their cells
                    userinfo = rosters[0].members[user]
                    try:
                        updcells, actionneeded = rosterfunc(rosters[0].members[user], rosters[0].headers, quota[division], intact.guild.get_member(user_to_uid([user])[0]))
                    except:
                        # this is an cfg.Error thing.
                        updcells = None
                        actionneeded = "Manual Reset Required"

                    if updcells:
                        cells[userinfo["Rank"]] += updcells
                        if check_promo(user, userinfo["Rank"], userinfo["Total Events"]):
                            try:
                                embeddict["Due For Promotion"].append(user)
                            except:
                                embeddict.update({"Due For Promotion" : [user]})

                    if actionneeded:
                        try:
                            embeddict[actionneeded].append(user)
                        except:
                            embeddict.update({actionneeded : [user]})

                # special directorate reset
                dircells = remove_bottom_row(rostersheets[1], "Directorate")
                updcells = []
                headers = rosters[1].headers
                for cell in dircells:
                    updcells.append(Cell(cell.row,headers['Minutes'],0))
                    updcells.append(Cell(cell.row,headers['Honor'],0))
                    updcells.append(Cell(cell.row,headers['Events'],0))

                # mainforce specfic point resets for NCO/CO
                # also rewrote this to make it O SO MUCH NICER, FASTER AND SMALLER, also fixed rate limiting.
                def pointsreset(roster: Worksheet):
                    tpcell = roster.find("Total Points", in_row=1)
                    rowvals= roster.col_values(1)
                    updcells = []
                    ret = {}
                    try:
                        index = rowvals.index("")
                    except:
                        index = len(rowvals)
                    for x in range (1, index):
                        for i in range (3, tpcell.col):
                            updcells.append(Cell(x+1, i, 0))
                        ret.update({rowvals[x] : roster.cell(x+1, tpcell.col).value})
                    roster.update_cells(updcells)
                    return ret
                
                # do points resets
                points = pointsreset(cfg.NCOroster)
                points.update(pointsreset(cfg.COroster))
                rostersheets[1].update_cells(updcells)

                # update all the cells rank by rank
                # bulk updating is more efficient and won't rate limit me
                for rank in cells:
                    if len(cells[rank]) > 0:
                        rostersheets[0].update_cells(cells[rank], value_input_option="USER_ENTERED")
                        None
            else:
                index = 1
                # rank lock, time check, and confirmation prompt here
                # try:
                #     if comuserinfo["TFD"] != division:
                #         raise
                # except:
                #     await intact.followup.send("You can't reset a Roster that isn't yours.")
                #     return
                comrank = get_scgroup_rank([comuser])
                if comrank[comuser]['rank'] < 8: # if user is not TFD Officer+ 
                    await intact.followup.send("You're rank is not high enough to run this command.", ephemeral=True)
                    return
                if int(quota[division]["Cycle"]["End"]) - 10800 > int(datetime.now().timestamp()):
                    await intact.followup.send(f"You cannot reset the roster yet, you must wait until at least <t:{quota[division]['Cycle']['End']-10000}:t> to reset the Roster.", ephemeral=True)
                    return
                
                # confirmation prompt
                view = YesorNo()
                await intact.followup.send("Are you sure you want to reset the roster?", view=view)
                await view.wait()

                if view.no:
                    await intact.delete_original_response()
                    return
                
                elif view.yes:
                    await intact.edit_original_response(content="Reset in Progress, Please Wait.", view=None)

                cells = []
                for user in rosters[1].members:
                    # get userinfo, run the appropriate roster command, and update their cells
                    userinfo = rosters[1].members[user]
                    if userinfo["TFD"] == division:
                        try:
                            updcells, actionneeded = rosterfunc(rosters[1].members[user], rosters[1].headers, quota[division], intact.guild.get_member(user_to_uid([user])[0]))
                        except:
                            # this is an cfg.Error thing
                            updcells = None
                            actionneeded = "Manual Reset Required"
                        if updcells:
                            cells += updcells
                        if actionneeded:
                            try:
                                embeddict[actionneeded].append(user)
                            except:
                                embeddict.update({actionneeded : [user]})
                    else:
                        continue

                # updating the cells, I eventually decided to also do this in bulk, rather than doing it by person to save time in the api calls.
                rostersheets[1].update_cells(cells, value_input_option="USER_ENTERED")

            # creating log embed
            # this padding is a shitty attempt to make embeds look decent on PC.
            padding = " ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ ⠀ "
            embeds: list[Embed] = []
            embed = Embed(title="Quota Cycle Reset Statistics", description=f"Statistics from Quota Cycle: <t:{quota[division]['Cycle']['Start']}:d> - <t:{quota[division]['Cycle']['End']}:d>", color=cfg.embedcolors[division])
            embed.description += padding

            # get the most active member FIXED NOW
            try:
                most = embeddict["Complete"][0]
                for i in embeddict["Complete"]:
                    userinfo = rosters[index].members[i]
                    if float(rosters[index].members[most]["Minutes"]) < float(userinfo["Minutes"]):
                        most = i
                try:
                    embed.add_field(name="Most Active User", value=intact.guild.get_member(user_to_uid([most])[0]).mention)
                except:
                    embed.add_field(name="Most Active User", value=most)
                embed.add_field(name="⠀", value="⠀")
                embed.add_field(name="⠀", value="⠀")
                embeds.append(embed)
            except:
                None

            # pre defined promotion embed, it's getting added to the embeds list at the end so it's at the bottom
            promotionembed = Embed(title="Due For Promotion", description=f"{padding}", color=cfg.embedcolors[division])

            # for each action, run through it, add a field per person, if you hit 25 people, start a new embed, clever logic here for that hard limit.
            for x in embeddict:
                # iterate over the people 25 at a time
                for jump in range(0, len(embeddict[x]), 25):
                    if x != "Due For Promotion": # promotion already defined
                        embed = Embed(title=x, color=cfg.embedcolors[division])
                        embed.description = f"{padding}"

                    # iterate over each person in the batch of 25, if it hits the end it'll raise an index out of range cfg.Error, signaling the end of this action list
                    for i in range(jump, jump+25):
                        try:
                            user = embeddict[x][i]
                            userinfo = rosters[index].members[user]
                            if x == "Due For Promotion": # promotion was predefined
                                try: # tries to do discord mention for easy of role changes
                                    user = intact.guild.get_member(user_to_uid([user])[0])
                                    promotionembed.add_field(name=user, value=user.mention)
                                    # attempt to send a DM to the user due for promotion.
                                    await send_dm(user, content="Congratulations! You have been automatically put up for promotion to the next rank in Main Force!" \
                                    " The Main Force officers have been notified of this and you should recieve a promotion within the next day." \
                                    " If you do not recieve the promotion, contact any officer.")
                                except:
                                    promotionembed.add_field(name=user, value="@user?!")
                            else:
                                try:
                                    points[user]
                                    embed.add_field(name=user, value=f"Minutes: {userinfo['Minutes']}\nEvents: {userinfo['Events']}\nPoints: {points[user]}")
                                except:
                                    embed.add_field(name=user, value=f"Minutes: {userinfo['Minutes']}\nEvents: {userinfo['Events']}")
                        except:
                            if (i-1)%3:
                                for j in range((i-1)%3, 3):
                                    embed.add_field(name="⠀", value="⠀")
                            break
                    embeds.append(embed)
                    embed = False

            if len(promotionembed.fields) > 0:
                embeds.append(promotionembed)
            # doing pages nums
            pages = len(embeds)
            
            for i in range(1, pages+1):
                embeds[i-1].set_footer(text=f"{i}/{pages}")
                
            # send out logs
            auditembed = Embed(title=f"Quota Reset Performed on Roster {division}", description=f"**Performed By:** {intact.user.mention}", color=cfg.embedcolors[division])
            await intact.edit_original_response(content="Done!", view=None)

            # if there are too many embeds, this splits them up in groups of 10 to send to the statistics channel
            if len(embeds) > 10:
                for i in range(0, len(embeds), 10):
                    temp = []
                    for z in range(i, i+10):
                        try:
                            temp.append(embeds[z])
                        except:
                            break
                    for x in channel_id:
                        await intact.guild.get_channel(x).send(embeds=temp)
                    if division == "Nothing To See Here":
                        # NTSH has quota logs get sent to the interstate server.
                        await tree.client.get_guild(1321681628828925962).get_channel(1407055533772374097).send(embeds=temp)
            else:
                for x in channel_id:
                    await intact.guild.get_channel(x).send(embeds=embeds)
                if division == "Nothing To See Here":
                    # NTSH has quota logs get sent to the interstate server.
                    await tree.client.get_guild(1321681628828925962).get_channel(1407055533772374097).send(embeds=embeds)
            
            # send logs
            await intact.guild.get_channel(cfg.logchannel_ids[division]).send(embed=auditembed.set_author(name=f"{comuser}"))
            await tree.client.get_guild(588427075283714049).get_channel(588438540090736657).send(embed=auditembed)

            # adjust cycle times to the next cycle and save them
            quota[division]['Cycle']['Start'] += quota[division]['Cycle']['Interval']
            quota[division]['Cycle']['End'] += quota[division]['Cycle']['Interval']
            with open(get_local_path("data\\quota.json"), "w") as f:
                json.dump(quota, f, indent=2)
                f.close()
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Quota {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Quota {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

    print(f"{cfg.logstamp()}[Setup]{cfg.Success} Quota command group setup complete")
