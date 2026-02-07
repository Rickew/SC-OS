from python.uiclasses import ShopItems, ItemEditSelect, CancelButton, YesorNo, ItemEdit, ItemDivEdit, OptionEdit, BasicSelect, BasicModalSelect, ItemView, CancelorBack
from python.helpers import discord_to_username, get_local_path, get_scgroup_rank
from discord import Interaction, app_commands, Embed, Guild, Object
from python.commands import coupon, honorshop
from traceback import format_exc
import data.config as cfg
from asyncio import sleep
import inspect
import json

ITEMS = {}

COMMAND_NAME = "shopitems"

GUILD_IDS = [
    588427075283714049, #MF
    653542671100411906, #NTSH
    691298558032478208, #IF
    672480434549948438, #TC
    661593066330914828  #TAG
]

def div_frmt(divs: list):
    return str(divs).strip('[]').replace("'", "")

def get_diffs(items, untouched):
    diffs = {}
    for x in items:
        for y in items[x]:
            try: 
                for z in items[x][y]:
                    untouched[x][y]
                    try:
                        if items[x][y][z] != untouched[x][y][z]:
                            try:
                                diffs[x]
                                try:
                                    diffs[x][y].update({z : items[x][y][z]})

                                except:
                                    diffs[x].update({y : {z : items[x][y][z]}})
                            except:
                                diffs.update({x : {y : {z : items[x][y][z]}}})
                    except:
                        try:
                            diffs[x]
                            try:
                                diffs[x][y].update({z : items[x][y][z]})

                            except:
                                diffs[x].update({y : {z : items[x][y][z]}})
                        except:
                            diffs.update({x : {y : {z : items[x][y][z]}}})
            except:
                try:
                    if items[x][y] != untouched[x][y]:
                        try:
                            diffs[x].update({y : items[x][y]})
                        except:
                            diffs.update({x : {y : items[x][y]}})
                except:
                    diffs.update({x : items[x]})
    for x in untouched:
        try:
            items[x]
        except:
            diffs.update({x : untouched[x]})
            continue
        try:
            for y in untouched[x]["Options"]:
                try:
                    items[x]["Options"][y]
                except:
                    try:
                        diffs[x]["Options"].update({y : untouched[x]["Options"][y]})
                    except:
                        try:
                            diffs[x].update({"Options" : {y : untouched[x]["Options"][y]}})
                        except:
                            diffs.update({x : {"Options" : {y : untouched[x]["Options"][y]}}})
        except:
            None # no options
    return diffs

def load_options(guild: Guild):
        server = cfg.serverid_to_name[str(guild.id)]
        with open(get_local_path("data\\shopitems.json"), "r") as f:
            items = json.load(f)
            f.close()
        options = []
        x = 1
        for item in items:
            try:
                if "All" in items[item]["Division"] or server in items[item]["Division"]:
                    ITEMS.update({item : items[item]})
                    options.append(app_commands.Choice(name=item, value=x))
                    x+=1
                    continue
            except:
                None
            try:
                ITEMS.update({item : items[item]})
                for option in items[item]["Options"]:
                    if "All" not in items[item]["Options"][option]["Division"] and guild not in items[item]["Options"][option]["Division"]:
                        ITEMS[item]["Options"].pop(option)
                if len(ITEMS[item]["Options"]) == 0:
                    ITEMS.pop(item)
                else:
                    options.append(app_commands.Choice(name=item, value=x))
                    x+=1
                    continue
            except:
                None
        return options

