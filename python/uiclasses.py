from python.helpers import exportSheetData, discord_to_username, get_scgroup_rank, username_to_discord_id, RosterSheet, send_dm, get_ncgroup_rank
from python.commands.ntshhitsuite import honorshophit
from googleapiclient import discovery
from traceback import format_exc
from gspread import Worksheet
import data.config as cfg
from re import findall
import inspect
import discord
import json


class InactivityNotice(discord.ui.Modal):
    date = discord.ui.TextInput(label="Enter an End Date", style=discord.TextStyle.short, placeholder="mm/dd/yyyy")
    reason = discord.ui.TextInput(label="Enter a Reason", style=discord.TextStyle.long, placeholder="mm/dd/yyyy")
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.proceed = True
        self.stop()

class CancelorBack(discord.ui.View):
    cancel: bool = False
    back: bool = False
    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.red)
    async def cancelme(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancel = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Go Back",style=discord.ButtonStyle.gray)
    async def goback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.back = True
        await interaction.response.defer()
        self.stop()

class YesorNo(discord.ui.View):
    no: bool = False
    yes: bool = False
    @discord.ui.button(label="Yes",style=discord.ButtonStyle.success)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.yes = True
        self.stop()
        await interaction.response.defer()
    @discord.ui.button(label="No",style=discord.ButtonStyle.red)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.no = True
        await interaction.response.defer()
        self.stop()

class CancelButton(discord.ui.View):
    cancel: bool = False
    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.red)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancel = True
        await interaction.response.defer()
        self.stop()

class QuotaEdit(discord.ui.View):
    def __init__(self, *, timeout = 180, save: bool = False):
        super().__init__(timeout=timeout)
        self.savebutton.disabled = (not save)
    save: bool = False
    cancel: bool = False
    cycletime: bool = False
    rankquota: bool = False
    divquota: bool = False
    @discord.ui.button(label="Cycle/Time",style=discord.ButtonStyle.secondary, row=0)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cycletime = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Rank Quota",style=discord.ButtonStyle.blurple, row=0)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.rankquota = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Division Wide Quota",style=discord.ButtonStyle.gray, row=1)
    async def button3(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.divquota= True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.red, row=2)
    async def cancelbutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancel = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Save",style=discord.ButtonStyle.success, row=2, disabled=True)
    async def savebutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.save = True
        await interaction.response.defer()
        self.stop()

class NotesModal(discord.ui.Modal):
    proceed = False
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.proceed = True
        self.stop()

class BasicModal(discord.ui.Modal):
    submition = discord.ui.TextInput(label="Enter a Responce",style=discord.TextStyle.short)
    proceed = False
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.proceed = True
        self.stop()

class HitModal(discord.ui.Modal):
    target = discord.ui.TextInput(label="Enter a Username",style=discord.TextStyle.short)
    proceed = False
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.proceed = True
        self.stop()

