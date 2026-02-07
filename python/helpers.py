from discord import Interaction, User, Embed, Member, Message
from gspread import Cell, Worksheet
from asyncio import run as asyncrun
from requests import get as reqget
from discord.ext import commands
import data.config as cfg
from roblox import Client
from datetime import datetime as dt
import json
import os
from requests import post as reqpost

# has roster sheet data in a class form for easier access to users and sheet data
class RosterSheet:
    def __init__(self, name: str, col: int, row: int, cells: list[cfg.gspread.Cell]):
        self.name = name
        self.collumns = col
        self.rows = row
        self.headers: dict[str,str] = {}
        self.members: dict[str,dict[str,str|int]] = {}
        for i in range(1,col):
            self.headers.update({cells[i].value : cells[i].col-1})
        
        for i in range(col, len(cells), col):
            if cells[i].value in ("", "-", "_") or "Most Active" in cells[i].value:
                continue
            try:
                self.members[cells[i].value]
            except:
                self.members.update({cells[i].value : {}})
                for key in self.headers.keys():
                    self.members[cells[i].value].update({key : cells[i+self.headers[key]].value})
                self.members[cells[i].value].update({"Row" : cells[i].row})
        for x in self.headers:
            self.headers[x] += 1

# gets the local path for this project, path will append to the end of the local path
def get_local_path(path: str = None) -> str:
    filedir = os.path.dirname(__file__) # gets the directory of the program
    filedir = filedir.replace("python","")
    if path.count("/"):
        path.replace("/", "\\")
    filedir += f"{path}"
    return filedir

# optionally exports roster data, return roster worksheets and RosterSheet objects in a var
def exportSheetData(exporttofile: bool = False) -> tuple[list[Worksheet], list[RosterSheet]]:
    rostersheets = [cfg.MFroster, cfg.TFDroster, cfg.NCOroster, cfg.COroster]
    rosters:list[RosterSheet] = []
    for sheet in rostersheets:
        rosters.append(RosterSheet(sheet.title, sheet.col_count, sheet.row_count, sheet.get_all_cells()))
    for roster in rosters:
        with open(get_local_path("data\\"+roster.name+".json"), "w") as f:
            json.dump(roster.members, f, indent=4)
            f.close()
    return rostersheets, rosters   

# this is supposed to shift the points 1 row up or 1 row dow for the addition or removal of a person, also works for promtiona, probably.
# lowkey this function is unstable.
def shift_point_rows(ranks: list[str], rank: str, ad:str):
    ncoranks = cfg.NCOroster.col_values(col=14)
    ncoranks.remove("Roster Ranks")
    coranks = cfg.COroster.col_values(col=19)
    coranks.remove("Roster Ranks")

    if ncoranks[-1] == rank or coranks[-1] == rank and ad == "Add":
        return
    elif rank in ncoranks:
        roster = cfg.NCOroster
        ranks = ncoranks
    elif rank in coranks:
        roster = cfg.COroster
        ranks = coranks
    else:
        return
    while True:
        try:
            ranks.remove('')
        except:
            break
    print(f"{ranks=}")
    rankcells: list[Cell] = []
    for i in range(0, len(ncoranks)-1):
        print(i, len(ncoranks))
        if ranks[i] == rank:
            for x in range(i+1, len(ranks)):
                print(x, ncoranks[x])
                rankcells += roster.findall(ranks[x],in_column=2)
    print(rankcells)
    tpcell = roster.find("Total Points")
    print(f"{tpcell=}")
    if ad == "Add":
        shiftrownum = rankcells[0].row
    else:
        shiftrownum = rankcells[-1].row
    print(shiftrownum)
    rownums = []
    updcells = []
    rowvals = []
    for cell in rankcells:
        if ad == "Add":
            rownums.append(cell.row+1)
        else:
            rownums.append(cell.row-1)
    print(f"{rownums=}")
    for i in rownums:
        if ad == "Add":
            rowvals.append(roster.row_values(i-1))
        else:
            rowvals.append(roster.row_values(i+1))
    print(f"{rowvals=}")
    for i in range(0, len(rownums)):
        for y in range(3, tpcell.col):
            updcells.append(Cell(rownums[i], y, rowvals[i][y-1]))
    for y in range(3, tpcell.col):
        updcells.append(Cell(shiftrownum, y, 0))
    roster.update_cells(updcells)

