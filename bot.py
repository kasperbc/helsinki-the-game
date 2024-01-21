import discord
from discord import app_commands
import os, random, json, shutil
from datetime import datetime, timedelta
import asyncio
import yaml
from yaml import Loader

# load config data
if not os.path.isfile("config.yaml"):
    if not os.path.isfile("default_config.yaml"):
        print("Cannot start bot! The default_config.yaml or the config.yaml file do not exist!")
        exit()
    else:
        shutil.copyfile("default_config.yaml", "config.yaml")
        print("The config.yaml file was not found, generated a new one! Please fill it out with the details of your bot.")
        exit()

config_data = yaml.load(open("config.yaml", "r").read(), Loader=Loader)

datetime_format = config_data["datetime_format"]
role_color_emoji = {
    "#1abc9c": "🟢",
    "#11806a": "🟢",
    "#2ecc71": "🟢",
    "#1f8b4c": "🟢",
    "#3498db": "🔵",
    "#206694": "🔵",
    "#9b59b6": "🟣",
    "#71368a": "🟣",
    "#e74c3c": "🔴",
    "#ad1457": "🔴",
    "#f1c40f": "🟡",
    "#c27c0e": "🟡",
    "#e67e22": "🟠",
    "#992d22": "🟤",
    "#e74c3c": "🔴",
    "#992d22": "🟤",
    "#95a5a6": "⚪",
    "#979c9f": "⚪",
    "#607d8b": "⚪",
    "#546e7a": "⚪",
    "#99aab5": "⚪",
}

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=config_data["server_id"]))
    print(f'We have logged in as {client.user}')

# player data
def get_player_data_path(discordId: int):
    return f"players\\{discordId}.json"

def is_player_data_invalid(discordId: int):
    if (not os.path.isfile(get_player_data_path(discordId))):
        return True
    try:
        json.loads(open(get_player_data_path(discordId)).read())
    except ValueError as e:
        return True
    return False

def register_new_player_data(discordId: int):
    # set file as invalid if json is invalid
    if (is_player_data_invalid(discordId)):
        if (os.path.isfile(get_player_data_path(discordId))):
            os.rename(get_player_data_path(discordId), f"players\\{discordId}_invalid.json")
    
    asyncio.create_task(set_player_name(discordId))

    playerData = {
        "id": discordId,
        "balance": config_data["starting_balance"],
        "team": "Unassigned",
        "teamEmoji": "⚪",
        "currentChallenge": None,
        "timeOutEnd": datetime.now().strftime(datetime_format),
        "challengesAvailable": os.listdir("challenges"),
        "districtsCaptured": [],
        "dmsEnabled": True
    }

    open(get_player_data_path(discordId), "x").write(json.dumps(obj=playerData, indent=4))

async def set_player_name(discordId: int):
    player_data = json.loads(open(get_player_data_path(discordId), "r").read())

    m = await client.get_guild(config_data["server_id"]).fetch_member(discordId)
    
    team_name = m.display_name
    for i in range(len(m.roles)):
        if ("Team" in m.roles[i].name):
            print(m.roles[i].color)
            team_name = m.roles[i].name

            if m.roles[i].color in role_color_emoji:
                team_emoji = "⚪"
            else:
                team_emoji = role_color_emoji[str(m.roles[i].color)]
                
            break

    player_data["team"] = team_name
    player_data["teamEmoji"] = team_emoji

    open(get_player_data_path(discordId), "w").write(json.dumps(obj=player_data, indent=4))

def set_player_balance(discordId: int, value: int):
    if (is_player_data_invalid(discordId)):
        register_new_player_data(discordId)

    player_data = json.loads(open(get_player_data_path(discordId), "r").read())

    player_data["balance"] = value

    open(get_player_data_path(discordId), "w").write(json.dumps(player_data, indent=4))

def add_player_balance(discordId: int, amount: int):
    if (is_player_data_invalid(discordId)):
        register_new_player_data(discordId)

    player_data = json.loads(open(get_player_data_path(discordId), "r").read())

    player_data["balance"] = player_data["balance"] + amount

    open(get_player_data_path(discordId), "w").write(json.dumps(player_data, indent=4))

