from discord import Interaction, app_commands, Embed, Member, File
from python.helpers import exportSheetData, discord_to_username, single_UID_sync, idrostersanitize, get_scgroup_rank, trello_class_e_search, rotector_check
from requests import get, post
import data.config as cfg
from roblox import Client
import roblox
from datetime import datetime as dt
import threading
from python.badgegraph import process_user, get_local_path



def setup(tree: app_commands.CommandTree):
    None