class RankQuotaEdit(discord.ui.View):
    def __init__(self, *, timeout = 180, quota, points = False, save: bool = False):
        self.type = quota["Type"]
        if str(quota["Event"]) == "Mixed" or quota["Event"] == 99:
            andor = (True, True)
        elif "1" in quota["String"]:
            andor = (True, False)
        elif "2" in quota["String"]:
            andor = (False, True)
        else:
            andor = (False, False)
        super().__init__(timeout=timeout)
        self.points.disabled = (not points)
        self.button4.disabled = andor[0]
        self.button5.disabled = andor[1]
        self.savebutton.disabled = (not save)

    save: bool = False
    type: str = None
    cancel: bool = False
    back: bool = False
    selection: str = None
    userenteredvalue: int = None
    @discord.ui.button(label="Minutes",style=discord.ButtonStyle.blurple, row=0)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Time"
        modal = BasicModal(title="Enter time in Minutes (Enter 0 to Disable)")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.userenteredvalue = modal.submition.value
        self.stop()
    @discord.ui.button(label="Events",style=discord.ButtonStyle.success, row=0)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Event"
        modal = BasicModal(title="Enter number of events (Enter 0 to Disable)")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.userenteredvalue = modal.submition.value
        self.stop()
    @discord.ui.button(label="Points",style=discord.ButtonStyle.green, row=0)
    async def points(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Points"
        modal = BasicModal(title="Enter number of Points (Enter 0 to Disable)")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.userenteredvalue = modal.submition.value
        self.stop()
        self.stop()
    @discord.ui.button(label="Either",style=discord.ButtonStyle.green, row=1)
    async def button4(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "String"
        self.userenteredvalue = "1"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Both",style=discord.ButtonStyle.green, row=1)
    async def button5(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "String"
        self.userenteredvalue = "2"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Type",style=discord.ButtonStyle.secondary, row=1)
    async def button3(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Type"
        if self.type == "Auto":
            self.userenteredvalue = "Manual"
        else:
            self.userenteredvalue = "Auto"
        await interaction.response.defer()
    @discord.ui.button(label="Back",style=discord.ButtonStyle.secondary, row=2)
    async def backbutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.back = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.red, row=2)
    async def cancelbutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancel = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Save",style=discord.ButtonStyle.success, row=2, disabled=True)
    async def savebutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.save = True
        await interaction.response.defer()
        self.stop()

class CycleEdit(discord.ui.View):
    def __init__(self, *, timeout = 180, quota, points: bool = False, save: bool = False):
        if quota['Interval'] == 604800:
            intbool = (True, False)
        elif quota['Interval'] == 1209600:
            intbool = (False, True)
        super().__init__(timeout=timeout)
        self.button2.disabled = intbool[0]
        self.button3.disabled = intbool[1]
        self.savebutton.disabled = (not save)
        if points:
            if quota["Points"]:
                self.co.style = discord.ButtonStyle.red
        else:
            self.co.disabled = True
        self.points = quota["Points"]

    points: bool = None
    ncopoints: bool = None
    save: bool = False
    type: str = None
    cancel: bool = False
    back: bool = False
    selection: str = None
    userenteredvalue: int = None
    @discord.ui.button(label="Fix Cylce Time",style=discord.ButtonStyle.danger, row=0)
    async def button1(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Fix"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Weekly",style=discord.ButtonStyle.green, row=0)
    async def button2(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Interval"
        self.userenteredvalue = 604800
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Bi-Weekly",style=discord.ButtonStyle.green, row=0)
    async def button3(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Interval"
        self.userenteredvalue = 1209600
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Points",style=discord.ButtonStyle.green, row=1)
    async def co(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Points"
        self.userenteredvalue = not self.points
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Add/Sub NCO/CO Rank",style=discord.ButtonStyle.gray, row=1)
    async def addsubrank(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "addsubrank"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Back",style=discord.ButtonStyle.secondary, row=2)
    async def backbutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.back = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.red, row=2)
    async def cancelbutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancel = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Save",style=discord.ButtonStyle.success, row=2, disabled=True)
    async def savebutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.save = True
        await interaction.response.defer()
        self.stop()

class RosterRankSelect(discord.ui.Select):
    selected = False
    selection = None
    def __init__(self, sheetnum: int, row: int, col: int, ranklock: str, div: str):
        self.sheetrow = row
        self.col = col
        sheet = cfg.roster.get_worksheet(sheetnum)
        service = discovery.build("sheets", "v4", credentials=cfg.creds)
        request = service.spreadsheets().get(spreadsheetId=cfg.spreadsheet_id, ranges=sheet.title, fields="sheets(data(rowData(values(dataValidation))))")
        resp = request.execute()
        options = []
        lockout = False
        if ranklock and div != "Main Force":
            lockout = True
        with open(f"data\\ranklist{sheetnum}.json", "w") as f:
            json.dump(resp, f, indent=2)
            f.close()
        for x in resp['sheets'][0]['data'][0]['rowData'][cfg.ranknums[div]]['values'][col-1]['dataValidation']['condition']['values']:
            try:
                if str(x['userEnteredValue']) == ranklock and div == "Main Force":
                    lockout = True
                    continue
                elif str(x['userEnteredValue']) == ranklock:
                    lockout = False
                    continue
                elif lockout:
                    continue
            except:
                None
            options.append(discord.SelectOption(label= str(x['userEnteredValue'])))
        super(RosterRankSelect, self).__init__(options=options, placeholder="Select A Rank")
    
    async def callback(self, interaction: discord.Interaction):
        self.selection = self.values[0]
        await interaction.response.defer()
        self.selected = True
        return

class ApproveDenyHit(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Approve",style=discord.ButtonStyle.green, custom_id="honorshop:hitapprove")
    async def appr(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            print(f"{interaction.user} pressed a honor shop hit approve button")
            try:
                purchase = interaction.message.embeds[0].fields[0].value
                customer = interaction.message.embeds[0].fields[1].value
                bounty = interaction.message.embeds[0].fields[2].value
                target = interaction.message.embeds[0].fields[3].value
                await interaction.guild.get_channel(1328990510328709160).send(embed=discord.Embed(title="Honor Shop Hit Approved", description=f"Purchase Approved by {interaction.user.mention}", url=interaction.message.jump_url).add_field(name="Purchase", value=purchase, inline=False).add_field(name="Target", value=target).add_field(name="Customer", value=customer, inline=False))
                await interaction.message.edit(view=None, embed=interaction.message.embeds[0].add_field(name="Fulfilled By", value=interaction.user.mention, inline=False))
                await honorshophit(interaction, target, 1, customer, bounty)
            except:
                return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await interaction.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=discord.Embed(title=f"[Error][{__class__.__name__}][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[{__class__.__name__}][{inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    @discord.ui.button(label="Deny",style=discord.ButtonStyle.red, custom_id="honorshop:hitdeny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            print(f"{interaction.user} pressed a honor shop hit deny button")
            try:
                purchase = interaction.message.embeds[0].fields[0].value
                customer = interaction.message.embeds[0].fields[1].value
                await interaction.guild.get_channel(1328990510328709160).send(embed=discord.Embed(title="Honor Shop Purchase Denied", description=f"Purchase Denied by {interaction.user.mention}", url=interaction.message.jump_url).add_field(name="Purchase", value=purchase, inline=False).add_field(name="Customer", value=customer, inline=False))
                await interaction.message.edit(view=None, embed=interaction.message.embeds[0].add_field(name="Denied By", value=f"{interaction.user.mention}\nNo Refunds.", inline=False))
            except:
                print("interaction issue probably")
                return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await interaction.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=discord.Embed(title=f"[Error][{__class__.__name__}][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[{__class__.__name__}][{inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

class ApprAckDeny(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Acknowledge/Fulfill",style=discord.ButtonStyle.green, custom_id="honorshop:ackful")
    async def ack(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            print(f"{interaction.user} pressed a honor shop ack/fulfill button")
            try:
                try:
                    comuser = discord_to_username([str(interaction.user.id)])[0]
                    rank = get_scgroup_rank([comuser])[comuser]['rank']
                    if rank > 10:
                        action = "Fulfilled"
                    else:
                        action = "Acknowledged"
                except:
                    action = "Fulfilled"
                    print("Not on roster.")
                
                role = interaction.guild.get_role(1255328797981409340)
                if rank < 8 and role not in interaction.user.roles:
                    return
                else:
                    purchase = interaction.message.embeds[0].fields[0].value
                    customer = interaction.message.embeds[0].fields[1].value
                    await interaction.guild.get_channel(588438540090736657).send(embed=discord.Embed(title=f"Honor Shop Purchase {action}", description=f"Purchase {action} by {interaction.user.mention}", url=interaction.message.jump_url, color=interaction.message.embeds[0].color).add_field(name="Purchase", value=purchase, inline=False).add_field(name="Customer", value=customer, inline=False).set_author(name=f"{comuser} > {customer}"))
                    await interaction.message.edit(view=None, embed=interaction.message.embeds[0].add_field(name=f"{action} By", value=interaction.user.mention, inline=False))
            except:
                return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await interaction.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=discord.Embed(title=f"[Error][{__class__.__name__}][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[{__class__.__name__}][{inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    @discord.ui.button(label="Deny",style=discord.ButtonStyle.red, custom_id="honorshop:deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            print(f"{interaction.user} pressed a honor shop deny button")
            role = interaction.guild.get_role(1255328797981409340)
            rostersheets, rosters = exportSheetData()
            try:
                try:
                    comuser = discord_to_username([str(interaction.user.id)])[0]
                    rank = get_scgroup_rank([comuser])[comuser]['rank']
                except:
                    if role not in interaction.user.roles:
                        raise
                if rank < 8 and role not in interaction.user.roles:
                    return
                else:
                    purchase = interaction.message.embeds[0].fields[0].value
                    customer = interaction.message.embeds[0].fields[1].value
                    try:
                        usrinfo = rosters[0].members[customer]
                        rostersheets[0].update_cell(usrinfo["Row"], rosters[0].headers["Honor"], float(interaction.message.embeds[0].fields[-1].value) + float(usrinfo["Honor"]))
                    except:
                        try:
                            usrinfo = rosters[1].members[customer]
                            rostersheets[1].update_cell(usrinfo["Row"], rosters[1].headers["Honor"], float(interaction.message.embeds[0].fields[-1].value) + float(usrinfo["Honor"]))
                        except:
                            None
                    await interaction.guild.get_channel(588438540090736657).send(embed=discord.Embed(title="Honor Shop Purchase Denied", description=f"Purchase Denied by {interaction.user.mention}", url=interaction.message.jump_url, color=interaction.message.embeds[0].color).add_field(name="Purchase", value=purchase, inline=False).add_field(name="Customer", value=customer, inline=False).set_author(name=f"{comuser} > {customer}"))
                    await interaction.message.edit(view=None, embed=interaction.message.embeds[0].add_field(name="Denied By", value=f"{interaction.user.mention}\nIf Honor not replaced contact an Officer"))
            except:
                print("Error in getting comuser or rank probably")
                raise
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await interaction.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=discord.Embed(title=f"[Error][{__class__.__name__}][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[{__class__.__name__}][{inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

class InacApprDeny(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Approve",style=discord.ButtonStyle.green, custom_id="inac:approve")
    async def ack(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            print(f"{interaction.user} pressed a inac:approve button")
            rostersheets, rosters = exportSheetData()
            try:
                try:
                    comuser = discord_to_username([str(interaction.user.id)])[0]
                    rank = get_scgroup_rank([comuser])[comuser]['rank']
                except:
                    print("Not on roster.")
                if rank < 8:
                    return
                else:
                    user = interaction.message.embeds[0].fields[0].value
                    start = interaction.message.embeds[0].fields[1].value
                    end = interaction.message.embeds[0].fields[2].value
                    reason = interaction.message.embeds[0].fields[3].value
                    exemption = findall(r'\d\d/\d\d/\d\d\d\d', end)
                    try:
                        usrinfo = rosters[0].members[user]
                        rostersheets[0].update_cell(usrinfo["Row"], rosters[0].headers["Exempt Until"], exemption[0])
                    except:
                        try:
                            usrinfo = rosters[1].members[user]
                            rostersheets[1].update_cell(usrinfo["Row"], rosters[1].headers["Exempt Until"], exemption[0])
                        except:
                            None
                    await interaction.guild.get_channel(cfg.logchannel_ids[cfg.serverid_to_name[str(interaction.guild_id)]]).send(embed=discord.Embed(title="Inactivity Notice Request Approved", description=f"Inactivity Notice Request Approved by {interaction.user.mention}", url=interaction.message.jump_url, color=interaction.message.embeds[0].color).add_field(name="User", value=user, inline=False).add_field(name="Start", value=start, inline=False).add_field(name="End", value=end, inline=False).add_field(name="Start", value=reason, inline=False).set_author(name=f"{comuser} > {user}"))
                    await interaction.message.edit(view=None, embed=interaction.message.embeds[0].add_field(name="Approved By", value=interaction.user.mention, inline=False))
                    if interaction.guild_id == cfg.server_ids["Nothing To See Here"]:
                        try:
                            user = interaction.guild.get_member(username_to_discord_id([user])[0])
                            await send_dm(user, content=f"Your Inactivity Notice in {cfg.serverid_to_name[str(interaction.guild.id)]} has been accepted.", embeds=interaction.message.embeds)
                            await user.add_roles(interaction.guild.get_role(777273067511611422))
                        except Exception as e:
                            print("Error giving the role to the user or sending DM to user", e)
            except:
                return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await interaction.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=discord.Embed(title=f"[Error][{__class__.__name__}][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[{__class__.__name__}][{inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    @discord.ui.button(label="Deny",style=discord.ButtonStyle.red, custom_id="inac:deny")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            print(f"{interaction.user} pressed a inac:deny button")
            try:
                comuser = discord_to_username([str(interaction.user.id)])[0]
                rank = get_scgroup_rank([comuser])[comuser]['rank']
            except:
                print("Not on Roster.")
            if rank < 8:
                return
            else:
                user = interaction.message.embeds[0].fields[0].value
                start = interaction.message.embeds[0].fields[1].value
                end = interaction.message.embeds[0].fields[2].value
                reason = interaction.message.embeds[0].fields[3].value
                await interaction.guild.get_channel(cfg.logchannel_ids[cfg.serverid_to_name[str(interaction.guild_id)]]).send(embed=discord.Embed(title="Inactivity Notice Request Denied", description=f"Inactivity Notice Request Denied by {interaction.user.mention}", url=interaction.message.jump_url, color=interaction.message.embeds[0].color).add_field(name="User", value=user, inline=False).add_field(name="Start", value=start, inline=False).add_field(name="End", value=end, inline=False).add_field(name="Start", value=reason, inline=False).set_author(name=f"{comuser} > {user}"))
                await interaction.message.edit(view=None, embed=interaction.message.embeds[0].add_field(name="Denied By", value=f"{interaction.user.mention}"))
                try:
                    user = interaction.guild.get_member(username_to_discord_id([user])[0])
                    await send_dm(user, content=f"Your Inactivity Notice in {cfg.serverid_to_name[str(interaction.guild.id)]} has been accepted.", embeds=interaction.message.embeds)
                except Exception as e:
                    print("Error sending DM to user", e)
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await interaction.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=discord.Embed(title=f"[Error][{__class__.__name__}][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[{__class__.__name__}][{inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

class ShopItems(discord.ui.View):
    cancel: bool = False
    selection: str = None

    def __init__(self, *, timeout = 180, save: bool, itemsnum):
        super().__init__(timeout=timeout)
        self.savebutton.disabled = (not save)
        if itemsnum >= 25:
            self.add.disabled = True
        elif itemsnum <= 0:
            self.edit.disabled = True
            self.delete.disabled = True
    @discord.ui.button(label="Add Item",style=discord.ButtonStyle.success)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ItemAdd(title="Name Your Item")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.selection = "Add"
            self.userenteredvalue = modal.submition.value
        self.stop()
    @discord.ui.button(label="Edit Item",style=discord.ButtonStyle.gray)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Edit"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Remove Item",style=discord.ButtonStyle.red)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Remove"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.red, row=1)
    async def can(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancel = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Save",style=discord.ButtonStyle.success, row=1, disabled=True)
    async def savebutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.save = True
        await interaction.response.defer()
        self.stop()

class ItemView(discord.ui.View):
    cancel: bool = False
    selection: str = None
    @discord.ui.button(label="View Item Options",style=discord.ButtonStyle.gray)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "View"
        self.stop()
    @discord.ui.button(label="Close",style=discord.ButtonStyle.red, row=1)
    async def can(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.cancel = True
        self.stop()

class ItemEditSelect(discord.ui.Select):
    selected = False
    selection = None
    def __init__(self, items):

        options = []
        for item in items:
            options.append(discord.SelectOption(label=item))
        super(ItemEditSelect, self).__init__(options=options, placeholder=items[0])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.selection = self.values[0]
        self.selected = True
        return

class ItemAdd(discord.ui.Modal):
    submition = discord.ui.TextInput(label="Item Name",style=discord.TextStyle.short, placeholder="Name", required=True)
    proceed = False
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.proceed = True
        self.stop()

class LimitandCooldown(discord.ui.Modal):
    limit = discord.ui.TextInput(label="Limit",style=discord.TextStyle.short, placeholder="1", required=True)
    cooldown = discord.ui.TextInput(label="Cooldown",style=discord.TextStyle.short, placeholder="1", required=True)
    submision = []
    proceed = False
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.submision = [self.limit.value, self.cooldown.value]
        self.proceed = True
        self.stop()

class OptionAdd(discord.ui.Modal):
    name = discord.ui.TextInput(label="Name",style=discord.TextStyle.short, placeholder="Name", required=True)
    cost = discord.ui.TextInput(label="Cost",style=discord.TextStyle.short, placeholder="10", required=True)
    submision = []
    proceed = False
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.submision = [self.name.value, self.cost.value]
        self.proceed = True
        self.stop()

class BasicModalSelect(discord.ui.Select):
    selected = False
    selection = None
    userenteredvalue = None
    def __init__(self, *, options, modal_titles, modal_prompters, placeholder = None, disabled = False):
        self.prompts: list = modal_prompters
        self.modal_titles: list = modal_titles
        l = []
        for x in options:
            l.append(discord.SelectOption(label=x))
        super().__init__(placeholder=placeholder, max_values=1, options=l, disabled=disabled)
    
    async def callback(self, interaction: discord.Interaction):
        self.selection = self.values[0]
        if self.values[0] in self.prompts:
            if self.placeholder == "Limit & Cooldown?":
                label = self.modal_titles[self.prompts.index(self.selection)]
                modal = LimitandCooldown(title=label)
            else:
                label = self.modal_titles[self.prompts.index(self.selection)]
                modal = BasicModal(title=label)
            await interaction.response.send_modal(modal)
            await modal.wait()
            if modal.proceed:
                if self.placeholder == "Limit & Cooldown?":
                    self.userenteredvalue = modal.submision
                else:
                    self.userenteredvalue = modal.submition.value
                self.selected = True
        else:
            self.selected = True
            await interaction.response.defer()
        return

class BasicSelect(discord.ui.Select):
    selected = False
    selection = None
    def __init__(self, *, options, placeholder = None, max_values, disabled = False):
        l = []
        for x in options:
            l.append(discord.SelectOption(label=x))
        super().__init__(placeholder=placeholder, max_values=max_values, options=l, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        if len(self.values) == 1:
            self.selection = self.values[0]
        else:
            self.selection = self.values
        await interaction.response.defer()
        self.selected = True
        return
    
class HitSelect(discord.ui.Select):
    selected = False
    selection = None
    def __init__(self, *, options, placeholder = None, max_values, disabled = False):
        l = []
        for x in options:
            l.append(discord.SelectOption(label=x))
        super().__init__(placeholder=placeholder, max_values=max_values, options=l, disabled=disabled)

    async def callback(self, interaction: discord.Interaction):
        if len(self.values) == 1:
            self.selection = self.values[0]
        else:
            self.selection = self.values
        modal = HitModal(title="Enter a User")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.target = modal.target.value
            self.selected = True
            return

class ItemEdit(discord.ui.View):
    cancel: bool = False
    save: bool = False
    back: bool = False
    selection: str = None
    userenteredvalue: str = None

    def __init__(self, *, timeout = 180, save: bool, options: int|bool, limit: int, div: bool, coupons: bool):
        super().__init__(timeout=timeout)
        if limit == 0:
            self.cooldown.disabled = True
        if type(options) == bool:
            self.add.disabled = True
            self.edit.disabled = True
            self.delete.disabled = True
        elif options == 25:
            self.add.disabled = True
        elif options == 0:
            self.edit.disabled = True
            self.delete.disabled = True
        self.savebutton.disabled = (not save)
        self.div.disabled = (not div)
        self.cost.disabled = (not div)
        if coupons:
            self.coupon.style = discord.ButtonStyle.red
        else:
            self.coupon.style = discord.ButtonStyle.green


    @discord.ui.button(label="Add Option",style=discord.ButtonStyle.success, row=0)
    async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = OptionAdd(title="Enter a Name and Cost")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.selection = "Add"
            self.userenteredvalue = modal.submision
        self.stop()
    @discord.ui.button(label="Edit Option",style=discord.ButtonStyle.gray, row=0)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Edit"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Remove Option",style=discord.ButtonStyle.red, row=0)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Remove"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Cost",style=discord.ButtonStyle.blurple, row=1)
    async def cost(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = BasicModal(title="Enter a Honor Cost (5 by Default)")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.selection = "Cost"
            self.userenteredvalue = modal.submition.value
        self.stop()
    @discord.ui.button(label="Limit",style=discord.ButtonStyle.blurple, row=1)
    async def limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = BasicModal(title="Enter a Purchase Limit (0 for No Limit)")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.selection = "Limit"
            self.userenteredvalue = modal.submition.value
        self.stop()
    @discord.ui.button(label="Cooldown",style=discord.ButtonStyle.blurple, row=1)
    async def cooldown(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = BasicModal(title="Enter a Cooldown per Purchase")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.selection = "Cooldown"
            self.userenteredvalue = modal.submition.value
        self.stop()
    @discord.ui.button(label="Division",style=discord.ButtonStyle.blurple, row=1)
    async def div(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Division"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Coupons",style=discord.ButtonStyle.blurple, row=1)
    async def coupon(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.selection = "Coupons?"
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Cancel",style=discord.ButtonStyle.red, row=2)
    async def can(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.cancel = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Back",style=discord.ButtonStyle.gray, row=2)
    async def can(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.back = True
        await interaction.response.defer()
        self.stop()
    @discord.ui.button(label="Save",style=discord.ButtonStyle.success, row=2, disabled=True)
    async def savebutton(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.save = True
        await interaction.response.defer()
        self.stop()

class OptionEdit(discord.ui.View):
    back: bool = False
    selection: str = None
    userenteredvalue: str = None

    def __init__(self, *, timeout = 180, divs):
        super().__init__(timeout=timeout)
        x = {"Main Force" : self.mf, "Nothing To See Here" : self.ntsh, "The Armed Gentlemen" : self.tag, "The Crazies" : self.tc, "Iron Fist" : self.ironfist}
        try:
            if divs[0] != "All":
                for i in divs:
                    x[i].style = discord.ButtonStyle.red
            else:
                for i in x:
                    x[i].style = discord.ButtonStyle.red
        except:
            None
    @discord.ui.button(label="Cost",style=discord.ButtonStyle.green, row=0)
    async def cost(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = BasicModal(title="Enter a Cost (0 for No Limit)")
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            self.selection = "Cost"
            self.userenteredvalue = modal.submition.value
        self.stop()
    @discord.ui.button(label="MF",style=discord.ButtonStyle.green, row=1)
    async def mf(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "Main Force"
        self.stop()
    @discord.ui.button(label="NTSH",style=discord.ButtonStyle.green, row=1)
    async def ntsh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "Nothing To See Here"
        self.stop()
    @discord.ui.button(label="TAG",style=discord.ButtonStyle.green, row=1)
    async def tag(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "The Armed Gentlemen"
        self.stop()
    @discord.ui.button(label="TC",style=discord.ButtonStyle.green, row=1)
    async def tc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "The Crazies"
        self.stop()
    @discord.ui.button(label="IF",style=discord.ButtonStyle.green, row=1)
    async def ironfist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "Iron Fist"
        self.stop()
    @discord.ui.button(label="Back",style=discord.ButtonStyle.gray, row=2)
    async def can(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.back = True
        await interaction.response.defer()
        self.stop()

class ItemDivEdit(discord.ui.View):
    back: bool = False
    selection: str = None
    userenteredvalue: str = None

    def __init__(self, *, timeout = 180, divs):
        super().__init__(timeout=timeout)
        x = {"Main Force" : self.mf, "Nothing To See Here" : self.ntsh, "The Armed Gentlemen" : self.tag, "The Crazies" : self.tc, "Iron Fist" : self.ironfist}
        try:
            if divs[0] != "All":
                for i in divs:
                    x[i].style = discord.ButtonStyle.red
            else:
                for i in x:
                    x[i].style = discord.ButtonStyle.red
        except:
            None

    @discord.ui.button(label="MF",style=discord.ButtonStyle.green, row=1)
    async def mf(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "Main Force"
        self.stop()
    @discord.ui.button(label="NTSH",style=discord.ButtonStyle.green, row=1)
    async def ntsh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "Nothing To See Here"
        self.stop()
    @discord.ui.button(label="TAG",style=discord.ButtonStyle.green, row=1)
    async def tag(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "The Armed Gentlemen"
        self.stop()
    @discord.ui.button(label="TC",style=discord.ButtonStyle.green, row=1)
    async def tc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "The Crazies"
        self.stop()
    @discord.ui.button(label="IF",style=discord.ButtonStyle.green, row=1)
    async def ironfist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.selection = "Division"
        self.userenteredvalue = "Iron Fist"
        self.stop()
    @discord.ui.button(label="Back",style=discord.ButtonStyle.gray, row=2)
    async def can(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.back = True
        self.stop()

class RosterEditButtons(discord.ui.View):
    def __init__(self, username: str, division: str, roster: RosterSheet, rostersheet: Worksheet, manualquota: bool):
        super().__init__(timeout=100)
        self.username = username
        self.userinfo = roster.members[username]
        self.division = division
        self.roster = roster
        self.rostersheet = rostersheet
        self.chkqta.disabled = (not manualquota)
    rank: bool = False
    done: bool = False
    adqs: bool = False
    mrkqta: bool = False
    @discord.ui.button(label="Change Rank",style=discord.ButtonStyle.blurple, row=0)
    async def chnrnk(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.rank = True
        await interaction.response.defer()
        self.stop()
        return
    @discord.ui.button(label="Mark Quota",style=discord.ButtonStyle.blurple, row=0)
    async def chkqta(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.mrkqta = True
        await interaction.response.defer()
        self.stop()
        return
    @discord.ui.button(label="Edit Roster Notes",style=discord.ButtonStyle.gray, row=0)
    async def notes(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.division == "Main Force":
            notes = self.userinfo["Notes/Quota Log"]
        else:
            notes = self.userinfo["Notes"]
        newnotes = discord.ui.TextInput(label=f"Notes for {self.username}", style=discord.TextStyle.short, default=notes, required=False)
        modal = NotesModal(title="Roster Notes")
        modal.add_item(newnotes)
        await interaction.response.send_modal(modal)
        await modal.wait()
        if modal.proceed:
            if notes != newnotes.value:
                if self.division == "Main Force":
                    self.rostersheet.update_cell(self.userinfo["Row"], self.roster.headers["Notes/Quota Log"], newnotes.value)
                    self.userinfo["Notes/Quota Log"] = newnotes.value
                else:
                    self.rostersheet.update_cell(self.userinfo["Row"], self.roster.headers["Notes"], newnotes.value)
                    self.userinfo["Notes"] = newnotes.value
        self.stop()
        return
    @discord.ui.button(label="Add Quota Strike",style=discord.ButtonStyle.blurple, row=1)
    async def addqs(self, interaction: discord.Interaction, button: discord.ui.Button):
        if int(self.userinfo["Activity Strikes"]) + 1 <= 3 and self.division != "Nothing To See Here":
            self.rostersheet.update_cell(self.userinfo["Row"], self.roster.headers["Activity Strikes"], int(self.userinfo["Activity Strikes"]) + 1)
            self.userinfo["Activity Strikes"] = int(self.userinfo["Activity Strikes"]) + 1
        elif int(self.userinfo["Activity Strikes"]) + 1 <= 2 and self.division == "Nothing To See Here":
            self.rostersheet.update_cell(self.userinfo["Row"], self.roster.headers["Activity Strikes"], int(self.userinfo["Activity Strikes"]) + 1)
            self.userinfo["Activity Strikes"] = int(self.userinfo["Activity Strikes"]) + 1
        if int(self.userinfo["Activity Strikes"]) == 1:
            self.adqs = True
        else:
            await interaction.guild.get_channel(cfg.logchannel_ids[self.division]).send(embed=discord.Embed(color=cfg.embedcolors[self.division] ,title="Activity Strike Added", description=f"Activity Strike Added to `{self.username}` by {interaction.user.mention}").add_field(name="Activity Strikes", value=f"{int(self.userinfo['Activity Strikes']) - 1} -> {self.userinfo['Activity Strikes']}").add_field(name="Removal Date", value=self.userinfo["Activity Strike Removal Date"]).set_author(name=f"{discord_to_username([str(interaction.user.id)])[0]} > {self.username}"))
        await interaction.response.defer()
        self.stop()
        return
    @discord.ui.button(label="Remove Quota Strike",style=discord.ButtonStyle.blurple, row=1)
    async def rmqs(self, interaction: discord.Interaction, button: discord.ui.Button):
        if int(self.userinfo["Activity Strikes"]) - 1 >= 0:
            self.rostersheet.update_cell(self.userinfo["Row"], self.roster.headers["Activity Strikes"], int(self.userinfo["Activity Strikes"]) - 1)
            self.userinfo["Activity Strikes"] = int(self.userinfo["Activity Strikes"]) - 1
            await interaction.guild.get_channel(cfg.logchannel_ids[self.division]).send(embed=discord.Embed(color=cfg.embedcolors[self.division] ,title="Activity Strike Removed", description=f"Activity Strike Removed from `{self.username}` by {interaction.user.mention}").add_field(name="Activity Strikes", value=f"{int(self.userinfo['Activity Strikes']) + 1} -> {self.userinfo['Activity Strikes']}").set_author(name=f"{discord_to_username([str(interaction.user.id)])[0]} > {self.username}"))
        if int(self.userinfo["Activity Strikes"]) == 0:
            self.rostersheet.update_cell(self.userinfo["Row"], self.roster.headers["Activity Strike Removal Date"], "")
        await interaction.response.defer()
        self.stop()
        return
    @discord.ui.button(label="Remove a Strike",style=discord.ButtonStyle.success, row=1)
    async def rmstrk(self, interaction: discord.Interaction, button: discord.ui.Button):
        if int(self.userinfo["Punishments"]) - 1 >= 0:
            self.rostersheet.update_cell(self.userinfo["Row"], self.roster.headers["Punishments"], int(self.userinfo["Punishments"]) - 1)
            self.userinfo["Punishments"] = int(self.userinfo["Punishments"]) - 1
            await interaction.guild.get_channel(cfg.logchannel_ids[self.division]).send(embed=discord.Embed(color=cfg.embedcolors[self.division] ,title="Strike Removed", description=f"Strike Removed from `{self.username}` by {interaction.user.mention}").add_field(name="Strikes", value=f"{int(self.userinfo['Punishments']) + 1} -> {self.userinfo['Punishments']}").set_author(name=f"{discord_to_username([str(interaction.user.id)])[0]} > {self.username}"))
            if self.division == "Nothing To See Here":
                try:
                    discuser = interaction.guild.get_member(username_to_discord_id([self.username])[0])
                    await discuser.remove_roles(interaction.guild.get_role(759756623484289044))
                except Exception as e:
                    print("issue removing role:", e)
        await interaction.response.defer()
        self.stop()
        return
    @discord.ui.button(label="Done",style=discord.ButtonStyle.success, row=2)
    async def alldone(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.done = True
        await interaction.response.defer()
        self.stop()
        return