def add_player_district_claim(discordId: int, claim: str):
    game_data = json.loads(open("gamedata.json").read())
    player_data = json.loads(open(get_player_data_path(discordId), "r").read())

    if (claim not in game_data["openDistricts"]):
        print("Unable to add district to player (District not in open districts)")
        return False

    # set player data
    player_data["districtsCaptured"].append(claim)
    open(get_player_data_path(discordId), "w").write(json.dumps(obj=player_data, indent=4))

    # set game data
    game_data["openDistricts"].remove(claim)
    open("gamedata.json", "w").write(json.dumps(obj=game_data, indent=4))

    asyncio.create_task(update_game_status())
    asyncio.create_task(send_game_feed_message(event_emoji="🏳️", event_header="District captured!", message=f"**{player_data['team']}** {player_data['teamEmoji']} has captured the district of **{claim}**!"))

    return True

def remove_player_district_claim(discordId: int, claim: str):
    game_data = json.loads(open("gamedata.json").read())
    player_data = json.loads(open(get_player_data_path(discordId), "r").read())

    if (claim not in player_data["districtsCaptured"]):
        print("Unable to remove district from player (District not in claimed districts)")
        return False

    # set player data
    player_data["districtsCaptured"].remove(claim)
    open(get_player_data_path(discordId), "w").write(json.dumps(obj=player_data, indent=4))

    # set game data
    game_data["openDistricts"].append(claim)
    open("gamedata.json", "w").write(json.dumps(obj=game_data, indent=4))

    asyncio.create_task(update_game_status())

    return True

def add_open_claim(claim: str):
    # set game data
    game_data = json.loads(open("gamedata.json").read())
    game_data["openDistricts"].append(claim)
    open("gamedata.json", "w").write(json.dumps(obj=game_data, indent=4))

def remove_open_claim(claim: str):
    # set game data
    game_data = json.loads(open("gamedata.json").read())
    game_data["openDistricts"].remove(claim)
    open("gamedata.json", "w").write(json.dumps(obj=game_data, indent=4))

def set_new_challenge_player(discordId: int):
    # get player data
    player_data = json.loads(open(get_player_data_path(discordId), 'r').read())

    # reset challenges if none available
    if (len(player_data["challengesAvailable"]) <= 0):
        player_data["challengesAvailable"] = os.listdir("challenges")

    # get random challenge from available challenges
    challengePath = random.choice(player_data["challengesAvailable"])

    # update player data
    player_data["challengesAvailable"].remove(challengePath)
    player_data["currentChallenge"] = challengePath

    # save data
    open(get_player_data_path(discordId), 'w').write(json.dumps(obj=player_data, indent=4))

def get_player_current_challenge_description(discordId: int):
    player_data = json.loads(open(get_player_data_path(discordId), 'r').read())

    challengePath = player_data["currentChallenge"]
    return open(file=f"challenges\\{challengePath}").read()

# game data
def is_game_data_invalid():
    if (not os.path.isfile("gamedata.json")):
        return True
    
    try:
        json.loads(open("gamedata.json").read())
    except ValueError as e:
        return True
    return False

def create_new_game_data():
    game_data = {
        "started": False,
        "startTime": None,
        "statusMessageId": -1,
        "openDistricts": config_data["districts"]
    }

    open("gamedata.json", "w").write(json.dumps(game_data, indent=4))

def game_started():
    if (is_game_data_invalid()):
        return False

    game_data = json.loads(open("gamedata.json", 'r').read())

    return game_data["started"]

def time_since_game_start():
    game_data = json.loads(open("gamedata.json", 'r').read())

    start_time = datetime.strptime(game_data["startTime"], datetime_format)
    time_diff = datetime.now() - start_time

    return time_diff


# game status / feed

