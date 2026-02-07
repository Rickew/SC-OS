from python.uiclasses import BasicSelect, CancelButton, HitSelect, ApprAckDeny, ApproveDenyHit
from python.helpers import exportSheetData, discord_to_username, get_local_path, get_scgroup_rank
from discord import Interaction, app_commands, Embed, Guild
from datetime import datetime as dt
from traceback import format_exc
import data.config as cfg
from asyncio import sleep
import inspect
import json

GUILD_IDS = [
    588427075283714049, #MF
    653542671100411906, #NTSH
    691298558032478208, #IF
    672480434549948438, #TC
    661593066330914828  #TAG
]

COMMAND_NAME = "shop"

ITEMS = {}

def setup(tree: app_commands.CommandTree, guild: Guild):
    def load_options(guild: Guild, b = False):
        server = cfg.serverid_to_name[str(guild.id)]
        with open(get_local_path("data\\shopitems.json"), "r") as f:
            items:dict = json.load(f)
            f.close()
        ITEMS = items.copy()
        options = []
        x = 1
        for item in list(items.keys()):
            try:
                if "All" in items[item]["Division"] or server in items[item]["Division"]:
                    options.append(app_commands.Choice(name=item, value=x))
                    x+=1
                    continue
                else:
                    ITEMS.pop(item)
            except:
                None
            try:
                for option in list(items[item]["Options"].keys()):
                    if "All" not in items[item]["Options"][option]["Division"] and server not in items[item]["Options"][option]["Division"]:
                        ITEMS[item]["Options"].pop(option)
                if len(ITEMS[item]["Options"]) == 0:
                    print(f"popped: {item}")
                    ITEMS.pop(item)
                else:
                    options.append(app_commands.Choice(name=item, value=x))
                    x+=1
                    continue
            except:
                None
        if b:
            return ITEMS
        else:
            return options
    
    # This is the Honor Shop Command. All items get sent to the Main SC Honor Shop Channel for approval/fullfilment, and can also be denied.
    # - Universal Command
    # - Server Based
    # - Automatic Coupon/Discounts/Sales application
    @tree.command(name="shop", description="Purchase an Item From The Honor Shop", guild=guild)
    @app_commands.choices(item=load_options(guild))
    @app_commands.describe(item="The item you want to purchase.")
    @app_commands.describe(usecoupons="Select \"True\" to automatically apply any coupons issued to you.")
    async def shop(intact: Interaction, item: app_commands.Choice[int], usecoupons: bool):
        try:
            print(f"{cfg.logstamp()}[shop] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            ITEMS = load_options(intact.guild, True)
            rostersheets, rosters = exportSheetData()
            comuser = discord_to_username([str(intact.user.id)])[0]
            try:
                index = 0
                comuserinfo = rosters[index].members[comuser]
            except:
                try:
                    index = 1
                    comuserinfo = rosters[index].members[comuser]
                except:
                    await intact.followup.send(embed=Embed(title="Error", description="You are not on the Roster.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild.id)]]))
                    return
            try:
                if float(comuserinfo["Honor"]) < ITEMS[item.name]["Cost"] or float(comuserinfo["Honor"]) < 10:
                    await intact.followup.send(embed=Embed(title="Purchase Failed", description=f"You do not have enough honor to purchase item: {item.name}", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild.id)]]))
                    return
            except:
                None

            # Division Locking
            try:
                if comuserinfo["TFD"] != cfg.serverid_to_name[str(intact.guild_id)] and comuserinfo["TFD"] != "Directorate":
                    await intact.followup.send(embed=Embed(title="Error", description=f"You must use this command in your own server.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild.id)]]))
                    return
            except:
                None
            
            # Option Select
            try:
                view = CancelButton()
                if item.name == "NTSH Assassination":
                    optionselect = HitSelect(options=ITEMS[item.name]["Options"], placeholder="Select an Option", max_values=1)
                    content = content="WARNING: No honor will be taken if user is not in SC (name spelled wrong or etc), but **if you specify the wrong rank option** your honor will still be taken, and NTSH will not do the hit."
                else:
                    optionselect = BasicSelect(options=ITEMS[item.name]["Options"], placeholder="Select an Option", max_values=1)
                    content = None
                optionembed = Embed(title=f"Options For {item.name}", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]])
                for x in ITEMS[item.name]["Options"]:
                    optionembed.add_field(name=x, value=f"**Cost:** `{ITEMS[item.name]['Options'][x]['Cost']}`")
                view.add_item(optionselect)
                await intact.followup.send(embed=optionembed, view=view, content=content)
                i = 0
                while not optionselect.selected and not view.cancel:
                    await sleep(1)
                    i+=1
                    if i >= 100:
                        return
                if view.cancel:
                    await intact.delete_original_response()
                    return
                # see if they can even buy it.
                if "Main Force" in ITEMS[item.name]["Options"][optionselect.selection]["Division"]:
                    try:
                        if rosters[1].members[comuser]:
                            await Interaction.edit_original_response(view=None, content=None, embed=Embed(title="Purchase Failed", description=f"That item is not available to your division, or you need to purchase it in your TFD's Server."))
                            return
                    except:
                        None
                
                
                # check item limits
                if ITEMS[item.name]["Limit"] > 0:
                    with open(get_local_path("data\\shoppuchases.json"), "r") as f:
                        priorpurchases = json.load(f)
                        f.close
                    try:
                        # if the customer is over the limit with this purchase, by asking is this purchase long enough after their earliest purchase of this item to be not over limit
                        if priorpurchases[item.name][str(intact.user.id)]["Purchases"] + 1 > ITEMS[item.name]['Limit'] and int(dt.now().timestamp()) < (priorpurchases[item.name][str(intact.user.id)]["History"][0] + (ITEMS[item.name]["Cooldown"]*3600)):
                            # if this is going over limit
                            await intact.edit_original_response(content=None, view=None, embed=Embed(title="Purchase Failed", description=f"You have reached the limit on this item. You must wait until <t:{(priorpurchases[item.name][str(intact.user.id)]['History'][0] + (ITEMS[item.name]['Cooldown']*3600))}:S> to purchase {item.name} again.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild.id)]]))
                            return
                        else:
                            priorpurchases[item.name][str(intact.user.id)]["Purchases"] += 1
                            priorpurchases[item.name][str(intact.user.id)]["History"].append(int(dt.now().timestamp()))
                            priorpurchases[item.name][str(intact.user.id)]["History"].pop(0)

                    except:
                        try:
                            priorpurchases[item.name].update({str(intact.user.id) : {"Purchases" : 1, "History" : [int(dt.now().timestamp())]}})
                        except:
                            priorpurchases.update({item.name : {str(intact.user.id) : {"Purchases" : 1, "History" : [int(dt.now().timestamp())]}}})
                    
                    with open(get_local_path("data\\shoppuchases.json"), "w") as f:
                        json.dump(priorpurchases, f, indent=2)
                        f.close
                deduction = ITEMS[item.name]['Options'][optionselect.selection]['Cost']
                finalembed = Embed(title=f"Honor Shop Purchase", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]).add_field(name="Purchase", value=f"{item.name} - {optionselect.selection}", inline=False).add_field(name="Customer", value=comuser, inline=False).add_field(name="Cost", value=deduction, inline=False)
                if item.name == "NTSH Assassination":
                    finalembed.add_field(name="Target", value=optionselect.target, inline=False)
                    try:
                        tarinfo = rosters[0].members[optionselect.target]
                        tardiv = "Main Force"
                    except:
                        try:
                            tarinfo = rosters[1].members[optionselect.target]
                            tardiv = tarinfo["TFD"]
                        except:
                            await intact.edit_original_response(view=None, embed=None, content="Target not in SC, or not on the Roster.")
                            return
                    finalembed.add_field(name="Target Divsion", value=tardiv).add_field(name="Target's Rank", value=tarinfo["Rank"])

                        
                    
            except:
                if ITEMS[item.name]["Limit"] > 0:
                    with open(get_local_path("data\\shoppurchases.json"), "r") as f:
                        priorpurchases = json.load(f)
                        f.close
                    try:
                        # if the customer is over the limit with this purchase, by asking is this purchase long enough after their earliest purchase of this item to be not over limit
                        if priorpurchases[item.name][str(intact.user.id)]["Purchases"] + 1 > ITEMS[item.name]['Limit'] and int(dt.now().timestamp()) < (priorpurchases[item.name][str(intact.user.id)]["History"][0] + (ITEMS[item.name]["Cooldown"]*3600)):
                            # if this is going over limit
                            await intact.edit_original_response(content=None, view=None, embed=Embed(title="Purchase Failed", description=f"You have reached the limit on this item. You must wait until <t:{(priorpurchases[item.name][str(intact.user.id)]['History'][0] + (ITEMS[item.name]['Cooldown']*3600))}:S> to purchase {item.name} again.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild.id)]]))
                            return
                        else:
                            priorpurchases[item.name][str(intact.user.id)]["Purchases"] += 1
                            priorpurchases[item.name][str(intact.user.id)]["History"].append(int(dt.now().timestamp()))
                            priorpurchases[item.name][str(intact.user.id)]["History"].pop(0)


                    except:
                        try:
                            priorpurchases[item.name].update({str(intact.user.id) : {"Purchases" : 1, "History" : [int(dt.now().timestamp())]}})
                        except:
                            priorpurchases.update({item.name : {str(intact.user.id) : {"Purchases" : 1, "History" : [int(dt.now().timestamp())]}}})
                    
                    with open(get_local_path("data\\shoppuchases.json"), "w") as f:
                        json.dump(priorpurchases, f, indent=2)
                        f.close
                deduction = ITEMS[item.name]['Cost']
                finalembed = Embed(title=f"Honor Shop Purchase", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]).add_field(name="Purchase", value=f"{item.name}", inline=False).add_field(name="Customer", value=comuser, inline=False).add_field(name="Cost", value=deduction, inline=False)

            # run sales, discounts and coupons
            if ITEMS[item.name]["Coupons?"]:
                with open(get_local_path("data\\coupons.json"), "r") as f:
                    coupons = json.load(f)
                    f.close()
                string = ""
                try:
                    if dt.now().day == 1:
                        deduction -= deduction*coupons["Sales"]["Monthly Sale"]
                        string += "Sale: Monthly Sale\n"
                    if dt.now().weekday() in [5, 6]:
                        deduction -= deduction*coupons["Sales"]["Weekend Sale"]
                        string += "Sale: Weekend Sale\n"
                except:
                    None
                temp = tree.client.get_guild(588427075283714049).get_role(1239749185226543185).members
                NCOmemIDs = []
                for mem in temp:
                    NCOmemIDs.append(mem.id)
                rank = get_scgroup_rank([str(comuser)])
                rank = rank[comuser]['rank']
                if rank < 8 and intact.user.id in NCOmemIDs:
                    deduction -= deduction*coupons["Discounts"]["NCO"]
                    string += "Discount: NCO Discount\n"
                elif rank >= 8:
                    deduction -= deduction*coupons["Discounts"]["Officer"]
                    string += "Discount: Officer Discount\n"
                temp = tree.client.get_guild(588427075283714049).get_role(1288566904486891650).members
                motwmemids = []
                for mem in temp:
                    motwmemids.append(mem.id)
                if intact.user.id in motwmemids:
                    deduction -= deduction*coupons["Discounts"]["MOTW"]            
                    string += "Discount: MOTW Discount\n"
                try:
                    applied = None
                    if usecoupons:
                        for coupon in coupons["Coupons"][item.name]:
                            if str(intact.user.id) in coupons["Coupons"][item.name][coupon]["issuedto"]:
                                applied = coupons["Coupons"][item.name][coupon]
                                couponname = coupon

                    if applied:
                        deduction -= deduction*applied['Discount']
                        string += f"Coupon Applied: {couponname}\nIssued By: {applied['issuedby']}\nIssued On: <t:{applied['issuedon']}:S>"
                        coupons["Coupons"][item.name][couponname]["issuedto"].remove(str(intact.user.id))
                        if len(coupons["Coupons"][item.name][couponname]['issuedto']) <= 0:
                            coupons["Coupons"][item.name].pop(couponname)
                            if len(coupons["Coupons"][item.name]) <= 0:
                                coupons["Coupons"].pop(item.name)
                        
                except:
                    None
                if string != "":
                    finalembed.add_field(name="Sales/Discounts/Coupons Applied", value=string, inline=False).add_field(name="Final Cost", value=deduction, inline=False)

                with open(get_local_path("data\\coupons.json"), "w") as f:
                    json.dump(coupons, f, indent=2)
                    f.close()
            # if they can't buy it
            if float(comuserinfo["Honor"]) < deduction:
                await intact.edit_original_response(content=None, view=None, embed=Embed(title="Purchase Failed", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]], description=f"You do not have enough honor to purchase item: {item.name}: {optionselect.selection}"))
                return
            
            rostersheets[index].update_cell(comuserinfo["Row"], rosters[index].headers["Honor"], float(comuserinfo["Honor"]) - deduction)
            await intact.edit_original_response(content="Done", view=None, embed=None)
            if item.name == "NTSH Assassination":
                view = ApproveDenyHit()
                await tree.client.get_guild(751538726647103489).get_channel(1336710880234176666).send(embed=finalembed, view=view)
            else:
                view = ApprAckDeny()
                await tree.client.get_guild(588427075283714049).get_channel(1273403110668369930).send(embed=finalembed, view=view)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][{inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[{inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    
    print(f"{cfg.logstamp()}[Setup]{cfg.Success} shop command setup complete for Guild: {guild.id}")

        