# the command for running rblx_disc_IDsync() since its an async function
def runIDsync(bot: commands.Bot):
    asyncrun(rblx_disc_IDsync(bot))

# sanitized the IDRoster based on if users are in the group or not, and if a discord ID is in the discord or not.
async def idrostersanitize(bot: commands.Bot = None, intact: Interaction = None):
    scgroup = await Client().get_group(4971973)
    members = scgroup.get_members()
    members = await members.flatten()
    if os.path.exists(get_local_path("data\\IDroster.json")):
    # load already logged users
        with open(get_local_path("data\\IDroster.json")) as f:
            users = json.load(f)
            f.close() 

        # This is a discrimpancy check for unlogging those who don't need to be logged.
        # aka users that are not in the roblox group are getting tossed out of the IDroster
        checkmems = []
        pop = []
        for mem in members:
            checkmems.append(mem.name)
        for user in users['rblxuser']:
            if user in checkmems:
                continue
            else:
                pop.append(user)
        for x in pop:
            if users["rblxuser"][x]["discID"] != 0:
                print(f"Removed Discord ID for {x}: {users['rblxuser'][x]['discID']} from ID Roster")
                users["discID"].pop(str(users["rblxuser"][x]["discID"]))
            print(f"Removed {x} from ID Roster.")
            users["rblxuser"].pop(x)
        if bot:
            discordmems = bot.get_guild(588427075283714049).members
        elif intact:
            discordmems = intact.client.get_guild(588427075283714049).members
        pop.clear()
        for mem in discordmems:
            checkmems.append(str(mem.id))
        for id in users["discID"].keys():
            if id in checkmems:
                continue
            else:
                pop.append(id)
        for x in pop:
            try:
                print(f"Removed {id} for user: {users['discID']['rblxuser']} from ID Roster.")
                users["discID"].pop(id)
            except:
                print("NAME CHANGE ISSUE PLEASE FIX THIS")
        with open(get_local_path("data\\IDroster.json"), "w") as f:
            json.dump(users, f, indent=2)
            f.close()
        return True
    else:
        return False

# makes or modifies the IDRoster
async def rblx_disc_IDsync(bot: commands.Bot):
    scgroup = await Client().get_group(4971973)
    members = scgroup.get_members()
    members = await members.flatten()

    if os.path.exists(get_local_path("data\\IDroster.json")):
        if await idrostersanitize(bot):
            print("Sanitization Completed")
        else:
            print("Sanitization Failed, how did you even get here?")

    # load already logged users
        with open(get_local_path("data\\IDroster.json")) as f:
            users = json.load(f)
            f.close() 
    
        # check discrempancy
        for mem in members:
            try:
                # Check if user is logged
                users["rblxuser"][mem.name]
            except:
                # if user isn't logged
                users["rblxuser"].update({mem.name : {'discID' : 0, 'rblxID' : mem.id}})
    else:
    # no IDroster around, gotta make it.
        users: dict[str,dict] = {"rblxuser" : {}, "discID": {}}
        for mem in members:
        # build out IDroster
            users["rblxuser"].update({mem.name : {"discID" : 0, "rblxID" : mem.id}})

    # no matter what, IDroster var needs some disc ID's if it doesn't have em.
    i = 0
    x = len(members)
    for mem in members:
        i+=1
        # check if discID is logged
        if users["rblxuser"][mem.name]["discID"] == 0:
            # handle discID not being logged
            # try to resolve discord ID from roblox uid
            r:dict = json.loads(reqget(f'https://api.blox.link/v4/public/guilds/588427075283714049/roblox-to-discord/{mem.id}', 
                    headers={"Authorization" : cfg.bloxlinkkeys["588427075283714049"]}).content.decode())
            # if error is recieved
            if "error" in r.keys():
                print(f"User {mem.name} Not In Discord Server or Not Verified With Bloxlink {i}/{x}.")
            # if no error, update IDroster var
            else:
                print(f"User {mem.name} is in Server {i}/{x}.")
                users["rblxuser"][mem.name]['discID'] = int(r["discordIDs"][0])
                users["discID"].update({r["discordIDs"][0] : {"rblxuser": mem.name, "rblxID" : mem.id}})
        else:
            print(f"User {mem.name} Already Logged {i}/{x}")

    with open(get_local_path("data\\IDroster.json"), "w") as f:
        json.dump(users, f, indent=2)
        f.close()
    print("ID Roster Checks build/checks complete.\n\n")