async def update_game_status():
    game_data = json.loads(open("gamedata.json", 'r').read())

    statusText = "# Game Status\n"

    # captured districts
    players = os.listdir("players")
    for i in range(len(players)):
        if ("invalid" in players[i]):
            continue
        
        player_data = json.loads(open(f"players\\{players[i]}", 'r').read())
        statusText += f"## {player_data['team']}\n"

        if (len(player_data["districtsCaptured"]) != 0):
            for j in range(len(player_data["districtsCaptured"])):
                statusText += f"- {player_data['districtsCaptured'][j]}\n"
        else:
            statusText += "*No districts captured yet*\n"
    
    # uncaptured districts
    statusText += "## Uncaptured districts\n"
    if (len(game_data["openDistricts"]) != 0):
        game_data["openDistricts"] = sorted(game_data["openDistricts"])
        for i in range(len(game_data["openDistricts"])):
            statusText += f"- {game_data['openDistricts'][i]}\n"
    else:
        statusText += "*No uncaptured districts 😔*"

    try:
        statusmsg = client.get_channel(config_data["game_status_channel_id"]).get_partial_message(game_data["statusMessageId"])
        await statusmsg.edit(content=statusText)
    except:
        statusmsg = await client.get_channel(config_data["game_status_channel_id"]).send(content=statusText)
        game_data["statusMessageId"] = statusmsg.id
        open("gamedata.json", 'w').write(json.dumps(obj=game_data, indent=4))

async def send_game_feed_message(event_emoji: str, event_header: str, message: str):
    await client.get_channel(config_data["game_feed_channel_id"]).send(content=f"## **{event_header}** {event_emoji}\n{message}")

# views
class ClaimSelect(discord.ui.Select):
    def __init__(self):
        options=[]
        
        # load all open districts as options
        game_data = json.loads(open("gamedata.json").read())
        open_districts = sorted(game_data["openDistricts"])
        if (len(open_districts) == 0):
            options.append(discord.SelectOption(label="No open districts", emoji="😔"))
        else:
            for i in range(len(open_districts)):
                options.append(discord.SelectOption(label=open_districts[i]))

        super().__init__(placeholder="Please select your current district:",max_values=1,min_values=1,options=options)
    async def callback(self, interaction: discord.Interaction):
        if (self.values[0] == "No open districts"):
            await interaction.response.edit_message(view=None, content="## This is so sad\nThere are no districts left to capture, so you cannot capture any.")
            return
        
        if (add_player_district_claim(discordId=interaction.user.id, claim=self.values[0])):
            await interaction.response.edit_message(view=None, content=f"## Captured!\nYou have captured the district of **{self.values[0]}**!\n\n*If this was a misclick, message kekis about it.*")
        else:
            await interaction.response.edit_message(view=None, content=f"## Uh oh!\nYou cannot capture the district of **{self.values[0]}**, because it is claimed by someone else.\n\n*If you believe this is a mistake, message kekis about it.*")

class ClaimView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ClaimSelect())

