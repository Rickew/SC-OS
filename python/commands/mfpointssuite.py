from discord import Interaction, app_commands, Embed, Member, Object
from python.helpers import discord_to_username, get_scgroup_rank
from traceback import format_exc
from gspread import Worksheet
import data.config as cfg
import inspect

COMMAND_NAME = "points"

GUILD_IDS = [
    588427075283714049
]

def get_catergories(roster: Worksheet):
    rowvals = roster.row_values(1)
    while True:
        try:
            rowvals.remove('')
        except:
            break
    while rowvals[-1] != "Total Points":
        rowvals.pop(-1)
    rowvals.pop(-1)

    while rowvals[0] != "Rank":
        rowvals.pop(0)
    rowvals.pop(0)
    return rowvals

def setup(tree: app_commands.CommandTree):
    points = app_commands.Group(name="points", description="Edit points in categories for NCO's and CO's.", guild_ids=GUILD_IDS, guild_only=True)
    tree.add_command(points)
    NCOcats = get_catergories(cfg.NCOroster)
    NCOoptions = [app_commands.Choice(name=x, value=NCOcats.index(x)+1) for x in NCOcats]
    COcats = get_catergories(cfg.COroster)
    COoptions = [app_commands.Choice(name=x, value=COcats.index(x)+1) for x in COcats]
    

    # This command allows the editing of points for an NCO on the Roster.
    # - Server Locked (Main SC)
    # - Rank Locked
    @points.command(name="nco", description="Edit the points value of an MF NCO or Officer on the Roster.")
    @app_commands.describe(user="The user who's points you want to edit.")
    @app_commands.describe(category="The category of event/task you're editing.")
    @app_commands.describe(addsub="Select to add or subtract points.")
    @app_commands.describe(amount="The amount you want to add/subtract. Can be in decimals for half credit of a task.")
    @app_commands.choices(addsub=[app_commands.Choice(name="Add", value=1), app_commands.Choice(name="Subtract", value=2)])
    @app_commands.choices(category=NCOoptions)
    async def nco(intact: Interaction, user: Member, category: app_commands.Choice[int], addsub:app_commands.Choice[int], amount: float):
        try:
            print(f"{cfg.logstamp()}[Points nco] command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="Your uids are not syced."))
                return
            rank = get_scgroup_rank([comuser])[comuser]['rank']
            if rank < 8: 
                await intact.followup.send("You're not allowed to run this command.")
                return
            try:
                usr = discord_to_username([str(user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="User uids are not syced."))
                return
            cell = cfg.NCOroster.find(usr, in_column=1)
            if not cell:
                await intact.followup.send(embed=Embed(title="Error", description="User is not on the NCO Roster."))
                return
            headercell = cfg.NCOroster.find(category.name, in_row=1)
            if not headercell:
                await intact.followup.send(embed=Embed(title="Error", description="Category Issue."))
                return
            if addsub.value == 2:
                amount = 0.0-amount
            totalpoints = cfg.NCOroster.cell(cell.row, cfg.NCOroster.find("Total Points", in_row=1).col)
            val = float(cfg.NCOroster.cell(cell.row, headercell.col).value)
            cfg.NCOroster.update_cell(cell.row, headercell.col, val+amount)
            newtotal = cfg.NCOroster.cell(totalpoints.row, totalpoints.col)
            await intact.followup.send(embed=Embed(title="NCO Roster Points Changed", color=cfg.embedcolors["Main Force"]).add_field(name="Catergory", value=category.name).add_field(name="Amount", value=f"{val} -> {val+amount}").add_field(name="Total Points", value=f"{totalpoints.value} -> {newtotal.value}"))
            await intact.guild.get_channel(cfg.logchannel_ids["Main Force"]).send(embed=Embed(title="NCO Roster Points Changed", description=f"Points changed for {user.mention} by {intact.user.mention}", color=cfg.embedcolors["Main Force"]).add_field(name="Catergory", value=category.name).add_field(name="Amount", value=f"{val} -> {val+amount}").add_field(name="Total Points", value=f"{totalpoints.value} -> {newtotal.value}").set_author(name=f"{comuser} > {user}"))
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Points {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Points {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
        

    # This command allows the editing of points for an officer on the Roster.
    # - Server Locked (Main SC)
    # - Rank Locked
    @points.command(name="officer", description="Edit the points value of an MF NCO or Officer on the Roster.")
    @app_commands.describe(user="The user who's points you want to edit.")
    @app_commands.describe(category="The category of event/task you're editing.")
    @app_commands.describe(addsub="Select to add or subtract points.")
    @app_commands.describe(amount="The amount you want to add/subtract. Can be in decimals for half credit of a task.")
    @app_commands.choices(addsub=[app_commands.Choice(name="Add", value=1), app_commands.Choice(name="Subtract", value=2)])
    @app_commands.choices(category=COoptions)
    async def officer(intact: Interaction, user: Member, category: app_commands.Choice[int], addsub:app_commands.Choice[int], amount: float):
        try:
            print(f"Points Officer Command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="Your uids are not syced."))
                return
            rank = get_scgroup_rank([comuser])[comuser]['rank']
            if rank < 9: 
                await intact.followup.send("You're not allowed to run this command.")
                return
            try:
                usr = discord_to_username([str(user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="User uids are not syced."))
                return
            cell = cfg.COroster.find(usr, in_column=1)
            if not cell:
                await intact.followup.send(embed=Embed(title="Error", description="User is not on the Officer Roster."))
                return
            headercell = cfg.COroster.find(category.name, in_row=1)
            if not headercell:
                await intact.followup.send(embed=Embed(title="Error", description="Category Issue."))
                return
            if addsub.value == 2:
                amount = 0.0-amount
            totalpoints = cfg.COroster.cell(cell.row, cfg.COroster.find("Total Points", in_row=1).col)
            val = float(cfg.COroster.cell(cell.row, headercell.col).value)
            cfg.COroster.update_cell(cell.row, headercell.col, val+amount)
            newtotal = cfg.COroster.cell(totalpoints.row, totalpoints.col)
            await intact.followup.send(embed=Embed(title="CO Roster Points Changed", color=cfg.embedcolors["Main Force"]).add_field(name="Catergory", value=category.name).add_field(name="Amount", value=f"{val} -> {val+amount}").add_field(name="Total Points", value=f"{totalpoints.value} -> {newtotal.value}"))
            await intact.guild.get_channel(cfg.logchannel_ids["Main Force"]).send(embed=Embed(title="CO Roster Points Changed", description=f"Points changed for {user.mention} by {intact.user.mention}", color=cfg.embedcolors["Main Force"]).add_field(name="Catergory", value=category.name).add_field(name="Amount", value=f"{val} -> {val+amount}").add_field(name="Total Points", value=f"{totalpoints.value} -> {newtotal.value}").set_author(name=f"{comuser} > {user}"))
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Points {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Points {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

        
    # View the points of an NCO or Officer.
    # - Server Locked (Main SC)
    # - Rank Locked
    @points.command(name="view", description="View the points of an NCO or Officer.")
    @app_commands.describe(user="The user who's points you want to view.")
    async def view(intact: Interaction, user: Member = None):
        try:
            print(f"Points View Command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            if user:
                try:
                    usr = discord_to_username([str(user.id)])[0]
                except:
                    await intact.followup.send(embed=Embed(title="Error", description="User uids are not syced."))
                    return
            else:
                try:
                    usr = discord_to_username([str(intact.user.id)])[0]
                except:
                    await intact.followup.send(embed=Embed(title="Error", description="Your uids are not syced."))
                    return
                
            cell = cfg.NCOroster.find(usr, in_column=1)
            roster = cfg.NCOroster
            if not cell:
                cell = cfg.COroster.find(usr, in_column=1)
                roster = cfg.COroster
            if not cell:
                await intact.followup.send(embed=Embed(title="Error", description="You are not / User is not on the NCO or Officer Roster."))
                return
            values = roster.row_values(cell.row)
            categories = get_catergories(roster)
            categories.append("Total Points")
            while True:
                try:
                    float(values[0])
                    break
                except:
                    values.pop(0)
            while True:
                try:
                    float(values[-1])
                    break
                except:
                    values.pop(-1)
            embed = Embed(title=f"{usr}'s Points by Category", color=cfg.embedcolors["Main Force"])
            for i in range(0, len(categories)):
                embed.add_field(name=categories[i], value=values[i])
            for i in range(len(categories)%3, 3):
                embed.add_field(name="⠀", value="⠀")
            await intact.followup.send(embed=embed)
            return
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Points {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Points {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)


    # Refresh the Catergories for NCO and CO Roster.
    # - Server Locked (Main SC)
    # - Rank Locked
    @points.command(name="refresh", description="Refresh the Catergories for NCO and CO Roster.")
    async def refresh(intact: Interaction):
        try:
            print(f"Points View Command ran by {intact.user} in {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="Your uids are not syced."))
                return
            rank = get_scgroup_rank([comuser])[comuser]['rank']
            if rank < 10: 
                await intact.followup.send("You're not allowed to run this command.")
                return

            for gid in GUILD_IDS:
                tree.remove_command("points",guild=Object(id=gid))
                tree.sync(guild=Object(id=gid))
                print("✅ Points Command Group Cleared")
                setup(tree)
                print("✅ Points Command Group Re-Setup Complete")

            # command resync
            for gid in GUILD_IDS:
                await tree.sync(guild=Object(id=gid))
                print(f"✅ Re-Synced guild commands for {gid}: {tree.client.get_guild(gid).name}")
            await intact.followup.send("Done!")
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Points {inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[Points {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

    print(f"{cfg.logstamp()}[Setup]{cfg.Success} Points command group setup complete")