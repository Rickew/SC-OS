from roblox.partials.partialuser import RequestedUsernamePartialUser as RequestedUsernamePartialUser
from discord import app_commands, Member, Interaction, Embed, User, Message, ButtonStyle, ui
from python.helpers import exportSheetData, discord_to_username
from traceback import format_exc
from datetime import datetime
import data.config as cfg
from gspread import Cell
from requests import get
import inspect
import roblox
import re

class YesorNo(ui.View):
    no: bool = False
    yes: bool = False
    @ui.button(label="Yes",style=ButtonStyle.success)
    async def button1(self, interaction: Interaction, button: ui.Button):
        self.yes = True
        self.stop()
        await interaction.response.defer()
    @ui.button(label="No",style=ButtonStyle.red)
    async def button2(self, interaction: Interaction, button: ui.Button):
        self.no = True
        await interaction.response.defer()
        self.stop()

COMMAND_NAME = "hit"

GUILD_IDS = [
    751538726647103489
]


def parseStatus(status):
    if status:
        if not status in ["Complete", "Incomplete", "In Progress", "Revoked"]:
            raise
        if status == "Complete":
            status = f"{status} :green_square:"
        elif status == "Incomplete":
            status = f"{status} :red_square:"
        elif status == "In Progress":
            status = f"{status} :orange_square:"
        elif status == "Revoked":
            status = f"{status} :prohibited:"
    return status

def CreateHitLogEmbed(discuser: User | Member, hitlink: str, authorization: str,
        rblxuser: RequestedUsernamePartialUser | roblox.users.User, usrlink: str, num: str, reason: str,
        bounty: str, expiration: str, color: str, style: str):
    logembed = Embed(title="Hit Authorized and Placed", description=f"**Hit sent by**: <@!{discuser.id}>", color=color, url=hitlink)
    logembed.add_field(name="Hit Authorized By",value=authorization, inline=True)
    logembed.add_field(name="Hit Placed On", value=f"[{rblxuser.name}]({usrlink})", inline=True)
    logembed.add_field(name="Hit Reason", value=reason, inline=True)
    logembed.add_field(name="Hit Amount", value=num, inline=True)
    logembed.add_field(name="Style", value=style, inline=True)
    logembed.add_field(name="Bounty", value=bounty, inline=True)
    logembed.add_field(name="Expires", value=expiration, inline=True)
    return logembed

def creatHitEmbed(rblxuser: RequestedUsernamePartialUser | roblox.BaseUser, usrlink: str, reason: str, 
        num: str, authorization: str, bounty: str, expiration: str,  color: int, style: str):
    usrimg = cfg.rbximgurl.replace("{uid}", str(rblxuser.id))
    usrimg = get(usrimg).content.decode().split("\",\"")[1].split(":\"")[1]
    hitembed = Embed(title=f"{rblxuser.name}", description=f"", color=color, url=usrlink)
    hitembed.add_field(name="Hit Reason", value=reason, inline=False)
    hitembed.add_field(name="Hit Amount", value=num, inline=True)
    hitembed.add_field(name="Style", value=style, inline=True)
    hitembed.add_field(name="⠀", value="⠀", inline=True)
    hitembed.add_field(name="Bounty", value=bounty, inline=False)
    hitembed.add_field(name="Hit Status", value="Incomplete :red_square:", inline=False)
    hitembed.add_field(name="Expires", value=expiration, inline=False)
    hitembed.set_footer(text=f"Authorized by {authorization}", icon_url=cfg.ntsh_logo)
    hitembed.set_thumbnail(url=usrimg)
    return hitembed

def parseExpiration(expiration: str):
    if "never" in expiration.lower():
        return "Never"
    if not re.fullmatch(r'^(?!(.*([wmdy]).*\2))(\d{1,4}[wmdy])*$', expiration.lower()):
        return None
    try: 
        timestamp = int(datetime.now().timestamp())
    except:
        None
    try:
        timestamp += int(re.findall("\\d+[y]", expiration.lower())[0].strip("y")) * 31536000
    except:
        None
    try:
        timestamp += int(re.findall("\\d+[m]", expiration.lower())[0].strip("m")) * 2592000
    except:
        None
    try:
        timestamp += int(re.findall("\\d+[w]", expiration.lower())[0].strip("w")) * 604800
    except:
        None
    try:
        timestamp += int(re.findall("\\d+[d]", expiration.lower())[0].strip("d")) * 86400
    except:
        None
    return f"<t:{timestamp}:F> <t:{timestamp}:R>"