class TagSelect(discord.ui.Select):
    def __init__(self):
        options=[]

        # load all teams as options
        player_files = os.listdir("players")
        
        for i in range(len(player_files)):
            try:
                player_data = (json.loads(open(f"players\\{player_files[i]}").read()))
                options.append(discord.SelectOption(label=f"[{player_data['team']}] {player_data['displayName']}", emoji=player_data["teamEmoji"], value=player_data["id"]))
            except:
                continue
        
        
        super().__init__(placeholder="Which team are you tagging?:",max_values=1,min_values=1,options=options)
    async def callback(self, interaction: discord.Interaction):
        #if (str(self.values[0]) == str(interaction.user.id)):
            #await interaction.response.edit_message(content="You cannot tag yourself!", view=None)
            #return
        
        player_data_victim = json.loads(open(get_player_data_path(self.values[0]), 'r').read())
        player_data_tagger = json.loads(open(get_player_data_path(interaction.user.id), 'r').read())

        # reset victim balance
        set_player_balance(self.values[0], config_data["starting_balance"])

        # add tagger balance
        add_player_balance(interaction.user.id, config_data["coins_per_tag"])

        await interaction.response.edit_message(content=f"## Tagged!\nYou have tagged {player_data_victim['teamEmoji']} **{player_data_victim['team']}**!", view=None)
        
        class TagNotificationView(discord.ui.View):
            @discord.ui.button(label="Disable DMs", style=discord.ButtonStyle.danger)
            async def command_disable_dm_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_message(content="DMs have been disabled. Except for this one")
                player_data_victim = json.loads(open(get_player_data_path(interaction.user.id), 'r').read())
                player_data_victim["dmsEnabled"] = False
                open(get_player_data_path(interaction.user.id), 'w').write(json.dumps(player_data_victim))
                
        if (player_data_victim["dmsEnabled"]):
            m = await client.fetch_user(player_data_victim["id"]) 
            await m.send(content=f"# Uh oh!\nYou have been tagged by {player_data_victim['teamEmoji']} **{player_data_tagger['team']}**!\n\nYou must now immediately return to the starting point and can continue the game after arriving there. While on the way back, do not complete challenges and do not collect $200.", view=TagNotificationView())

        asyncio.create_task(send_game_feed_message(event_emoji="🎯", event_header="Team tagged!", message=f"**{player_data_victim['team']}** {player_data_victim['teamEmoji']} has been tagged by **{player_data_tagger['team']}** {player_data_tagger['teamEmoji']}!"))

class TagView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(TagSelect())

# commands
@tree.command(name = "help", description = "Open the help menu", guild=discord.Object(id=config_data["server_id"]))
async def command_help(interaction : discord.Interaction):
    class HelpView(discord.ui.View):

        @discord.ui.button(label="Commands and menus", style=discord.ButtonStyle.secondary)
        async def command_help_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
            command_list = """/help: Open the help menu
- Commands: Open the list of commands

/challenge: Open the challenge menu
- Draw Challenge: Get a new challenge, if you are not already in the progress of completing a challenge.
- Complete Challenge: Complete your current challenge and claim the district you are on, if it is unclaimed.
- Forfit Challenge: Give up on your current challenge. Doing this will block you from drawing new challenges for 5 minutes.

/shop: Open the shop and view your balance
- Metro Pass: Get a single-use metro pass. The metro pass allows you to enter a metro outside your captured districts. After you use this, you can travel as far as you want on the metro, but exiting and re-entering will require another pass.
- Challenge Redraw: Give up on your current challenge and draw a new one without any time penalty.
- Insta-capture: Capture the current district you are on without needing to completing a challenge.

/tag: Open the tag menu
- In order to tag another player, you must first get a recognizable photo of them and send it to the chat.
- Tagging another player gives you 2M."""

            await interaction.response.edit_message(content=f"## Commands and menus\n\n`{command_list}`", view=None)

    await interaction.response.send_message(content="What do you need help with?", view=HelpView(), ephemeral=True)

