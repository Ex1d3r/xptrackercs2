# Login for account that checks the XP
# This account can't be used at the same time as the checker is running
STEAM_USERNAME = ""
STEAM_PASSWORD = ""
SHARED_SECRET = ""

# Steam API key for getting account name and avatar
# If you disable it, you wont see user's names or avatars
STEAM_API_KEY = ""
DISABLE_STEAM_API = False

# Path where logins for Steam will be saved
CREDENTIALS_LOCATION = "credentials"

# Webhook that will be used to post XP updates
DISCORD_UPDATE_WEBHOOK = ""
WEBHOOK_USERNAME = "Name of webhook"
WEBHOOK_AVATAR_URL = ""

# Path for list of users being tracked
TRACKING_LIST_PATH = "tracking_list.json"

# Send message if user is added/removed
SEND_TRACKING_LIST_UPDATES = True

# Timeout between checks (in seconds)
CHECK_TIMEOUT = 10

MEDAL_TIER_EMOJIS = {
    4873: ("<:white:1146884993986088960>",  "White"),
    4874: ("<:green:1146884995990953984>",  "Green"),
    4875: ("<:blue:1146884999153455147>",   "Blue"),
    4876: ("<:purple:1146885003435843614>", "Purple"),
    4877: ("<:pink:1146885005373624442>",   "Pink"),
    4878: ("<:red:1146885008431272076>",    "Red")
}

NO_MEDAL_EMOJI = (":warning:", "No")