# takes a discord user ID and translates it to a roblox username from the ID Roster
# will error if user is not logged in the ID Roster
def discord_to_username(uids: list[str]) -> list[str]:
    with open(get_local_path("data\\IDroster.json"), "r") as f:
        users = json.load(f)
        f.close()
    ret = []
    for uid in uids:
        try:
            ret.append(users["discID"][uid]["rblxuser"])
        except:
            if len(uids) < 2:
                raise Exception("Error: Discord ID Unlinked")
            ret.append("Error: Discord ID Unlinked")
    return ret

# takes a discord user ID and translates it to a roblox username from the ID Roster
# will error if user is not logged in the ID Roster
def username_to_discord_id(usernames: list[str]) -> list[int]:
    with open(get_local_path("data\\IDroster.json"), "r") as f:
        users = json.load(f)
        f.close()
    ret = []
    for user in usernames:
        try:
            ret.append(int(users['rblxuser'][user]['discID']))
        except:
            if len(users) < 2:
                raise Exception("Error: Discord ID Unlinked")
            ret.append("Error: Discord ID Unlinked")
    return ret

# Single user UID Sync for ID Roster
# if the user it puts in is not in the roblox group it will sanitize them back off
# if the discord ID is not in the discord it will sanitize them back off aswell 
async def single_UID_sync(bot: commands.Bot, discID: int = None, rblxID: int = None, rblxuser : str = None):
    if discID:
        r:dict = json.loads(reqget(f'https://api.blox.link/v4/public/guilds/588427075283714049/discord-to-roblox/{discID}', 
            headers={"Authorization" : cfg.bloxlinkkeys["588427075283714049"]}).content.decode())
        if "error" in r.keys():
            raise "User is not verified with Bloxlink."
        rblxID = int(r["robloxID"])
        usr = await Client().get_user(rblxID)
        rblxuser = usr.name
    elif rblxID:
        r:dict = json.loads(reqget(f'https://api.blox.link/v4/public/guilds/588427075283714049/roblox-to-discord/{rblxID}', 
            headers={"Authorization" : cfg.bloxlinkkeys["588427075283714049"]}).content.decode())
        if "error" in r.keys():
            raise "User is not verified with Bloxlink."
        discID = int(r["discordIDs"][0])
        rblxuser = await Client().get_user(rblxID)
    elif rblxuser:
        usr = await Client().get_user_by_username(rblxuser)
        rblxID = usr.id
        r:dict = json.loads(reqget(f'https://api.blox.link/v4/public/guilds/588427075283714049/roblox-to-discord/{rblxID}', 
            headers={"Authorization" : cfg.bloxlinkkeys["588427075283714049"]}).content.decode())
        if "error" in r.keys():
            raise "User is not verified with Bloxlink."
        discID = int(r["discordIDs"][0])
    
    with open(get_local_path("data\\IDroster.json"), "r") as f:
        idRoster = json.load(f)
        f.close()
    idRoster["rblxuser"].update({rblxuser : {"discID" : discID, "rblxID" : rblxID}})
    idRoster["discID"].update({f"{discID}" : {"rblxuser" : rblxuser, "rblxID" : rblxID}})
    with open(get_local_path("data\\IDroster.json"), "w") as f:
        json.dump(idRoster, f, indent=2)
        f.close()
    return True