@tree.command(name = "shop", description = "Open the shop", guild=discord.Object(id=config_data["server_id"]))
async def command_shop(interaction : discord.Interaction):
    if (not game_started()):
        await interaction.response.send_message(content="The game has not started yet!", ephemeral=True)
        return

    if (is_player_data_invalid(interaction.user.id)):
        register_new_player_data(interaction.user.id)

    player_data = json.loads(open(get_player_data_path(interaction.user.id), 'r').read())
    balance = player_data["balance"]
    ongoingChallenge = player_data["currentChallenge"] != None

    class ShopView(discord.ui.View):

        if config_data["items"]["metro_pass"]["enabled"]:
            @discord.ui.button(label=f"Metro Pass [Cost: {["items"]["metro_pass"]["cost"]}]", style=discord.ButtonStyle.gray, emoji="🚇", row=0, disabled=balance < 1)
            async def metro_pass_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
                add_player_balance(discordId=interaction.user.id, amount=-["items"]["metro_pass"]["cost"])
                await interaction.response.edit_message(content=f"# Metro pass 🚇\nYou can now board the metro.", view=None)

        if config_data["items"]["challenge_redraw"]["enabled"]:
            @discord.ui.button(label=f"Challenge Redraw {["items"]["challenge_redraw"]["cost"]}", style=discord.ButtonStyle.gray, emoji="♻️", row=1, disabled=not ongoingChallenge or balance < 2)
            async def redraw_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
                add_player_balance(discordId=interaction.user.id, amount=-["items"]["challenge_redraw"]["cost"])
                set_new_challenge_player(discordId=interaction.user.id)
                await interaction.response.edit_message(content=f"# Challenge redraw ♻️\nYour current challenge has been redrawn.\n## New challenge:\n{get_player_current_challenge_description(interaction.user.id)}", view=None)

        if config_data["items"]["insta_capture"]["enabled"]:
            @discord.ui.button(label=f"Insta-capture {["items"]["insta_capture"]["cost"]}", style=discord.ButtonStyle.gray, emoji="🏳️", row=2, disabled=balance < 6)
            async def instacapture_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
                add_player_balance(discordId=interaction.user.id, amount=-["items"]["insta_capture"]["cost"])
                await interaction.response.edit_message(content="# Insta-capture 🏳️\nYou are able to capture the district you are on!", view=ClaimView())

    await interaction.response.send_message(content=f"# The Shop\n\nBalance: **{balance}**\n\nWhat would you like to buy?", view=ShopView(), ephemeral=True)

@tree.command(name = "challenge", description = "Open the challenge menu", guild=discord.Object(id=config_data["server_id"]))
async def command_challenge(interaction : discord.Interaction):
    if (not game_started()):
        await interaction.response.send_message(content="The game has not started yet!", ephemeral=True)
        return

    if (is_player_data_invalid(interaction.user.id)):
        register_new_player_data(interaction.user.id)

    # get challenge info
    player_data = json.loads(open(get_player_data_path(interaction.user.id), 'r').read())
    ongoingChallenge = player_data["currentChallenge"] != None
    if (not ongoingChallenge):
        challengeText = "You do not have any ongoing challenges."
    else:
        challengeText = "## Current challenge:\n" + open(file=f"challenges\\{player_data['currentChallenge']}").read()
    
    onTimeOut = datetime.strptime(player_data["timeOutEnd"], datetime_format) > datetime.now()
    if (onTimeOut):
        timeDiff = datetime.strptime(player_data["timeOutEnd"], datetime_format) - datetime.now()
        challengeText = f"Because you forfitted a challenge, you are not able to draw a new challenge. You can draw a new challenge in **{round(timeDiff.seconds / 60)}** minutes."

    class ChallengeView(discord.ui.View):

        @discord.ui.button(label="Draw challenge", style=discord.ButtonStyle.blurple, emoji="❔", row=0, disabled=ongoingChallenge | onTimeOut)
        async def challenge_draw_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
            set_new_challenge_player(interaction.user.id)

            # display challenge
            await interaction.response.edit_message(content=f"# Challenge\n{get_player_current_challenge_description(interaction.user.id)}", view=None)

        @discord.ui.button(label="Complete challenge", style=discord.ButtonStyle.green, emoji="🏳️", row=1, disabled=not ongoingChallenge)
        async def challenge_complete_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
            add_player_balance(discordId=interaction.user.id, amount=config_data["coins_per_capture"])
            await interaction.response.edit_message(content="# Challenge complete!\nYou have earned **1M**.\n\nYou can now capture your current district!", view=ClaimView())
            
            # clear current challenge
            player_data = json.loads(open(get_player_data_path(interaction.user.id), 'r').read())
            player_data["currentChallenge"] = None
            open(get_player_data_path(interaction.user.id), 'w').write(json.dumps(obj=player_data, indent=4))

        @discord.ui.button(label="Forfit challenge", style=discord.ButtonStyle.red, emoji="🗑️", row=2, disabled=not ongoingChallenge)
        async def challenge_forfit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
            # clear current challenge
            player_data = json.loads(open(get_player_data_path(interaction.user.id), 'r').read())
            player_data["currentChallenge"] = None

            # set timeout duration
            player_data["timeOutEnd"] = datetime.strftime(datetime.now() + timedelta(minutes=5), datetime_format)
            open(get_player_data_path(interaction.user.id), 'w').write(json.dumps(obj=player_data, indent=4))

            await interaction.response.edit_message(content="# Challenge forfitted\nYou have forfitted your current challenge.\n\nYou are able to draw a new challenge in 5 minutes.")


    await interaction.response.send_message(content=f"# Challenge menu\n{challengeText}\n", view=ChallengeView(), ephemeral=True)