async def sendhit(intact: Interaction, user: str, num: str, reason: str, bounty: str, style: app_commands.Choice[int] = None, expiration: str = "1w", ping: bool = False, authorization: str = None, run = False):
        print(f"{cfg.logstamp()}[Hit send] command ran by {intact.user} in {intact.guild.name}")
        if not run:
            await intact.response.defer(thinking=True, ephemeral=True)
        try:
            comuser = discord_to_username([str(intact.user.id)])[0]
            roster = exportSheetData()[1][1]
            color = cfg.embedcolors["Nothing To See Here"]
        except:
            print("Error in comuser")
            try:
                rblxusername = await roblox.Client.get_user(roblox.Client(), get(f"{cfg.disctorblx[0]}"
                    f"{intact.guild_id}{cfg.disctorblx[1]}{intact.user.id}", 
                    headers={"Authorization" : cfg.bloxlinkkeys[str(intact.guild_id)]}).json()['robloxID'])
            except:
                if not run:
                    await intact.followup.send(content="You must verify your account with bloxlink!", ephemeral=True)
                return
            comuser = rblxusername.name
            color = cfg.embedcolors["Other"]
        content = None
        if authorization == None:
            authorization = comuser
        try:
            client = roblox.Client()
            rblxuser = await client.get_user_by_username(user)
            usrlink = f"https://www.roblox.com/users/{rblxuser.id}/profile"
        except:
            if not run:
                await intact.followup.send("Roblox user does not exist, hit not sent.", ephemeral=True)
            else:
                print("Roblox User Doesn't Exist")
                return
        expiration = parseExpiration(expiration)
        if not style:
            style = "Normal"
        else:
            style = style.name
        hitembed = creatHitEmbed(rblxuser, usrlink, reason, num, authorization, bounty, expiration, color, style)
        if ping:
            content = f"{intact.guild.get_role(751538726647103493).mention} {intact.guild.get_role(751538726647103493).mention}"
        hitchannel = intact.guild.get_channel(1328547186006425773)
        hitlink = await hitchannel.create_thread(name=user,content=content,embed=hitembed,
                    applied_tags=[hitchannel.available_tags[0]],auto_archive_duration=10080)
        hitlink = hitlink.thread.starter_message.jump_url
        if not run:
            logembed = CreateHitLogEmbed(intact.user, hitlink, authorization, rblxuser, usrlink, num, reason, bounty, expiration, color, style)
            await intact.guild.get_channel(1328990510328709160).send(embed=logembed)
            await intact.followup.send("Done!", ephemeral=True)
        return

async def honorshophit(intact: Interaction, user: str, num: str, customer: str, bounty: str):
    expiration: str = "1w"
    authorization: str = "Honor Shop"
    reason: str = f"Honor Shop ({customer})"
    style: str = "Normal"
    hitchannel = intact.guild.get_channel(1328547186006425773)
    hitthread = None
    for thread in hitchannel.threads:
        try:
            if ("Incomplete" in thread.applied_tags[0].name or "In Progress" in thread.applied_tags[0].name) and thread.name.lower() == user.lower():
                message: Message = [message async for message in thread.history(limit=1, oldest_first=True)][0]
                if "Honor Shop" in message.embeds[0].fields[0].value:
                    hitthread = True
                    break
        except:
            continue
    if hitthread:
        try:
            hitembed = message.embeds[0].to_dict()
            if customer not in hitembed['fields'][0]['value']:
                hitembed['fields'][0]['value'] = f"{hitembed['fields'][0]['value'].strip(')')} & {customer})"
            if "/" in hitembed['fields'][1]['value']:
                try:
                    if hitembed['fields'][1]['value'][3]:
                        hitembed['fields'][1]['value'] = f"{hitembed['fields'][1]['value'][0]}/3"
                except:
                    None
                try:
                    if int(hitembed['fields'][1]['value'][2]) + num <= 3:
                        hitembed['fields'][1]['value'] = f"{hitembed['fields'][1]['value'][0]}/{int(hitembed['fields'][1]['value'][2]) + num}"

                except:
                    hitembed['fields'][1]['value'] = num+1

            else:
                if int(hitembed['fields'][1]['value']) + num <= 3:
                    hitembed['fields'][1]['value'] = int(hitembed['fields'][1]['value']) + num
            x = await message.edit(embed=Embed.from_dict(hitembed))
        except:
            None
    else:
        await sendhit(intact, user, num, reason, bounty, run=True, authorization=authorization)