def setup(tree: app_commands.CommandTree):
    # shopitems command ground
    shopitems = app_commands.Group(name="shopitems", description="View or Edit Shop Items", guild_ids=GUILD_IDS, guild_only=True)
    tree.add_command(shopitems)


    # Allows authorized users to edit the honor shop items.
    # - Universal Command
    # - Rank Locked
    @shopitems.command(name="edit", description="Edit the Honor Shop Items")
    async def edit(intact: Interaction):
        try:
            # I am not commenting this fucking command, its 500 lines long, someone else can bother with that shit, maybe they can optimize it too, hell that'd be cool now wouldn't it.
            print(f"{cfg.logstamp()}[ShopItems edit] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)

            # rank lock
            comuser = discord_to_username([str(intact.user.id)])[0]
            comranknum = get_scgroup_rank([comuser])[comuser]['rank']
            if comranknum < 10:
                await intact.followup.send("You're not allowed to run this command.") 
                return

            # load the shop items and buttons for editing
            with open(get_local_path("data\\shopitems.json"), "r") as f:
                items: dict[str,dict] = json.load(f)
                f.close()
            with open(get_local_path("data\\shopitems.json"), "r") as f:
                untouched: dict[str,dict] = json.load(f)
                f.close()

            while True:
                embed = Embed(title="Shop Items")
                itemoptions = []
                for item in items:
                    x = items[item]
                    try:
                        # some items have options
                        embed.add_field(name=item,value=f"Cost:`{x['Cost']}`\nLimit: `{x['Limit']}`\nCooldown: `{x['Cooldown']}` Hours\nCoupons? `{x['Coupons?']}`")
                    except:
                        embed.add_field(name=item,value=f"Item Options:`{len(x['Options'])}`\nLimit: `{x['Limit']}`\nCooldown: `{x['Cooldown']}` Hours\nCoupons? `{x['Coupons?']}`")
                    itemoptions.append(item)

                #load buttons
                diffs = get_diffs(items, untouched)
                view = ShopItems(save=len(diffs), itemsnum=len(items))
                await intact.edit_original_response(embed=embed, view=view)
                ind = await view.wait()
                if ind:
                    return
                
                if view.selection == "Add":
                    newname = view.userenteredvalue.replace('"', '\\"')
                    placeholder = ["Main Force", "Nothing To See Here", "The Armed Gentlemen", "The Crazies", "Iron Fist"]
                    view = CancelButton()
                    selects: list[BasicModalSelect | BasicSelect] = [
                    BasicModalSelect(options=['Yes', 'No'], modal_titles=["Enter a Cost"], modal_prompters=["No"], placeholder="Sub-Options?", disabled=True),
                    BasicModalSelect(options=['Yes', 'No'], modal_titles=["Enter a Limit & Cooldown"], modal_prompters=["Yes"], placeholder="Limit & Cooldown?", disabled=True),
                    BasicSelect(options=["Yes", "No"], placeholder="Coupons?", max_values=1, disabled=True),
                    BasicSelect(options=placeholder, placeholder="Divsion Access", max_values=5, disabled=True)
                    ]
                    x = 0
                    values = ["Not Selectied", "Not Selectied", "Not Selectied", "Not Selectied", "Not Selectied", "Not Selectied"]
                    for select in selects:
                        view.add_item(select)
                    for select in selects:
                        if x == 5 and values[1]:
                            break
                        try:
                            items[newname]
                            continue
                        except:
                            None
                        embed = Embed(title=f"New Item: {newname}", description=f"**Cost:**\n`{values[0]}`\n**Sub-Options:**\n`{values[1]}`\n**Limit:**\n`{values[2]}`\n**Cooldown:**\n`{values[3]}`\n**Coupons?**\n`{values[4]}`\n**Available to Divisions:**\n`{div_frmt(values[5])}`")
                        select.disabled = False
                        await intact.edit_original_response(embed=embed, view=view)
                        i = 0
                        while not select.selected and not view.cancel:
                            await sleep(1)
                            i+=1
                            if i >= 100:
                                return
                        select.disabled = True
                        if view.cancel:
                            break
                        elif x == 0:
                            if select.userenteredvalue:
                                try:
                                    if int(select.userenteredvalue) < 5:
                                        raise
                                    values[x] = int(select.userenteredvalue)
                                except:
                                    values[x] = 5
                                x+=1
                                values[x] = False
                            else:
                                values[x] = "N/A"
                                values[5] = "N/A"
                                x+=1
                                values[x] = True

                        elif x == 2:
                            try:
                                values[2] = int(select.userenteredvalue[0])
                                values[3] = int(select.userenteredvalue[1])
                                x+=1
                            except:
                                values[2] = 0
                                values[3] = 0
                                x+=1
                        elif type(select.selection) == str:
                            if select.selection == "Yes":
                                values[x] = True
                            elif select.selection == "No":
                                values[x] = False
                            else:
                                values[x] = select.selection
                        elif type(select.selection) == list:
                            if len(select.selection) == 5:
                                values[x] = ["All"]
                            else:
                                values[x] = select.selection   
                        x+=1
                    if view.cancel:
                        continue
                    embed = Embed(title=f"New Item: {newname}", description=f"**Cost:**\n`{values[0]}`\n**Sub-Options:**\n`{values[1]}\n**Limit:**\n`{values[2]}`\n**Cooldown:**\n`{values[3]}`\n**Coupons?**\n`{values[4]}`\n**Available to Divisions:**\n`{values[5]}`")
                    await intact.edit_original_response(embed=embed, view=view)
                    if values[1]:
                        items.update({newname : {"Options" : {}, "Limit" : values[2], "Cooldown": values[3], "Coupons?" : values[4]}})
                    else:
                        items.update({newname : {"Cost" : values[0], "Limit" : values[2], "Cooldown": values[3], "Coupons?" : values[4], "Division" : values[5]}})
                    continue

                elif view.selection == "Edit":
                    view = CancelButton()
                    select = ItemEditSelect(itemoptions)
                    view.add_item(select)
                    await intact.edit_original_response(embed=None, view=view)
                    x = 0
                    while not select.selected and not view.cancel:
                        await sleep(1)
                        x+=1
                        if x == 100:
                            return
                    if view.cancel:
                        continue

                    while True:
                        diffs = get_diffs(items, untouched)
                        x = items[select.selection]
                        options = []
                        try:
                            embed = Embed(title=f"Item Details for: {select.selection}", description=f"Cost:`{x['Cost']}`\nLimit: `{x['Limit']}`\nCooldown: `{x['Cooldown']}` Hours per Purchase\nCoupons? `{x['Coupons?']}`\nAvailable to Divisions: `{div_frmt(x['Division'])}`")
                            view = ItemEdit(save=diffs, options=False, limit=x['Limit'], div=True, coupons=x['Coupons?'])
                        except:
                            embed = Embed(title=f"Item Details for: {select.selection}", description=f"Limit: `{x['Limit']}`\nCooldown: `{x['Cooldown']}` Hours per Purchase\nCoupons? `{x['Coupons?']}`")
                            for op in x["Options"]:
                                y = x['Options'][op]
                                embed.add_field(name=op,value=f"Cost: `{y['Cost']}`\nAvailable to Divisions: `{div_frmt(y['Division'])}`")
                                options.append(op)
                            view = ItemEdit(save=diffs, options=len(options), limit=x["Limit"], div=False, coupons=x['Coupons?'])

                        await intact.edit_original_response(embed=embed, view=view)
                        await view.wait()
                        
                        # edit menu
                        if view.selection == "Add":
                            divs = "Not Selected"
                            name = view.userenteredvalue[0]
                            try:
                                items[select.selection]["Options"][name]
                                continue
                            except:
                                None
                            try:
                                if int(view.userenteredvalue[1]) < 5:
                                    raise
                                cost = int(view.userenteredvalue[1])
                                embed = Embed(title=f"New Option: {name}", description=f"**Cost:**\n`{cost}`\n**Available to Divisions:**\n`{divs}`")
                            except:
                                cost = 5
                                embed = Embed(title=f"New Option: {name}", description=f"**Cost:**\n`{cost}`\n**Available to Divisions:**\n`{divs}`")
                            view = CancelButton()
                            divselect = BasicSelect(options=["Main Force", "Nothing To See Here", "The Armed Gentlemen", "The Crazies", "Iron Fist"], placeholder="Divsion Access", max_values=5, disabled=False)
                            view.add_item(divselect)
                            await intact.edit_original_response(view=view, embed=embed)
                            i=0
                            while not divselect.selected and not view.cancel:
                                await sleep(1)
                                i+=1
                                if i >= 100:
                                    return
                            if view.cancel:
                                continue
                            if type(divselect.selection) == list:
                                if len(divselect.selection) == 5:
                                    divs = ["All"]
                                else:
                                    divs = divselect.selection
                            else:
                                divs = [divselect.selection]
                            items[select.selection]["Options"].update({name : {"Cost" : cost, "Division" : divs}})
                            continue

                        elif view.selection == "Edit":
                            view = CancelButton()
                            optionselect = ItemEditSelect(options)
                            view.add_item(optionselect)
                            await intact.edit_original_response(embed=None, view=view)
                            z = 0
                            while not optionselect.selected and not view.cancel:
                                await sleep(1)
                                z+=1
                                if z == 100:
                                    return
                            if view.cancel:
                                await intact.delete_original_response()
                                return
                            while True:
                                y = x['Options'][optionselect.selection]
                                view = OptionEdit(divs=y['Division'])
                                embed = Embed(title=f"Option Details for {optionselect.selection}", description=f"Cost:\n`{y['Cost']}`\nAvailable in Divisions:\n`{div_frmt(y['Division'])}`")
                                await intact.edit_original_response(view=view, embed=embed)
                                await view.wait()
                                if view.selection == "Cost":
                                    try:
                                        if int(view.userenteredvalue) >= 5:
                                            items[select.selection]["Options"][optionselect.selection][view.selection] = int(view.userenteredvalue)
                                    except:
                                        None
                                    continue
                                elif view.selection == "Division":
                                    placeholder = ["Main Force", "Nothing To See Here", "The Armed Gentlemen", "The Crazies", "Iron Fist"]
                                    if view.back:
                                        break
                                    elif view.selection:
                                        if view.userenteredvalue in y['Division']:
                                            items[select.selection]['Options'][optionselect.selection][view.selection].remove(view.userenteredvalue)
                                        elif "All" in y['Division']:
                                            placeholder.remove(view.userenteredvalue)
                                            items[select.selection]['Options'][optionselect.selection][view.selection] = placeholder
                                        elif len(y['Division']) == 4:
                                            items[select.selection]['Options'][optionselect.selection][view.selection] = ["All"]
                                        else:
                                            items[select.selection]['Options'][optionselect.selection][view.selection].append(view.userenteredvalue)
                                elif view.back:
                                    break
                        
                        elif view.selection == "Remove":
                            view = CancelButton()
                            optionselect = ItemEditSelect(options)
                            view.add_item(optionselect)
                            await intact.edit_original_response(embed=None, view=view)
                            x = 0
                            while not optionselect.selected and not view.cancel:
                                await sleep(1)
                                x+=1
                                if x == 100:
                                    return
                            if view.cancel:
                                await intact.delete_original_response()
                                return
                            view = YesorNo()
                            await intact.edit_original_response(view=view)
                            await view.wait()
                            if view.yes:
                                items[select.selection]["Options"].pop(optionselect.selection)
                            else:
                                continue
                        elif view.selection == "Cost":
                            try:
                                if int(view.userenteredvalue) >= 5:
                                    items[select.selection]['Cost'] = int(view.userenteredvalue)
                            except:
                                None
                            continue
                        elif view.selection == "Limit":
                            try:
                                if int(view.userenteredvalue) == 0:
                                    items[select.selection][view.selection] = int(view.userenteredvalue)
                                    items[select.selection]["Cooldown"] = 0
                                elif int(view.userenteredvalue) > 0:
                                    items[select.selection][view.selection] = int(view.userenteredvalue)
                                    if items[select.selection]["Cooldown"] == 0:
                                        items[select.selection]["Cooldown"] = 1
                            except:
                                continue
                        elif view.selection == "Cooldown":
                            try:
                                if int(view.userenteredvalue) == 0:
                                    items[select.selection][view.selection] = int(view.userenteredvalue)
                                    items[select.selection]["Limit"] = 0
                                elif int(view.userenteredvalue) > 0:
                                    items[select.selection][view.selection] = int(view.userenteredvalue)
                            except:
                                continue
                        elif view.selection == "Division":
                            while True:
                                placeholder = ["Main Force", "Nothing To See Here", "The Armed Gentlemen", "The Crazies", "Iron Fist"]
                                x = items[select.selection]
                                embed = Embed(title=f"Item Details for: {select.selection}", description=f"Cost:`{x['Cost']}`\nLimit: `{x['Limit']}`\nCooldown: `{x['Cooldown']}` Hours per Purchase\nCoupons? `{x['Coupons?']}`\nAvailable to Divisions: `{div_frmt(x['Division'])}`")
                                view = ItemDivEdit(divs=x['Division'])
                                await intact.edit_original_response(embed=embed, view=view)
                                await view.wait()
                                if view.back:
                                    break
                                elif view.selection:
                                    if view.userenteredvalue in x['Division']:
                                        items[select.selection][view.selection].remove(view.userenteredvalue)
                                    elif "All" in x['Division']:
                                        placeholder.remove(view.userenteredvalue)
                                        items[select.selection][view.selection] = placeholder
                                    elif len(x['Division']) == 4:
                                        items[select.selection][view.selection] = ["All"]
                                    else:
                                        items[select.selection][view.selection].append(view.userenteredvalue)
                        elif view.selection == "Coupons?":
                            items[select.selection][view.selection] = (not items[select.selection][view.selection])
                        elif view.cancel:
                            await intact.delete_original_response()
                            return
                        elif view.back:
                            break
                        elif view.save:
                            break
                elif view.selection == "Remove":
                    view = CancelButton()
                    select = ItemEditSelect(itemoptions)
                    view.add_item(select)
                    await intact.edit_original_response(embed=None, view=view)
                    x = 0
                    while not select.selected and not view.cancel:
                        await sleep(1)
                        x+=1
                        if x == 100:
                            return
                    if view.cancel:
                        await intact.delete_original_response()
                        return
                    view = YesorNo()
                    await intact.edit_original_response(view=view)
                    await view.wait()
                    if view.yes and select.selection != "NTSH Assassination":
                        items.pop(select.selection)
                    else:
                        continue


                elif view.cancel:
                    await intact.delete_original_response()
                    return
                try:
                    if view.save:
                        break
                except:
                    None

            diffs = get_diffs(items, untouched)
            await intact.edit_original_response(view=None, embed=None, content="Saved!")
            
            # save everything and resync command
            with open(get_local_path("data\\shopitems.json"), "w") as f:
                json.dump(items, f, indent=2)
                f.close()

            embeds = []
            for x in diffs:
                try:
                    items[x]
                except:
                    try:
                        embeds.append(Embed(title=f"Item Deleted From Honor Shop {x}", description=f"Honor Shop Item Deleted By: {intact.user.mention}").add_field(name="Cost",value=diffs[x]["Cost"], inline=False).add_field(name="Limit",value=diffs[x]["Limit"], inline=False).add_field(name="Cooldown",value=diffs[x]["Cooldown"], inline=False).add_field(name="Coupons?",value=diffs[x]["Coupons?"], inline=False).add_field(name="Available To Divisions",value=div_frmt(diffs[x]["Division"]), inline=False))
                        continue
                    except:
                        embed = Embed(title=f"Item Deleted From Honor Shop {x}", description=f"Honor Shop Item Deleted By: {intact.user.mention}\n**Limit:** `{diffs[x]['Limit']}`\n**Cooldown:** `{diffs[x]['Cooldown']}`\n**Coupons?** `{diffs[x]['Coupons?']}`\n**Options:** `{len(diffs[x]['Options'])} Options`")
                        for y in diffs[x]["Options"]:
                            embed.add_field(name=y,value=f"**Cost:**\n`{diffs[x]['Options'][y]['Cost']}`\n**Divisions:**\n`{div_frmt(diffs[x]['Options'][y]['Division'])}`", inline=False)
                        embeds.append(embed.set_author(name=f"{comuser}"))
                        continue
                try:
                    untouched[x]
                except:
                    try:
                        embeds.append(Embed(title=f"Item Added to Honor Shop: {x}", description=f"Honor Shop Item Added By: {intact.user.mention}").add_field(name="Cost",value=diffs[x]["Cost"], inline=True).add_field(name="Limit",value=diffs[x]["Limit"], inline=True).add_field(name="Cooldown",value=diffs[x]["Cooldown"], inline=True).add_field(name="Coupons?",value=diffs[x]["Coupons?"], inline=True).add_field(name="Available To Divisions",value=div_frmt(diffs[x]["Division"]), inline=True))
                        continue
                    except:
                        embed = Embed(title=f"Item Added to Honor Shop: {x}", description=f"Honor Shop Item Added By: {intact.user.mention}\n**Limit:** `{diffs[x]['Limit']}`\n**Cooldown:** `{diffs[x]['Cooldown']}`\n**Coupons?** `{diffs[x]['Coupons?']}`\n**Options:** `{len(diffs[x]['Options'])} Options`")
                        for y in diffs[x]["Options"]:
                            embed.add_field(name=y,value=f"**Cost:**\n`{diffs[x]['Options'][y]['Cost']}\n**Divisions:**\n`{div_frmt(diffs[x]['Options'][y]['Division'])}`", inline=False)
                        embeds.append(embed.set_author(name=f"{comuser}"))
                        continue

                # else its a change
                embed = Embed(title="Item Changed in Honor Shop", description=f"{x} Modified by {intact.user.mention}")
                for y in diffs[x]:
                    # go through options changes
                    if y == "Options":
                        for z in diffs[x][y]:
                            try:
                                # option addition
                                embed.add_field(name=f"Option Added: {z}",value=f"**Cost:**\n`{items[x][y][z]['Cost']}`\n**Available to Divisions:**\n`{div_frmt(items[x][y][z]['Division'])}`", inline=False)
                                continue
                            except:
                                try:
                                    # option deletion
                                    embed.add_field(name=f"Option Deleted: {z}",value=f"**Cost:**\n`{untouched[x][y][z]['Cost']}`\n**Available to Divisions:**\n`{div_frmt(untouched[x][y][z]['Division'])}`", inline=False)
                                    continue
                                except:
                                    None
                            for t in diffs[x][y][z]:
                                if t == "Division":
                                    embed.add_field(name=f"Option: **{z}**, Attribute: **{t}**", value=f"`{div_frmt(diffs[x][y][z][t])}` -> `{div_frmt(diffs[x][y][z][t])}`", inline=False)
                                else:
                                    embed.add_field(name=f"Option: **{z}**, Attribute: **{t}**", value=f"`{diffs[x][y][z][t]}` -> `{diffs[x][y][z][t]}`", inline=False)
                    elif y == "Division":
                        embed.add_field(name="Divisions Changed", value=f"`{div_frmt(untouched[x][y])}` -> `{div_frmt(diffs[x][y])}`", inline=False)             
                    else:
                        embed.add_field(name=f"{y.replace('?', '')} Changed", value=f"`{untouched[x][y]}` -> `{diffs[x][y]}`", inline=False)
                embeds.append(embed.set_author(name=f"{comuser}"))

            # log sending
            if len(embeds) > 10:
                for x in range(0, len(embeds), 10):
                    temp = []
                    for i in range(x, x+10):
                        try:
                            temp.append(embeds[i])
                        except:
                            break
                    await tree.client.get_guild(588427075283714049).get_channel(588438540090736657).send(embeds=temp)
                        
            else:
                await tree.client.get_guild(588427075283714049).get_channel(588438540090736657).send(embeds=embeds)
            
            guildcommands = [honorshop, coupon]

            for gid in GUILD_IDS:
                tree.remove_command("coupon", guild=Object(id=gid)) 
                tree.remove_command("shop", guild=Object(id=gid))
            print(f"{cfg.logstamp()}[Shopitems edit]{cfg.Success} coupon and shop commands Removed")
            
            for x in guildcommands:
                for gid in x.GUILD_IDS:
                    x.setup(tree, guild=Object(id=gid))
            print(f"{cfg.logstamp()}[Shopitems edit]{cfg.Success} Guild commands Re-Setup complete")

            # command resync
            for gid in GUILD_IDS:
                await tree.sync(guild=Object(id=gid))
                print(f"{cfg.logstamp()}[Shopitems edit]{cfg.Success} Re-Synced guild commands for {gid}: {tree.client.get_guild(gid).name}")
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Shopitems {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Shopitems {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

    # Allows regular users to view the honor shop items
    # - Universal Command
    # - Division Locked
    @shopitems.command(name="view", description="View the Honor Shop Items")
    async def view(intact: Interaction):
        try:
            print(f"{cfg.logstamp()}[ShopItems view] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            load_options(intact.guild)
            while True:
                embed = Embed(title="Shop Items", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]])
                itemoptions = []
                for item in ITEMS:
                    x = ITEMS[item]
                    try:
                        # some items have options
                        embed.add_field(name=item,value=f"Cost:`{x['Cost']}`\nLimit: `{x['Limit']}`\nCooldown: `{x['Cooldown']}` Hours\nCoupons? `{x['Coupons?']}`")
                    except:
                        embed.add_field(name=item,value=f"Item Options:`{len(x['Options'])}`\nLimit: `{x['Limit']}`\nCooldown: `{x['Cooldown']}` Hours\nCoupons? `{x['Coupons?']}`")
                    try:
                        if x["Options"]:
                            itemoptions.append(item)
                    except:
                        continue
                view = ItemView()
                await intact.edit_original_response(embed=embed, view=view)
                ind = await view.wait()
                if ind:
                    return
                if view.cancel:
                    await intact.delete_original_response()
                    return
                view = CancelButton()
                select = BasicSelect(options=itemoptions, placeholder="Select an Option", max_values=1)
                view.add_item(select)
                await intact.edit_original_response(view=view)
                i = 0
                while not select.selected and not view.cancel:
                    await sleep(1)
                    i+=1
                    if i >= 100:
                        await intact.delete_original_response()
                        return
                if view.cancel:
                    await intact.delete_original_response()
                    return
                while True:
                    view = CancelorBack()
                    x = ITEMS[select.selection]
                    try:
                        embed = Embed(color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]], title=f"Item Details for: {select.selection}", description=f"Cost:`{x['Cost']}`\nLimit: `{x['Limit']}`\nCooldown: `{x['Cooldown']}` Hours per Purchase\nCoupons? `{x['Coupons?']}`")
                    except:
                        embed = Embed(color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]], title=f"Item Details for: {select.selection}", description=f"Limit: `{x['Limit']}`\nCooldown: `{x['Cooldown']}` Hours per Purchase\nCoupons? `{x['Coupons?']}`")
                        for op in x["Options"]:
                            y = x['Options'][op]
                            if cfg.serverid_to_name[str(intact.guild_id)] in y["Division"] or "All" in y["Division"]:
                                embed.add_field(name=op,value=f"Cost: `{y['Cost']}`\nAvailable to Divisions: `{div_frmt(y['Division'])}`")
                    await intact.edit_original_response(embed=embed, view=view)
                    ind = await view.wait()
                    if ind:
                        intact.delete_original_response()
                        return
                    if view.back:
                        break
                    if view.cancel:
                        await intact.delete_original_response()
                        return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Shopitems {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Shopitems {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

    print(f"{cfg.logstamp()}[Setup]{cfg.Success} Shopitems command group setup complete")