@tree.command(name = "tag", description= "Tag / Eliminate another team by taking a photo of them", guild=discord.Object(id=config_data["server_id"]))
async def command_tag(interaction : discord.Interaction):
    if (not game_started()):
        await interaction.response.send_message(content="The game has not started yet!", ephemeral=True)
        return

    if (time_since_game_start().seconds / 60 < 30):
        await interaction.response.send_message(content=f"The grace period is not yet over! The grace period ends in {30 - round(time_since_game_start().seconds / 60)} minute(s).", ephemeral=True)
        return
    
    if (is_player_data_invalid(interaction.user.id)):
        register_new_player_data(interaction.user.id)

    await interaction.response.send_message(content="## Tag menu\nWhich player are you tagging?\n\n*(Please make sure you have taken a photo and sent it before using this menu. Also avoid misclicking here because this is really annoying to undo)*", view=TagView(), ephemeral=True)


# admin commands
@tree.command(name = "startgame", description = "Start the game", guild=discord.Object(id=config_data["server_id"]))
async def command_start_game(interaction : discord.Interaction):
    # check if game data exists
    if (is_game_data_invalid()):
        print("Game data invalid. Creating new data.")
        create_new_game_data()

    # check if game started
    if (game_started()):
        await interaction.response.send_message("The game has already been started!", ephemeral=True)
        return
    
    
    await interaction.response.send_message(content="Starting game...", ephemeral=True)

    game_status_msg = await client.get_channel(config_data["game_status_channel_id"]).send(content="# Game status")
    
    game_data = json.loads(open("gamedata.json", 'r').read())
    
    game_data["started"] = True
    game_data["startTime"] = datetime.now().strftime(datetime_format)
    game_data["statusMessageId"] = game_status_msg.id

    open("gamedata.json", "w").write(json.dumps(obj=game_data, indent=4))

    await update_game_status()
    asyncio.create_task(send_game_feed_message(event_emoji="🏁", event_header="Game started!", message=f"The game has started!"))

@tree.command(name = "pausegame", description = "Pause the game without clearing data. Can be resumed later with /resumegame", guild=discord.Object(id=config_data["server_id"]))
async def command_pause_game(interaction : discord.Interaction):
    game_data = json.loads(open("gamedata.json", 'r').read())
    game_data["started"] = False
    open("gamedata.json", "w").write(json.dumps(obj=game_data, indent=4))

    await interaction.response.send_message("Game has been paused!", ephemeral=True)

    asyncio.create_task(send_game_feed_message(event_emoji="✋", event_header="Game paused!", message=f"The game has been paused!"))

@tree.command(name = "resumegame", description = "Un-pause the game.", guild=discord.Object(id=config_data["server_id"]))
async def command_resume_game(interaction : discord.Interaction):
    game_data = json.loads(open("gamedata.json", 'r').read())
    game_data["started"] = True
    open("gamedata.json", "w").write(json.dumps(obj=game_data, indent=4))

    await interaction.response.send_message("Game has been resumed!", ephemeral=True)

    asyncio.create_task(send_game_feed_message(event_emoji="🏁", event_header="Game resumed!", message=f"The game has been un-paused!"))