def setup(tree: app_commands.CommandTree):
    # NTSH Hit command group
    hit = app_commands.Group(name="hit", description="Hit Management", guild_ids=GUILD_IDS, guild_only=True)
    tree.add_command(hit)

    @hit.command(name="send", description="Place a hit on someone.")
    @app_commands.describe(num="How many hits?")
    @app_commands.describe(ping="Send a ping?")
    @app_commands.describe(authorization="If someone else authorized this hit put their username.")
    @app_commands.describe(bounty="Specify how much honor is earned per kill on the target.")
    @app_commands.describe(expiration="Format for time: \"Never\" or \"#y#m#w#d\"")
    @app_commands.describe(style="Normal or Execution")
    @app_commands.choices(style=[app_commands.Choice(name="Normal", value=1), app_commands.Choice(name="Execution", value=2)])
    async def send(intact: Interaction, user: str, num: str, reason: str, bounty: str, style: app_commands.Choice[int] = None, expiration: str = "1w", ping: bool = False, authorization: str = None):
        try:
            await sendhit(intact, user, num, reason, bounty, style, expiration, ping, authorization)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Hit {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Hit {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    


    @hit.command(name="update", description= "Make any changes you need to an active hit.")
    @app_commands.describe(targetname="Name of the hit target.")
    @app_commands.describe(newname="Change the hit target.")
    @app_commands.describe(reason="Update the reason.")
    @app_commands.describe(amount="Input the \"x/x\" of hits completed or just a number (xx) all other input will be rejected.")
    @app_commands.describe(style="Update the style of the hit")
    @app_commands.describe(bounty="Change the amount of honor an NTSH will recieve for completing this hit.")
    @app_commands.describe(status="Update the status of the hit.")
    @app_commands.describe(expiration="Change the expiration date of the hit.")
    @app_commands.describe(authorization="Change who authorized the hit.")
    @app_commands.choices(style=[
        app_commands.Choice(name="Normal", value=1),
        app_commands.Choice(name="Execution", value=2)])
    @app_commands.choices(status=[
        app_commands.Choice(name="Incomplete", value=1),
        app_commands.Choice(name="In Progress", value=2),
        app_commands.Choice(name="Complete", value=3),
        app_commands.Choice(name="Revoked", value=4)])
    async def update(intact: Interaction, targetname: str = None, newname: str = None, reason: str = None, amount: str = None, style: app_commands.Choice[int] = None, bounty: str = None, expiration: str = None, status: app_commands.Choice[int] = None, authorization: str = None):
        try:
            print(f"{cfg.logstamp()}[Hit update] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(ephemeral=True,thinking=True)
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
                color = cfg.embedcolors["Nothing To See Here"]
            except:
                try:
                    rblxusername = await roblox.Client.get_user(roblox.Client(), get(f"{cfg.disctorblx[0]}"
                        f"{intact.guild_id}{cfg.disctorblx[1]}{intact.user.id}", 
                        headers={"Authorization" : cfg.bloxlinkkeys[str(intact.guild_id)]}).json()['robloxID'])
                except:
                    await intact.followup.send(content="You must verify your account with bloxlink!", ephemeral=True)
                    return
                comuser = rblxusername.name
                color = cfg.embedcolors["Other"]
            message = None
            hitchannel = intact.guild.get_channel(1328547186006425773)
            try:
                if not targetname and intact.channel.parent.id == hitchannel.id or targetname.lower() == intact.channel.name.lower():
                    message: Message = [message async for message in intact.channel.history(limit=1, oldest_first=True)][0]
                    targetname = message.thread.name
                else:
                    for thread in hitchannel.threads:
                        if thread.name.lower() == targetname.lower():
                            message: Message = [message async for message in thread.history(limit=1, oldest_first=True)][0]
                            break
            except:
                try:
                    await intact.followup.send(content="No hit target specified.", ephemeral=True)
                except:
                    await intact.followup.send(content="No hit target specified.", ephemeral=True)
                return
            if not message:
                try:
                    await intact.followup.send(content="There is no active hit on that target.", ephemeral=True)
                except:
                    await intact.followup.send(content="There is no active hit on that target.", ephemeral=True)
                return
            elif not (newname or status or amount or reason or authorization or bounty or expiration):
                try:
                    await intact.followup.send(content="Hit unchanged :thumbsup:", ephemeral=True)
                except:
                    await intact.followup.send(content="Hit unchanged :thumbsup:", ephemeral=True)
                return
            elif message.thread.locked:
                try:
                    await intact.followup.send(content="This hit is no longer editable.", ephemeral=True)
                except:
                    await intact.followup.send(content="This hit is no longer editable.", ephemeral=True)
                try:
                    await message.thread.edit(archived=True)
                except:
                    await message.thread.edit(archived=True)
                return
            updatedEmbed = message.embeds[0].to_dict()
            if newname:
                try:
                    client = roblox.Client()
                    rblxuser = await client.get_user_by_username(newname)
                    usrlink = f"https://www.roblox.com/users/{rblxuser.id}/profile"
                    usrimg = cfg.rbximgurl.replace("{uid}", str(rblxuser.id))
                    usrimg = get(usrimg).content.decode().split("\",\"")[1].split(":\"")[1]
                    logembed = Embed(title=f"Hit Changed", description=f"**Hit Modified by**: <@!{intact.user.id}>", color=color, url=message.jump_url)
                    logembed.add_field(name="Hit Target", value=f"Was: {updatedEmbed['title']}\nNow: {rblxuser.name}", inline=True)
                    updatedEmbed["title"] = rblxuser.name
                    updatedEmbed["url"] = usrlink
                    updatedEmbed["thumbnail"]["url"] = usrimg
                    updatedEmbed["thumbnail"]["proxy_url"] = ""
                    await message.thread.edit(name=rblxuser.name)
                except:
                    try:
                        await intact.followup.send(content="Roblox user does not exist, hit not sent.",ephemeral=True)
                    except:
                        await intact.followup.send(content="Roblox user does not exist, hit not sent.",ephemeral=True)
                    return
            if not newname:
                logembed = Embed(title=f"Hit on {targetname} Modified", description=f"**Hit Modified by**: {comuser} <@!{intact.user.id}>", color=color, url=message.jump_url)
            if reason:
                logembed.add_field(name="Hit Reason", value=f"Was: {updatedEmbed['fields'][0]['value']}\nNow: {reason}", inline=True)
                updatedEmbed['fields'][0]['value'] = reason
            if amount:
                if re.findall(r'\d+/\d+', amount) or re.findall(r'\d+', amount):
                    logembed.add_field(name="Hit Amount", value=f"Was: {updatedEmbed['fields'][1]['value']}\nNow: {amount}", inline=True)
                    updatedEmbed['fields'][1]['value'] = amount
            if style:
                style = style.name
                logembed.add_field(name="Style", value=f"Was: {updatedEmbed['fields'][2]['value']}\nNow: {style}", inline=True)
                updatedEmbed['fields'][2]['value'] = style
            if bounty:
                logembed.add_field(name="Bounty", value=f"Was: {updatedEmbed['fields'][4]['value']}\nNow: {bounty}", inline=True)
                updatedEmbed['fields'][4]['value'] = bounty
            if status:
                status = status.name
                try:
                    oldstatus = updatedEmbed['fields'][5]['value']
                    status = parseStatus(status)
                    updatedEmbed['fields'][5]['value'] = status
                    logembed.add_field(name="Hit Status", value=f"Was: {oldstatus}\nNow: {status}", inline=True)
                    try:
                        await message.thread.remove_tags(hitchannel.available_tags[cfg.hittag[oldstatus.split(" :")[0].lower()]])
                    except:
                        await message.thread.remove_tags(hitchannel.available_tags[cfg.hittag[oldstatus.split(" :")[0].lower()]])
                    try:
                        await message.thread.add_tags(hitchannel.available_tags[cfg.hittag[status.split(" :")[0].lower()]])
                    except:
                        await message.thread.add_tags(hitchannel.available_tags[cfg.hittag[status.split(" :")[0].lower()]])
                except Exception as e:
                    print(e)
                    try:
                        await intact.followup.send(content="Cannot update hit with that value.", ephemeral=True)
                    except:
                        await intact.followup.send(content="Cannot update hit with that value.", ephemeral=True)
                    return
            if expiration:
                expiration = parseExpiration(expiration)
                logembed.add_field(name="Expiration", value=f"Was: {updatedEmbed['fields'][6]['value']}\nNow: {expiration}", inline=False)
                updatedEmbed['fields'][6]['value'] = expiration
            if authorization:
                logembed.add_field(name="Authorization", value=f"Was: {updatedEmbed['footer']['text'].strip('Authorized by ')}\nNow: {authorization}", inline=True)
                logembed.set_author(name=f"{comuser}")
                updatedEmbed['footer']['text'] = f"Authorized by {authorization}"
            logchannel = intact.guild.get_channel(1328990510328709160)
            try:
                await message.edit(embed=Embed.from_dict(updatedEmbed))
            except:
                await message.edit(embed=Embed.from_dict(updatedEmbed))
            try:
                await logchannel.send(embed=logembed)
            except:
                await logchannel.send(embed=logembed)
            await intact.followup.send(content=f"The hit has been modified.", ephemeral=True)
            if status in ["Complete :green_square:", "Revoked :prohibited:"]:
                try:
                    await message.thread.edit(locked=True, archived=True)
                except:
                    await message.thread.edit(locked=True, archived=True)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][NTSH Hit{inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[NTSH Hit {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    


    @hit.command(name="delete", description= "Deletes specified hit.")
    async def delete(intact: Interaction):
        try:
            print(f"{cfg.logstamp()}[Hit delete] command ran by {intact.user} in {intact.guild.name}")
            hitchannel = intact.guild.get_channel(1328547186006425773)
            try:
                if intact.channel.parent != hitchannel:
                    await intact.response.send_message("Hit not specified.", ephemeral=True)
                    return
            except:
                await intact.response.send_message("Hit not specified.", ephemeral=True)
                return
            view = YesorNo()
            await intact.response.send_message(content="Are you sure you want to delete this hit?",view=view, ephemeral=True)
            await view.wait()
            if view.yes:
                message: Message = [message async for message in intact.channel.history(limit=1, oldest_first=True)][0]
                hit = message.embeds[0].to_dict()
                logembed = Embed(title=f"Hit on {hit['title']} Deleted", description=f"**Deleted by:** {intact.user.mention}", url=hit["url"])
                logembed.add_field(name="Hit Authorized By", value=f"{hit['footer']['text'].strip('Authorized By')}")
                for field in hit["fields"]:
                    if field["name"] == "⠀":
                        continue
                    logembed.add_field(name=field["name"], value=field["value"], inline=True)
                await intact.guild.get_channel(1328990510328709160).send(embed=logembed)
                await intact.channel.delete()
                
            elif view.no:
                await intact.edit_original_response(content="Hit was not deleted.",view=None)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][NTSH Hit{inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[NTSH Hit {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    
    @hit.command(name="award", description="Award the bounty of a hit to a member.")
    @app_commands.describe(user="The user who is being awarded the hit bounty.")
    async def award(intact: Interaction, user: Member):
        try:
            print(f"{cfg.logstamp()}[Hit award] command ran by {intact.user} in {intact.guild.name}")
            hitchannel = intact.guild.get_channel(1328547186006425773)
            try:
                if intact.channel.parent != hitchannel:
                    await intact.response.send_message("This must be ran inside of a hit thread.", ephemeral=True)
                    return
            except:
                await intact.response.send_message("This must be ran inside of a hit thread.", ephemeral=True)
                return
            message: Message = [message async for message in intact.channel.history(limit=1, oldest_first=True)][0]
            try:
                bounty = int(message.embeds[0].fields[4].value)
            except:
                await intact.followup.send("Issue with bounty??")
                return
            rostersheets, rosters = exportSheetData()
            rostersheet = rostersheets[1]
            roster = rosters[1]
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
                color = cfg.embedcolors["Nothing To See Here"]
            except:
                try:
                    rblxusername = await roblox.Client.get_user(roblox.Client(), get(f"{cfg.disctorblx[0]}"
                        f"{intact.guild_id}{cfg.disctorblx[1]}{intact.user.id}", 
                        headers={"Authorization" : cfg.bloxlinkkeys[str(intact.guild_id)]}).json()['robloxID'])
                except:
                    await intact.followup.send(content="You must verify your account with bloxlink!", ephemeral=True)
                    return
                comuser = rblxusername.name
                color = cfg.embedcolors["Other"]
            try:
                usr = discord_to_username([str(user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="User UIDs are probably not synced.", color=color))
                return

            logembed = Embed(color=color, title=f"Hit Bounty Awarded To {usr} by {comuser}", description=f"Hit Bounty Awarded to {user.mention} by {intact.user.mention}")
            rostersheet.update_cells([Cell(roster.members[usr]["Row"], roster.collumns["Honor"], roster.members[usr]["Honor"]+bounty)], value_input_option="USER_ENTERED")
            logembed.add_field(name=f"Bounty", value=bounty)
            await intact.followup.send("Done!")
            await intact.channel.send(embed=logembed)
            await intact.guild.get_channel(1328990510328709160).send(embed=logembed)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][NTSH Hit{inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[NTSH Hit {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

    print(f"{cfg.logstamp()}[Setup]{cfg.Success} NTSH Hit command group setup complete")