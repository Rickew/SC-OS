from python.helpers import exportSheetData, discord_to_username, get_scgroup_rank, send_dm
from discord import Interaction, app_commands, Embed, Guild, Member
from traceback import format_exc
import data.config as cfg
import inspect

ITEMS = {}

COMMAND_NAME = "strike"

GUILD_IDS = [
    588427075283714049, #MF
    653542671100411906, #NTSH
    691298558032478208, #IF
    672480434549948438, #TC
    661593066330914828  #TAG
]

def setup(tree: app_commands.CommandTree, guild: Guild):
    # Increases the strikes a user has on the roster. Sends a DM to that user informing them of the strike. Replies to the log_link with a confirmation.
    # - Global Command
    # - Channel Locked
    # - Rank Locked
    @tree.command(name="strike", description="Strike someone.", guild=guild)
    @app_commands.describe(user="Discord mention of the user you want to strike.")
    @app_commands.describe(log_link="The message link to the punishment log.")
    async def strike(intact: Interaction, user: Member, log_link: str):
        try:
            print(f"{cfg.logstamp()}[strike] command used by {intact.user} in server: {intact.guild.name}")
            await intact.response.defer(thinking=True, ephemeral=True)
            rostersheets, rosters = exportSheetData()

            # comuser resolution
            try:
                comuser = discord_to_username([str(intact.user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="Your uids are not synced", color=cfg.embedcolors[division]))
            
            # rank lock
            rank = get_scgroup_rank([comuser])[comuser]['rank']
            if rank < 8:
                await intact.followup.send("You're not allowed to use this command.")
                return

            # check to see if the message link is a message from the punishment channel in that division
            try:
                # get division
                division = cfg.serverid_to_name[str(intact.guild_id)]
                if intact.channel.id == cfg.punishment_channels[division]:
                    message = await intact.channel.fetch_message(int(log_link.split("/")[-1]))
                else:
                    raise Exception("e")
            except Exception as e:
                await intact.followup.send(embed=Embed(title="Error", description=f"Message link: {log_link} is not valid."))
                return

            # user resolution
            try:
                usr = discord_to_username([str(user.id)])[0]
            except:
                await intact.followup.send(embed=Embed(title="Error", description="User's uids are not synced", color=cfg.embedcolors[division]))
                return
            try:
                index = 0
                userinfo = rosters[index].members[usr]
            except:
                try:
                    index = 1
                    userinfo = rosters[index].members[usr]
                except:
                    await intact.followup.send(embed=Embed(title="Error", description="User not on Roster.", color=cfg.embedcolors[division]))
                    return
            
            # NTSH is special and wants their automatic discord removal as 2 strikes
            if int(userinfo["Punishments"]) + 1 == 2 and division == "Nothing To See Here":
                for role in user.roles:
                    try:
                        if ("Medal", "Star", "Finest") not in role.name:
                            await user.remove_roles(role.id)
                    except:
                        print(f"{cfg.logstamp()}[strike]{cfg.Error} removing role \"{role.name}\" from {user}:", e)
                try:
                    await user.add_roles(user.guild.get_role(773221920485015552))
                except Exception as e:
                    print(f"{cfg.logstamp()}[strike]{cfg.Error} adding veteran role to {user}:", e)
            elif division == "Nothing To See Here":
                try:
                    await user.add_roles(intact.guild.get_role(759756623484289044))
                except Exception as e:
                    print(f"{cfg.logstamp()}[strike]{cfg.Error} adding striked role to {usr}", e)
            
            # embed creation
            embed = Embed(title=f"Strike Given", description=f"Strike given to {user.mention} by {intact.user.mention}", color=cfg.embedcolors[division])
            
            # increase number on roster
            rostersheets[index].update_cell(userinfo["Row"], rosters[index].headers["Punishments"], int(userinfo["Punishments"]) + 1)

            # reply to log message
            await message.reply(embed=embed,mention_author=False)

            # send user a dm about it
            ind = await send_dm(user, message, content=f"You have been given a strike in {division}. If you feel this is unjust you may contact an officer from {division} about it. Log listed below.")
            
            # final confirmation message to comuser
            if not ind:
                await intact.followup.send("Done, but I was unable to send a DM to the user to inform them of their strike.")
            else:
                await intact.followup.send("Done, User has a recieved a DM notice about their strike.")
        except:
            # this is complete overview Error handling, sends errors to testing server
            i = await tree.client.get_guild(926850392271241226).get_channel(1308928443974684713).send(embed=Embed(title=f"[Error][{inspect.currentframe().f_code.co_name}]", description=format_exc(5)))
            print(f"{cfg.logstamp()}[{inspect.currentframe().f_code.co_name}]{cfg.Error}", i.jump_url)
    
    print(f"{cfg.logstamp()}[Setup]{cfg.Success} strike command setup complete for Guild: {guild.id}")
    