@tree.command(name = "resetgame", description = "Reset game data (Use carefully!)", guild=discord.Object(id=config_data["server_id"]))
async def command_reset_game(interaction : discord.Interaction, confirmation: bool):
    if (not confirmation):
        return

    files = os.listdir("players\\")
    
    backupdir = f"backup_data\\{datetime.now().strftime('backup_%d-%m-%Y_%H.%M.%S_%f')}"
    os.mkdir(backupdir)

    # backup/clear player data
    if (len(files) > 0):
        for i in range(len(files)):
            shutil.move(f"players\\{files[i]}", f"{backupdir}")

    # backup/clear game data
    if (os.path.exists("gamedata.json")):
        shutil.move("gamedata.json", backupdir)
    
    create_new_game_data()

    await interaction.response.send_message(content="Game data reset!", ephemeral=True)

@tree.command(name = "resetplayer", description = "Reset player data (Use carefully!)", guild=discord.Object(id=config_data["server_id"]))
async def command_reset_player(interaction : discord.Interaction, player: discord.Member):
    playerPath = get_player_data_path(player.id)

    if (os.path.exists(playerPath)):
        os.remove(playerPath)
    
    register_new_player_data(player.id)

    await interaction.response.send_message(content="Player data reset!", ephemeral=True)

@tree.command(name = "setbalance", description = "Set a player's balance", guild=discord.Object(id=config_data["server_id"]))
async def command_set_player_balance(interaction : discord.Interaction, player: discord.Member, value: int):
    set_player_balance(discordId=player.id, value=value)

    await interaction.response.send_message("Set balance succesfully!", ephemeral=True)

@tree.command(name = "playerinfo", description = "Get a player's JSON data", guild=discord.Object(id=config_data["server_id"]))
async def command_get_player_info(interaction : discord.Interaction, player: discord.Member):
    await interaction.response.send_message(content=f"### {player.id}.json ({player.display_name})\n`{open(get_player_data_path(player.id), 'r').read()}`", ephemeral=True)

@tree.command(name = "addclaim", description = "Add a district for a player", guild=discord.Object(id=config_data["server_id"]))
async def command_add_player_claim(interaction : discord.Interaction, player: discord.Member, claim: str):
    if (add_player_district_claim(discordId=player.id, claim=claim)):
        await interaction.response.send_message(content=f"Captured **{claim}** for **{player.display_name}**", ephemeral=True)
    else:
        await interaction.response.send_message(content=f"Cannot capture **{claim}** for **{player.display_name}** because **{claim}** is captured by someone else.", ephemeral=True)

@tree.command(name = "removeclaim", description = "Remove a district from a player", guild=discord.Object(id=config_data["server_id"]))
async def command_remove_player_claim(interaction : discord.Interaction, player: discord.Member, claim: str):
    if (remove_player_district_claim(discordId=player.id, claim=claim)):
        await interaction.response.send_message(content=f"Unclaimed **{claim}** from **{player.display_name}**", ephemeral=True)
    else:
        await interaction.response.send_message(content=f"Cannot remove **{claim}** from **{player.display_name}** because **{claim}** is not captured by {player.display_name}.", ephemeral=True)

@tree.command(name = "addopenclaim", description = "Add a district to the open districts", guild=discord.Object(id=config_data["server_id"]))
async def command_add_open_claim(interaction : discord.Interaction, claim: str):
    add_open_claim(claim=claim)
    await interaction.response.send_message(content=f"Added **{claim}** to the open claims", ephemeral=True)

@tree.command(name = "removeopenclaim", description = "Remove a district from the open districts", guild=discord.Object(id=config_data["server_id"]))
async def command_remove_open_claim(interaction : discord.Interaction, claim: str):
    remove_open_claim(claim=claim)
    await interaction.response.send_message(content=f"Removed **{claim}** from the open districts", ephemeral=True)

@tree.command(name = "gameinfo", description = "View the game JSON info", guild=discord.Object(id=config_data["server_id"]))
async def command_remove_open_claim(interaction : discord.Interaction):
    await interaction.response.send_message(content=f"## gamedata.json\n`{open('gamedata.json').read()}`", ephemeral=True)

# setup
try:
   os.mkdir("players")
except FileExistsError:
   # directory already exists
   pass

# run client
client.run(config_data["bot_token"])