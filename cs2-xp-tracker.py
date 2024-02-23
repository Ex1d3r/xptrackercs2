from config import *
from csgo.client import CSGOClient
from csgo.enums import ECsgoGCMsg
from DiscordWebhook import DiscordWebhook, DiscordEmbed
from steam import client
from steam import guard
from steam.client import SteamClient
from steam.steamid import SteamID
from TrackedUsers import TrackedUsers
from TrackingList import TrackingList
import base64
import csgo
import dataclasses
import datetime
import gevent
import os
import requests
import time

steam_client = SteamClient()
csgo_client = CSGOClient(steam_client)
tracking_list = TrackingList(TRACKING_LIST_PATH)
tracked_users = TrackedUsers()

webhook = DiscordWebhook(DISCORD_UPDATE_WEBHOOK)

checking_loop_running = False

def steam_cli_input_patched_for_retry(message):
	if message == "Steam is down. Keep retrying? [y/n]: ":
		print(f"steam_cli_input_patched_for_retry(): Steam is down, automatically answering yes to retry question.")
		return "y"
	return input(message)

client._cli_input = steam_cli_input_patched_for_retry

def steam_login():
	global SHARED_SECRET

	print(f"Logging in to Steam as {STEAM_USERNAME}")

	if steam_client.logged_on: 
		return

	if not os.path.exists(CREDENTIALS_LOCATION):
		os.makedirs(CREDENTIALS_LOCATION)
	steam_client.set_credential_location(CREDENTIALS_LOCATION)

	if steam_client.relogin_available: 
		steam_client.relogin()
	elif steam_client.login_key is not None: 
		steam_client.login(username=STEAM_USERNAME, login_key=steam_client.login_key)
	else:
		if SHARED_SECRET is None:
			steam_client.cli_login(username=STEAM_USERNAME, password=STEAM_PASSWORD)
		else:
			two_factor_code = guard.generate_twofactor_code(base64.b64decode(SHARED_SECRET))
			steam_client.login(username=STEAM_USERNAME, password=STEAM_PASSWORD, two_factor_code=two_factor_code)

			if not steam_client.logged_on:
				SHARED_SECRET = None
				print(f"Login with shared secret didn't work.")
				steam_client.cli_login(username=STEAM_USERNAME, password=STEAM_PASSWORD)

def launch_csgo():
	if csgo_client.connection_status == csgo.enums.GCConnectionStatus.NO_SESSION:
		steam_login()
		csgo_client.launch()

@dataclasses.dataclass
class CSGOProfile:
	level: int
	xp: int
	medals: [int]

def get_user_level_and_xp(steam_id):
	launch_csgo()

	inspect_params = { "account_id": SteamID(steam_id).as_32, "request_level": 32 }
	csgo_client.send(ECsgoGCMsg.EMsgGCCStrike15_v2_ClientRequestPlayersProfile, inspect_params)
	response = csgo_client.wait_event(ECsgoGCMsg.EMsgGCCStrike15_v2_PlayersProfile, timeout=5)

	if response is None:
		raise Exception("CS:GO sent an empty response.")

	profile = response[0].account_profiles[0]
	csgo_profile = CSGOProfile(
		profile.player_level,
		max(0, profile.player_cur_xp - 327680000),
		list(profile.medals.display_items_defidx)
	)
	return csgo_profile

def get_user_name_and_avatar(steam_id, api_key):
	if DISABLE_STEAM_API:
		raise Exception("Steam API is disabled")

	params = {
		"key": api_key,
		"steamids": steam_id
	}

	response = requests.get("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/", params=params)
	response.raise_for_status()

	json = response.json()
	for player in json["response"]["players"]:
		if player["steamid"] != str(steam_id):
			continue
		return player["personaname"], player["avatarfull"]

	raise Exception(f"Could't find {steam_id} in response.")

def calculate_difference(now, previous, _max):
	difference = now - previous
	if difference < 0:
		difference += _max
	return difference

def get_medal_info(medals):
	for medal_id in medals:
		if medal_id in MEDAL_TIER_EMOJIS:
			return MEDAL_TIER_EMOJIS[medal_id]

	return NO_MEDAL_EMOJI