# get the quota string for automatic quota for each division and rank
def get_quota_string(div, rank) -> str:
    with open(get_local_path("data\\quota.json"), "r") as f:
        quota = json.load(f)
        f.close()
    if quota[div][rank]["Type"] == "Auto":
        string = cfg.quotastrings[div][quota[div][rank]["String"]].replace("{minutes}", str(quota[div][rank]["Time"])).replace("{events}", str(quota[div][rank]["Event"]))
        try:
            string = string.replace("{points}", quota[div][rank]["Points"])
        except:
            None
    else:
        string = None
    return string

# gets the rank of a Discord user from the Roster
# will error if user is not in ID Roster, or is user is not on the Roster 
def get_roster_rank(user: User) -> str:
    try:
        username = discord_to_username([str(user.id)])[0]
    except Exception as e:
        raise e
    rosters = exportSheetData()[1]
    try:
        return rosters[0].members[username]['Rank']
    except:
        try:
            return rosters[1].members[username]['Rank']
        except:
            raise Exception("User Not On Roster.")
        
# gets group rank number from SC group, input is roblox usernames
def get_scgroup_rank(users: list[str]) -> dict[dict[str,str|int]]:
    ranks = {}
    url = "https://groups.roblox.com/v1/users/{userId}/groups/roles"
    for usr in users:
        try:
            uid = reqpost(url="https://users.roblox.com/v1/usernames/users", json={"usernames" : [usr], "excludeBannedUsers" : True}).json()["data"][0]["id"]
            r = reqget(url=url.replace("{userId}", str(uid))).json()['data']
            for group in r:
                if group['group']['id'] == 4971973:
                    ranks.update({usr : {'rank' : group['role']['rank'], 'name' : group['role']['name']}})
            ranks[usr]
            print(ranks)
        except:
            ranks.update({usr : {'rank' : -1, 'name' : ''}})
    return ranks

def bgc_group_roles(users: list[str]):
    retembed = Embed(title="Groups & Ranks")
    url = "https://groups.roblox.com/v1/users/{userId}/groups/roles"
    url2 = "https://groups.roblox.com/v1/groups/{groupid}/roles"
    for usr in users:
        try:
            uid = reqpost(url="https://users.roblox.com/v1/usernames/users", json={"usernames" : [usr], "excludeBannedUsers" : True}).json()["data"][0]["id"]
            r = reqget(url=url.replace("{userId}", str(uid))).json()['data']
            for group in r:
                r = reqget(url=url2.replace("{userId}", str(group['id']))).json()['groupRoles'][0]
                if group['role']['rank'] == r['rank']:
                    retembed.add_field(name=f"{group['name']}\nMembers: `{group['memberCount']}`", value=f"{group['role']['name']}\n**Lowest Rank**")
                else:
                    retembed.add_field(name=f"{group['name']}", value=f"{r['name']}")
        except:
            return Embed(title="Error", description="Error getting groups.")
    return retembed

def get_ncgroup_rank(users: list[str]) -> dict[dict[str,str|int]]:
    ranks = {}
    url = "https://groups.roblox.com/v1/users/{userId}/groups/roles"
    for usr in users:
        try:
            uid = reqpost(url="https://users.roblox.com/v1/usernames/users", json={"usernames" : [usr], "excludeBannedUsers" : True}).json()["data"][0]["id"]
            r = reqget(url=url.replace("{userId}", str(uid))).json()['data']
            for group in r:
                if group['group']['id'] == 4965800:
                    ranks.update({usr : group['role']['name']})
            ranks[usr]
        except:
            ranks.update({usr : ''})
    return ranks

def remove_bottom_row(rostersheet: Worksheet, string: str) -> list[Cell]:
    cells = rostersheet.findall(string)
    if not cells:
        raise Exception(f"Couldn't find any cells with \"{string}\" in them.")
    if rostersheet.cell(cells[-1].row-1, 1).value in ("Most Active TFD Member", "Most Active Main Force"):
            cells.pop(-1)
    return cells

