from discord import Interaction, app_commands, Guild
from discord import app_commands, Message
import json
import data.config as cfg

COMMAND_NAME = "update"

GUILD_IDS = [
    588427075283714049, #MF
    653542671100411906, #NTSH
    691298558032478208, #IF
    672480434549948438, #TC
    661593066330914828  #TAG
]

def setup(tree: app_commands.CommandTree, guild: Guild):
    # interacts with google sheet
    # input is a list of users from disord, and the amount of honor they get
    @tree.command(name="update", description="Update the outdated bot", guild=guild)
    async def update(intact: Interaction, test: str):
        print(f"Update Command ran by {intact.user} in {intact.guild.name}")
        # channel = intact.guild.get_channel(1263167899116372131)
        # message: Message = [message async for message in channel.history(limit=1, oldest_first=False)][0]
        # print(json.dumps(message.embeds[0].to_dict(), indent=2))
        await intact.response.send_message("Done!", ephemeral=True)