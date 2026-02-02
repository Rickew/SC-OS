from python.helpers import discord_to_username, get_local_path, get_scgroup_rank
from discord import Interaction, app_commands, Embed, Guild
from traceback import format_exc
from datetime import datetime
import data.config as cfg
from re import findall
import json
import random
import string
import inspect

COMMAND_NAME = "coupon"

GUILD_IDS = [
    588427075283714049
]

ITEMS = {}

def setup(tree: app_commands.CommandTree, guild: Guild):
    def load_options():
        with open(get_local_path("data\\shopitems.json"), "r") as f:
            items = json.load(f)
            f.close()
        options = []
        x = 1
        for item in items:
            try:
                if items[item]['Coupons?']:
                    ITEMS.update({item : items[item]})
                    options.append(app_commands.Choice(name=item, value=x))
                    x+=1
                    continue
            except:
                None
        return options

    def generate_coupon():
        chars = string.ascii_letters  # A–Z + a–z

        part1 = ''.join(random.choice(chars) for _ in range(5))
        part2 = ''.join(random.choice(chars) for _ in range(5))
        part3 = ''.join(random.choice(chars) for _ in range(5))

        return f"{part1}-{part2}-{part3}"
    
    # This command can create a coupon for 1 or more SC to use in the Honor Shop
    # - Main SC Server Locked
    # - Rank Locked
    @tree.command(name="coupon", description="Give a coupon to 1 or more SC", guild=guild)
    @app_commands.choices(item=load_options())
    @app_commands.choices(discount=[app_commands.Choice(name="10%",value=10),
                                app_commands.Choice(name="15%",value=15),
                                app_commands.Choice(name="20%",value=20),
                                app_commands.Choice(name="25%",value=25),
                                app_commands.Choice(name="30%",value=30),
                                app_commands.Choice(name="35%",value=35),
                                app_commands.Choice(name="40%",value=40)])
    @app_commands.describe(item="The item you want to make a coupon for.")
    @app_commands.describe(discount="The discount you want to apply to the coupon")
    @app_commands.describe(users="The users you want to give the coupon to.")
    async def coupon(intact: Interaction, item: app_commands.Choice[int], discount: app_commands.Choice[int], users: str):
        try:
            print(f"[coupon] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="You're not on the Roster."))
            rank = get_scgroup_rank([comuser])[comuser]['rank']
            if rank < 8:
                await intact.followup.send("You're not allowed to run this command.")
            with open(get_local_path("data\\coupons.json"), "r") as f:
                coupons = json.load(f)
                f.close()
            while True:
                couponname = generate_coupon()
                try:
                    coupons["Coupons"][item.name][couponname]
                    continue
                except:
                    break
            try:
                resultsembed = Embed(title="Errors")

                # parse uids
                uidinput: list[str] = findall(r'<@\d+>',users)
                temp = uidinput.copy()
                uids = []
                for uid in temp:
                    uids.append(uid.replace("@", "").replace("<", "").replace(">", ""))
                # parse uids into Roblox usernames
                users = discord_to_username(uids)
                temp = uids.copy()
                for i in range(0, len(users)):
                    if "Error" in users[i]:
                        resultsembed.add_field(name="UID Error", value=f"User \"<@{temp[i]}>\" not on roster")
                        uids.remove(str(temp[i]))
                        continue
                if len(uids) > 0:
                    try:
                        coupons["Coupons"][item.name].update({couponname : {"issuedto" : uids, "issuedby" : f"{comuser} - <@{intact.user.id}>", "issuedon" : int(datetime.now().timestamp()), "Discount" : float(discount.value)/100.0}})
                    except:
                        coupons["Coupons"].update({item.name : {couponname : {"issuedto" : uids, "issuedby" : f"{comuser} - <@{intact.user.id}>", "issuedon" : int(datetime.now().timestamp()), "Discount" : float(discount.value)/100.0}}})
                else:
                    await intact.followup.send("Done!")
                    return
            except:
                resultsembed.add_field(name="UID Error", value=f"User \"<@{uids[0]}>\" not on roster")
            with open(get_local_path("data\\coupons.json"), "w") as f:
                json.dump(coupons, f, indent=2)
                f.close()
            finalembeds = [Embed(title="Coupon Created", description=f"**Coupon Tag:**\n{couponname}").add_field(name="Issued To", value=str(uidinput).strip("[]").replace("'", ""), inline=False).add_field(name="Discount", value=discount.name, inline=False).add_field(name="For Item", value=item.name, inline=False).add_field(name="Issued By", value=f"{comuser} - <@{intact.user.id}>", inline=False).set_author(name=comuser)]
            await intact.guild.get_channel(588438540090736657).send(embeds=finalembeds)
            if len(resultsembed.fields) > 0:
                finalembeds.append(resultsembed)
            await intact.followup.send("Done", embeds=finalembeds)
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][{inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[{inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

    print(f"[Setup]{cfg.Success} Coupon command setup complete for Guild: {guild.id}")