def user_xp_changed(tracked_user, medals):
	if tracked_user.first_check:
		print(f"First change for {tracked_user.steam_id}. Not sending message.")
		return

	print(f"Change for {tracked_user.steam_id}. Sending message.")

	username = f"`{tracked_user.steam_id}`"
	avatar = ""

	try:
		username, avatar = get_user_name_and_avatar(tracked_user.steam_id, STEAM_API_KEY)
	except Exception as e:
		print(f"Could't get username and avatar for {tracked_user.steam_id}: {e}")
		pass

	medal_emoji, medal_color = get_medal_info(medals)

	embed = DiscordEmbed()
	embed.set_title(f"XP Tracker | {username}")
	embed.set_url(f"https://steamcommunity.com/profiles/{tracked_user.steam_id}")
	embed.set_thumbnail(avatar)
	embed.set_timestamp(datetime.datetime.utcnow().isoformat())
	arr = ["", "<:Csgoranklevel1:1138864063410081842>", "<:Csgoranklevel2:1138864074826989619>", "<:Csgoranklevel3:1138864084855570545>", "<:Csgoranklevel4:1138864098516406352>", "<:Csgoranklevel5:1138864108926681119>", "<:Csgoranklevel6:1138864123346681896>", "<:Csgoranklevel7:1138864139947749496>", "<:Csgoranklevel8:1138864154162241606>", "<:Csgoranklevel9:1138864167588212767>", "<:Csgoranklevel10:1138864180229853227>", "<:Csgoranklevel11:1138864194394013736>", "<:Csgoranklevel12:1138864209665470534>", "<:Csgoranklevel13:1138864219916337192>", "<:Csgoranklevel14:1138864230230134946>", "<:Csgoranklevel15:1138864244557889626>", "<:Csgoranklevel16:1138864257283407874>", "<:Csgoranklevel17:1138864313440927836>", "<:Csgoranklevel18:1138864323654070403>", "<:Csgoranklevel19:1138864335331012780>", "<:Csgoranklevel20:1138864351336472756>", "<:Csgoranklevel21:1138864362375892992>", "<:Csgoranklevel22:1138864375348867263>", "<:Csgoranklevel23:1138864395271798895>", "<:Csgoranklevel24:1138864407263326228>", "<:Csgoranklevel25:1138864417761660969>", "<:Csgoranklevel26:1138864427911889077>", "<:Csgoranklevel27:1138864440847114310>", "<:Csgoranklevel28:1138864451848781864>", "<:Csgoranklevel29:1138864468625993831>", "<:Csgoranklevel30:1138864480663650396>", "<:Csgoranklevel31:1138864492567072880>", "<:Csgoranklevel32:1138864511449825351>", "<:Csgoranklevel33:1138864524322164787>", "<:Csgoranklevel34:1138864538024943667>", "<:Csgoranklevel35:1138864546853961870>", "<:Csgoranklevel36:1138864557146787940>", "<:Csgoranklevel37:1138864566760112138>", "<:Csgoranklevel38:1138864585093431458>", "<:Csgoranklevel39:1138864597307232317>", "<:Csgoranklevel40:1138864608736722976>"]

	if tracked_user.xp != tracked_user.previous_xp:
		XP_PER_LEVEL = 5000
		xp_difference = calculate_difference(tracked_user.xp, tracked_user.previous_xp, XP_PER_LEVEL)
		embed.add_field(name="", value=f"<:XP:948817713336299592> **Gained: {xp_difference:+} XP**\n<a:senko_hi:1126862720646533230>  **Progress: {tracked_user.xp}/5,000 XP** \n<:LVL:948817713260789790> **Need {XP_PER_LEVEL - tracked_user.xp} XP for next level**")
	else:
		embed.add_field(name="XP (unchanged)", value=f"Now: *{tracked_user.xp}*")

	if tracked_user.level != tracked_user.previous_level:
		level_difference = calculate_difference(tracked_user.level, tracked_user.previous_level, 40)
	
	embed.add_field(name="", value=f"{medal_emoji} **{medal_color} Medal**\n{arr[tracked_user.level]} **Rank: {tracked_user.level}/40**")

	embed.set_footer(f"discord.gg/XePnsNzB | {username} played {tracked_user.matches} match(es)", icon_url="https://cdn.discordapp.com/attachments/1094711830271754342/1138540641752727692/scs_edit006WindowsIcon.png")

	webhook.send(embed=embed)

def check_user(steam_id):
	tracked_user = tracked_users.find_tracked_user_by_steam_id(steam_id)

	try:
		csgo_profile = get_user_level_and_xp(tracked_user.steam_id)
	except Exception as e:
		print(f"Couldn't get level and XP for {tracked_user.steam_id}: {e}")
		return

	print(f"Got profile for {steam_id}: {csgo_profile}")
	tracked_user.update_level_and_xp(csgo_profile.level, csgo_profile.xp, user_xp_changed, csgo_profile.medals)

