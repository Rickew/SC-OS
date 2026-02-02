from python.helpers import exportSheetData, get_local_path, discord_to_username, send_dm
from discord import Interaction, app_commands, Embed, Member
from python.uiclasses import InactivityNotice, InacApprDeny
from traceback import format_exc
from datetime import datetime
import data.config as cfg
from json import load
import inspect

now = datetime.now

COMMAND_NAME = "inactivity"

GUILD_IDS = [
    588427075283714049, #MF
    653542671100411906, #NTSH
    691298558032478208, #IF
    672480434549948438, #TC
    661593066330914828  #TAG
]

def setup(tree: app_commands.CommandTree):    
    # inactivity group
    inac = app_commands.Group(name="inactivity", description="Quota Management", guild_ids=GUILD_IDS, guild_only=True)
    tree.add_command(inac)

    # Submits an inactivity notice request, or removes it if they have one active, this includes OVERTIME notices.
    # - Global Command
    # - Approval/Denial Support
    # - Server Lock Except for Directorate
    # - Conditional Lock
    @inac.command(name="notice", description="Request an Inactivity Notice, or remove your Active Notice.")
    async def notice(intact: Interaction):
        try:
            print(f"[Inactivity notice] Command ran by {intact.user} in server {intact.guild.name}")

            # resolve comuser
            rostersheets, rosters = exportSheetData()
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except Exception as e:
                await intact.response.send_message(ephemeral=True, embed=Embed(title="Error", description=e, color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                return
            try:
                comuserinfo = rosters[0].members[comuser]
                index = 0
            except:
                try:
                    comuserinfo = rosters[1].members[comuser]
                    index = 1
                except:
                    await intact.response.send_message(ephemeral=True, embed=Embed(title="Error", description="You're not on the roster. Contact an Officer to fix.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
            
            # loading quota settings
            with open(get_local_path("data\\quota.json"), "r") as f:
                quota = load(f)
                f.close()
            interval = quota[cfg.serverid_to_name[str(intact.guild_id)]]['Cycle']['Interval']
            start = quota[cfg.serverid_to_name[str(intact.guild_id)]]['Cycle']['Start']
            userquota = quota[cfg.serverid_to_name[str(intact.guild_id)]][comuserinfo["Rank"]]

            if (index == 0 and cfg.serverid_to_name[str(intact.guild_id)] != "Main Force" and comuserinfo["Rank"] not in ("Commander", "Head Commander", "General")) or (index == 1 and cfg.serverid_to_name[str(intact.guild_id)] == "Main Force"):
                # Server lock except for directorate
                await intact.response.send_message("Use this command in your own server..", ephemeral=True)
                return
            
            elif comuserinfo["Exempt Until"] == "OVERTIME":
                # OVERTIME Handler
                rostersheets[index].update_cell(comuserinfo["Row"], rosters[index].headers["Exempt Until"], "")
                if userquota["Type"] == "Manual":
                    rostersheets[index].update_cell(comuserinfo["Row"], rosters[index].headers["Quota"], "INCOMPLETE")

                if intact.guild_id == cfg.server_ids["Nothing To See Here"]:
                    # NTSH inactivity role
                    try:
                        await intact.user.remove_roles(intact.guild.get_role(777273067511611422))
                    except Exception as e:
                        print(f"[Inactivity notice]{cfg.Error} removing inactivity role from the user.", e)
                        
                # send confimation
                await intact.response.send_message("OVETIME notice removed.", ephemeral=True)
                return
            
            elif comuserinfo["Exempt Until"] != "":
                # Handling a non-empty quota cell
                try:
                    # saving for later
                    date = comuserinfo["Exempt Until"]

                    # found normal date, switch up that cell
                    rostersheets[index].update_cell(comuserinfo["Row"], rosters[index].headers["Exempt Until"], "")

                    if intact.guild_id == cfg.server_ids["Nothing To See Here"]:
                        # NTSH inactivity role
                        try:
                            await intact.user.remove_roles(intact.guild.get_role(777273067511611422))
                        except Exception as e:
                            print(f"[Inactivity notice]{cfg.Error} removing the inactivity role from the user.", e)

                    # Parse potential date into a timestamp
                    intdate = int(datetime.strptime(date, r'%m/%d/%Y').timestamp())

                    if userquota["Type"] == "Manual":
                        # manual type quota, not going to do this unless it's a valid date meaning "EXEMPT would be found in the quota cell"
                        rostersheets[index].update_cell(comuserinfo["Row"], rosters[index].headers["Quota"], "INCOMPLETE")

                    # send confimation for correct date
                    await intact.response.send_message(ephemeral=True, embed=Embed(title="Inactivity Notice Ended Early", description="You have ended your Inactivity Notice Early, if you have not already completed quota, you will be expected to complete it. If you did this by mistake, or if you have special permission to go on OVERTIME, contact an Officer.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                    return
                except:
                    # un-parsable date in cell
                    # send confirmation
                    await intact.response.send_message(ephemeral=True, embed=Embed(title="Warning", description="The date under your Exemption cell on the Roster had a incorrect value, this value has been removed, if you still need to submit an IN, please re-run the command", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                    return
                
            if comuserinfo["Quota"] not in ("COMPLETE") and now().timestamp() > (start + interval/2):
                # if they haven't completed quota and we are midway though the cycle
                await intact.response.send_message(embed=Embed(title="Error", description="You have not completed quota in the current quota cycle, you must complete quota before"), ephemeral=True, color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]])
                return

            # sending a modal for user input
            modal = InactivityNotice(title="Inactivity Notice Request")
            await intact.response.send_modal(modal)
            await modal.wait()

            if modal.proceed:
                try:
                    # parse date
                    intdate = int(datetime.strptime(modal.date.value, r'%m/%d/%Y').timestamp())
                except:
                    # if its not correct
                    await intact.followup.send(embed=Embed(title="Error", description=f"{modal.date.value} is not a valid date. Date input must be mm/dd/yyyy, (i.e. 01/01/1991 - Jan 1st, 1991)", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]), ephemeral=True)
                    return
                if intdate <= now().timestamp():
                    # if its in the past
                    await intact.followup.send(embed=Embed(title="Error", description=f"{modal.date.value} is in the past.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]), ephemeral=True)
                    return
                
                # iterate over the cycles to find the cycle the date is in, then push the final date to the back of that cycle
                finalstamp = quota[cfg.serverid_to_name[str(intact.guild_id)]]['Cycle']['End']
                while finalstamp < intdate:
                    finalstamp += interval
                
                # final dates
                startdate = now()
                endate = datetime.fromtimestamp(finalstamp).strftime(r'%m/%d/%Y')

                # put the embed with approval/denial buttons
                view = InacApprDeny()
                message = await intact.guild.get_channel(cfg.inac_channels[cfg.serverid_to_name[str(intact.guild_id)]]).send(view=view, embed=Embed(title="Inactivity Notice Request", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]).add_field(name="User", value=comuser, inline=False).add_field(name="Start", value=f"{startdate.strftime(r'%m/%d/%Y')}", inline=False).add_field(name="End", value=f"{endate} <t:{finalstamp}:R>", inline=False).add_field(name="Reason", value=modal.reason.value, inline=False))
                await intact.followup.send(f"Inactivity Notice Submitted!\n{message.jump_url}", ephemeral=True)
            return
        except:
            # this is complete overview Error handling, sends cfg.Errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Inactivity {inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[Inactivity {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    

    # Access command for manipulating a users exemption cell, allows the user to remove an exiting OVERTIME or Inactivity Notice, or do a notice for them.
    # - Global Command
    # - Server Lock
    # - Rank Lock 
    @inac.command(name="override", description="Request an Inactivity Notice, or remove your Active Notice.")
    async def override(intact: Interaction, user: Member):
        try:
            print(f"[Inactivity override] Command ran by {intact.user} in server {intact.guild.name}")
            rostersheets, rosters = exportSheetData()

            # comuser resolutino
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except Exception as e:
                await intact.response.send_message(ephemeral=True, embed=Embed(title="Error", description="You're uids are not synced.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                return
            try:
                comuserinfo = rosters[0].members[comuser]
            except:
                try:
                    comuserinfo = rosters[1].members[comuser]
                except:
                    await intact.response.send_message(ephemeral=True, embed=Embed(title="Error", description="You're not on the roster.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                    return
            
            # user resolution
            # determining roster indexs
            try:
                usr = discord_to_username([str(user.id)])[0]
            except Exception as e:
                await intact.response.send_message(ephemeral=True, embed=Embed(title="Error", description="User uids are not synced.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                return
            try:
                userinfo = rosters[0].members[usr]
                index = 0
            except:
                try:
                    userinfo = rosters[1].members[usr]
                    index = 1
                except:
                    await intact.response.send_message(ephemeral=True, embed=Embed(title="Error", description="User not on the roster.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                    return
            
            # loading quota settings
            with open(get_local_path("data\\quota.json"), "r") as f:
                quota = load(f)
                f.close()
            interval = quota[cfg.serverid_to_name[str(intact.guild_id)]]['Cycle']['Interval']
            userquota = quota[cfg.serverid_to_name[str(intact.guild_id)]][userinfo["Rank"]]

            if (index == 0 and cfg.serverid_to_name[str(intact.guild_id)] != "Main Force" ) or (index == 1 and cfg.serverid_to_name[str(intact.guild_id)] == "Main Force"):
                # server locking, no need for directorate exception
                await intact.response.send_message("Use this command in the appropriate server.", ephemeral=True)
                return
            
            elif comuserinfo["Rank"] not in ("Task Force Leader", "Security Major", "Commander", "Head Commander", "General"):
                # rank lock w/o rank resolution because I'm lazy
                await intact.response.send_message("You're not allowed to use this command.", ephemeral=True)
                return
            
            elif userinfo["Exempt Until"] == "OVERTIME":
                # OVERTIME Notice handler
                rostersheets[index].update_cell(userinfo["Row"], rosters[index].headers["Exempt Until"], "")
                if userquota["Type"] == "Manual":
                    rostersheets[index].update_cell(comuserinfo["Row"], rosters[index].headers["Quota"], "INCOMPLETE")

                if intact.guild_id == cfg.server_ids["Nothing To See Here"]:
                    # NTSH inactivity role
                    try:
                        await user.remove_roles(intact.guild.get_role(777273067511611422))
                    except Exception as e:
                        print(f"[Inactivity override]{cfg.Error} removing the role to the user.", e)

                # send confirmation and a log to server logs, also a DM to the user
                await intact.response.send_message("OVETIME notice removed.", ephemeral=True)
                await send_dm(user, content=f"Your OVERTIME Notice in SC, excepting you from quota for this cycle, has been removed, if you believe this is a mistake, please contact an officer.")
                await intact.guild.get_channel(cfg.logchannel_ids[cfg.serverid_to_name[str(intact.guild_id)]]).send(embed=Embed(title="OVERTIME Notice Removed Early", description=f"{user.mention}'s OVERTIME Notice Removed by {intact.user.mention}", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]).set_author(name=f"{comuser} > {user}"))
                return
            elif userinfo["Exempt Until"] != "":
                # Handling a non-empty quota cell
                try:
                    # saving for later
                    date = comuserinfo["Exempt Until"]

                    # found normal date, switch up that cell
                    rostersheets[index].update_cell(comuserinfo["Row"], rosters[index].headers["Exempt Until"], "")

                    if intact.guild_id == cfg.server_ids["Nothing To See Here"]:
                        # NTSH inactivity role
                        try:
                            await intact.user.remove_roles(intact.guild.get_role(777273067511611422))
                        except Exception as e:
                            print(f"[Inactivity notice]{cfg.Error} removing the inactivity role from the user.", e)

                    # Parse potential date into a timestamp
                    intdate = int(datetime.strptime(date, r'%m/%d/%Y').timestamp())

                    if userquota["Type"] == "Manual":
                        # manual type quota, not going to do this unless it's a valid date meaning "EXEMPT would be found in the quota cell"
                        rostersheets[index].update_cell(comuserinfo["Row"], rosters[index].headers["Quota"], "INCOMPLETE")

                    # send confimation for correct date
                    await intact.response.send_message("Inactivity Notice Removed.", ephemeral=True)
                    await send_dm(user, content=f"Your Inactivity Notice in SC, has been removed, if you believe this is a mistake, please contact an officer.")
                    await intact.guild.get_channel(cfg.logchannel_ids[cfg.serverid_to_name[str(intact.guild_id)]]).send(embed=Embed(title="Inactivity Notice Removed Early", description=f"{user.mention}'s Inactivity Notice Removed by {intact.user.mention}", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]).set_author(name=f"{comuser} > {user}"))
                except:
                    # un-parsable date in cell
                    # send confirmation
                    await intact.response.send_message(ephemeral=True, embed=Embed(title="Warning", description="The date under that users Exemption cell on the Roster had a incorrect value, this value has been removed, if you still need to override their IN, please re-run the command", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]))
                return
            
            # sending a modal for user input
            modal = InactivityNotice(title="Inactivity Notice Request")
            await intact.response.send_modal(modal)
            await modal.wait()

            if modal.proceed:
                try:
                    # parse date
                    intdate = int(datetime.strptime(modal.date.value, r'%m/%d/%Y').timestamp())
                except:
                    # if its not correct
                    await intact.followup.send(embed=Embed(title="Error", description=f"{modal.date.value} is not a valid date. Date input must be mm/dd/yyyy, (i.e. 01/01/1991 - Jan 1st, 1991)", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]), ephemeral=True)
                    return
                if intdate <= now().timestamp():
                    # if its in the past
                    await intact.followup.send(embed=Embed(title="Error", description=f"{modal.date.value} is in the past.", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]), ephemeral=True)
                    return
                
                # iterate over the cycles to find the cycle the date is in, then push the final date to the back of that cycle
                finalstamp = quota[cfg.serverid_to_name[str(intact.guild_id)]]['Cycle']['End']
                while finalstamp < intdate:
                    finalstamp += interval
                
                # final dates
                startdate = now()
                endate = datetime.fromtimestamp(finalstamp).strftime(r'%m/%d/%Y')
                
                # updating cell
                rostersheets[index].update_cell(userinfo["Row"], rosters[index].headers["Exempt Until"], endate)
                if userquota["Type"] == "Manual":
                    # handling manual type quota
                    rostersheets[index].update_cell(comuserinfo["Row"], rosters[index].headers["Quota"], "EXEMPT")

                if intact.guild_id == cfg.server_ids["Nothing To See Here"]:
                    # NTSH inactivity role
                    try:
                        await user.add_roles(intact.guild.get_role(777273067511611422))
                    except Exception as e:
                        print(f"[Inactivity override]{cfg.Error} giving the role to the user.", e)
                
                # send log and dm
                await send_dm(user, content=f"An Inactivity Notice has been submitted on your behalf by an officer, if you believe this to be a mistake, you can remove it yourself by useing the `/inactivity notice` command.")
                await intact.guild.get_channel(cfg.logchannel_ids[cfg.serverid_to_name[str(intact.guild_id)]]).send(embed=Embed(title="Inactivity Notice Request", description=f"Inactivity Notice Submitted by {intact.user.mention} for {user.mention}", color=cfg.embedcolors[cfg.serverid_to_name[str(intact.guild_id)]]).add_field(name="User", value=usr, inline=False).add_field(name="Start", value=f"{startdate.strftime(r'%m/%d/%Y')}", inline=False).add_field(name="End", value=f"{endate} <t:{finalstamp}:R>", inline=False).add_field(name="Reason", value=modal.reason.value, inline=False).set_author(name=f"{comuser} > {user}"))
            return
        except:
            # this is complete overview Error handling, sends cfg.Errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][Inactivity {inspect.currentframe().f_code.co_name}]", description=format_exc(2)))
            print(f"[Inactivity {inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)

    print(f"[Setup]{cfg.Success} Inactivity command group setup complete")