def trello_class_e_search(query):
    url = "https://api.trello.com/1/boards/E9nodzRk/cards"
    params = {
        "key": cfg.trelloapi[0],
        "token": cfg.trelloapi[2],
        "fields": "name,labels,url",
        "label_fields": "name,color"
    }
    r = reqget(
        url,
        params=params
    )
    cards = r.json()
    matches = []
    for card in cards:
        if query.lower() in card["name"].lower():
            matches.append({
                "name": card["name"],
                "approvals": [l["name"] for l in card["labels"]],
                "url": card["url"]
            })
    return matches

def rotector_check(uid):
    
    rotectorembed = Embed(title="Rotector Rating", url=f"https://rotector.com/")
    r = reqget(url=f"https://roscoe.rotector.com/v1/lookup/roblox/user/{uid}").json()
    print("Rotector Check:")
    if r['data']['flagType'] == 0:
        try:
            rotectorembed.set_footer(text=f"Last Updated: {dt.fromtimestamp(r['data']['lastUpdated']).strftime(r'%b %d, %Y')}")
            rotectorembed.add_field(name="Rotector Rating", value="Human Reviewed as Safe")
            rotectorembed.color = 0x29cc04
            print("Human Reviewed as Safe", "color=green", dt.fromtimestamp(r['data']['lastUpdated']).strftime(r'%b %d, %Y'))
        except:
            rotectorembed.add_field(name="Rotector Rating", value="Not Reviewed Yet")
            print("Not Reviewed yet", "color=grey")
    elif r['data']['flagType'] == 1:
        rotectorembed.set_footer(text=f"Last Updated: {dt.fromtimestamp(r['data']['lastUpdated']).strftime(r'%b %d, %Y')}")
        rotectorembed.add_field(name="Rotector Rating", value="AI Reviewed as Unsafe")
        rotectorembed.add_field(name="AI Cofidence", value=f"{(r['data']['confidence'])*100.0:.2f}%")
        rotectorembed.color = 0xde8304
        print("AI Reviewed as Unsafe", "AI Confidence:", f"{(r['data']['confidence'])*100.0:.2f}%", "color=orange", dt.fromtimestamp(r['data']['lastUpdated']).strftime(r'%b %d, %Y'))
    elif r['data']['flagType'] == 2:
        rotectorembed.set_footer(text=f"Last Updated: {dt.fromtimestamp(r['data']['lastUpdated']).strftime(r'%b %d, %Y')}")
        rotectorembed.add_field(name="Rotector Rating", value="Human Reviewed as Unsafe")
        rotectorembed.add_field(name="Cofidence", value=f"{(r['data']['confidence'])*100.0:.2f}%")
        rotectorembed.color = 0xed0202
        print("Human Reviewed as Unsafe", "Confidence:", f"{(r['data']['confidence'])*100.0:.2f}%", "color=orange", dt.fromtimestamp(r['data']['lastUpdated']).strftime(r'%b %d, %Y'))
    elif r['data']['flagType'] == 3:
        rotectorembed.set_footer(text=f"Last Updated: {dt.fromtimestamp(r['data']['processedAt']).strftime(r'%b %d, %Y')}")
        rotectorembed.add_field(name="Rotector Rating", value="AI Reviewed as Safe")
        rotectorembed.color = 0x02b0bd
        print("AI Reviewed as Safe", "color=skyblue", dt.fromtimestamp(r['data']['processedAt']).strftime(r'%b %d, %Y'))
    else:
        rotectorembed.description = f"Error Occured with Rotector Rating"
    return rotectorembed

# send a dm to the user, if a message is specified to be forwarded, then it'll be send after the initial message.
async def send_dm(user: User | Member, forward: Message = None, **kwargs):
    try:
        try:
            await user.dm_channel.send(**kwargs)
        except:
            try:
                await user.create_dm()
                await user.dm_channel.send(**kwargs)
            except:
                return False
        if forward:
            try:
                await forward.forward(user.dm_channel)
            except:
                await user.create_dm()
                await forward.forward(user.dm_channel)
        return True
    except:
        return False