def get_tracking_list_difference():
	old_tracking_list = tracking_list.get_tracking_list()
	tracking_list.read_tracking_list_from_file()
	new_tracking_list = tracking_list.get_tracking_list()

	tracking_added = [steam_id for steam_id in new_tracking_list if steam_id not in old_tracking_list]
	tracking_removed = [steam_id for steam_id in old_tracking_list if steam_id not in new_tracking_list]
	return tracking_added, tracking_removed

def send_tracking_list_difference_if_needed(tracking_added, tracking_removed):
	if not SEND_TRACKING_LIST_UPDATES:
		return

	if len(tracking_added) == 0  and len(tracking_removed) == 0:
		print(f"No difference in tracking list.")
		return

	print(f"Tracking list difference: {len(tracking_added)=} {len(tracking_removed)=}")

	embed = DiscordEmbed()
	embed.set_title("XP Tracker users changed")

	if len(tracking_added):
		steam_ids_list = "\n".join(tracking_added)
		embed.add_field(name="Users Added", value=f"```{steam_ids_list}```")

	if len(tracking_removed):
		steam_ids_list = "\n".join(tracking_removed)
		embed.add_field(name="Users Removed", value=f"```{steam_ids_list}```")

	embed.set_timestamp(datetime.datetime.utcnow().isoformat())
	webhook.send(embed=embed)

def check_users():
	global checking_loop_running

	if checking_loop_running:
		return

	checking_loop_running = True

	while True:
		tracking_added, tracking_removed = get_tracking_list_difference()
		send_tracking_list_difference_if_needed(tracking_added, tracking_removed)

		for steam_id in tracking_list.get_tracking_list():
			print(f"Checking {steam_id}")
			check_user(steam_id)

		print(f"Next check in {CHECK_TIMEOUT} seconds.")
		gevent.sleep(CHECK_TIMEOUT)

@steam_client.on("logged_on")
def steam_client_logged_on():
	print("Steam client logged on")
	csgo_client.launch()

@csgo_client.on("ready")
def csgo_client_ready():
	print("CS:GO client ready")

	embed = DiscordEmbed()
	embed.set_title("XP Tracker started")
	embed.add_field(name="Users", value=f"Tracking {len(tracking_list.get_tracking_list())} user(s)")
	embed.add_field(name="Checking", value=f"Checking every {CHECK_TIMEOUT} seconds")
	embed.set_timestamp(datetime.datetime.utcnow().isoformat())

	check_users()

def do_first_setup():
	global tracking_list
	if os.path.exists(TRACKING_LIST_PATH):
		return

	print("This seems to be your first time launching the program.")

	setup_tracking_list = input("Do you want to set up the tracking list now? [Y/n] ") in ("Y", "y")
	if not setup_tracking_list:
		print(f"Okay. Resuming execution as normal")
		return

	print("Enter a Steam ID to start tracking or enter \"save\" to save tracking list and continue.")

	temp_tracking_list = []
	save = False

	while not save:
		steamid_to_add = input("Steam ID to add: ")
		if steamid_to_add == "save":
			save = True
			continue

		if not steamid_to_add.isdigit() or int(steamid_to_add) < 0x0110000100000000 or int(steamid_to_add) >= 0x01100001FFFFFFFF:
			add_anyways = input(f"{steamid_to_add} doesn't seem to be a valid SteamID64. Add anyways? [Y/n] ") in ("Y", "y")
			if not add_anyways:
				continue

		if steamid_to_add in temp_tracking_list:
			print(f"Already added {steamid_to_add}.")
			continue

		temp_tracking_list.append(steamid_to_add)
		print(f"Added {steamid_to_add} to tracking list.")
		print(f"Current list: {', '.join(temp_tracking_list)}")

	print(f"Saving list to {TRACKING_LIST_PATH}")
	for entry in temp_tracking_list:
		tracking_list.add_to_tracking_list(entry)
	print(f"Saved tracking list. Resuming execution as normal.")

if __name__ == "__main__":
	do_first_setup()

	webhook.set_username(WEBHOOK_USERNAME)
	webhook.set_avatar_url(WEBHOOK_AVATAR_URL)

	steam_login()
	steam_client.run_forever()












