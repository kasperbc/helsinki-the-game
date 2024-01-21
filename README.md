# Helsinki: The Game
A Discord bot and instructions for running a "Jet Lag: The Game"- inspired game on a city-scale. 

## Summary

The game is largely based off Season 4: "Battle 4 America" of Jet Lag: The Game. The players interact with the game using this Discord bot.

In the game, two or more teams go around the city of Helsinki and try to capture as many districts as possible before time runs out. 

To capture a district, the team must travel to the district and complete a randomly drawn challenge.

Once a challenge is completed, the team earns coins to spend in the shop. The items include things such as redrawing challenges and capturing districts instantly.

If a team is in a district you have captured and you get a photo of them, they get tagged, have to go back to the start and the tagging team earns extra coins!

_Todo: Write a proper instructions manual in docs_

## Requirements
* Python 3.12.1 or later
* The `discord` and `PyYaml` Python packages
* The capability to host a Discord bot for the duration of the game
* 2 or more players

## Setup

### Step 1: Create a new server

It is recommended that you run this game on an empty server. [Create a new server](https://support.discord.com/hc/en-us/articles/204849977-How-do-I-create-a-server) from the Discord client.

### Step 2: Set up channels

Create at least the following channels on your server:
* A "Game feed" channel
    * Used by the bot to announce important events during the game.
* A "Game status" channel
    * The bot will send messages here to update the status of the game. 
    * The players can use this to easily see which districts are free and which teams have what districts.
* A "Commands" channel
    * The players will need to interact with the bot during the game, so create a channel where the players can send bot commands.
* A "General" channel
    * This should be seperate from the "commands" channel.

It is recommended to set the "Game Feed" and "Game Status" channels up so the players cannot send messages in them.

### Step 3: Create a Discord Bot

Create a Discord Bot from the [Discord Developer Portal](https://discord.com/developers/applications) and invite it to your server. The default intents are enough to run the bot. 

If you are unsure on how to do this, follow the instructions [here](https://discordpy.readthedocs.io/en/stable/discord.html).


### Step 4: Set up the bot

Download or clone the repository and install the necessary Python packages.

Once downloaded, rename the `default_config.yaml` file to `config.yaml`, or run the `bot.py` Python script once, which will do it for you.

Open the config file and paste your bot token inside the `bot_token` field.

Paste your Discord server ID inside the `server_id` field.

Paste the channel ID's of the "Game Feed" and "Game Status" channels inside the `game_feed_channel_id` and `game_status_channel_id` fields.

If you are unsure on how to get your server and channel IDs, follow the instructions [here](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID).

### Step 5: Create the team roles

In your servers, create a role for each of your teams. The name or the permissions of your roles do not matter, but the role color does.

Make sure that each role has a distinct color. Currently, only the default role colors are supported (Do not use custom colors).

_Remember, that currently only one player is supported per team. If you want multiple players per team, each team must assign a person to interact with the bot._

Create an admin role with all the permissions if necessary.

### Step 6: Set up commands

Run the script to boot up the bot at least once. This should register the commands to the server.

Open the "Integrations" tab of your server and open the bot in the "Bots and Apps" section.

Under "Roles & Members", disable the permissions from the `@everyone` role (so that it shows a red X).

Under "Commands", enable permissions for the `@everyone` role for the following commands:
* /challenge
* /help
* /shop
* /tag

If done properly, the page should look like [this](docs/imgs/correct_command_setup.png).

### Step 7: Create challenges
Currently, 10 challenges have been written for this, but that is probably not enough go get the full enjoyment out of this, so it is recommended to write more challenges before playing.

To add more challenges to the game, go to the `challenges` folder and create a new text file for each challenge. You can delete the pre-written challenges, if you want to.

### Playing the game
You should now be ready to play the game! If you haven't, invite your players to the discord server and assign the team roles to the players.

The bot needs to be online for the duration of the game. You can host it on your computer or pay for external hosting.

General advice:

* Once started, the bot does not automatically stop the game. The amount of playtime should be agreed on beforehand and an admin must stop the game with a command once the time is up.

* Every player should have an active ticket for the HSL AB-Zone for the duration of the game.

* The setup and playtime might take a couple of hours, so reserve most of the day for this.

* Play with trustworthy players, nothing is preventing anyone from capturing districts they have not captured or completing challenges they have not completed.

* It might be a good idea to plan a time for a break in advance, running around the city for hours straight might be exhausting. The game can be paused with a command.

* The team names are the same as the displady names of the players, but the players can change their server nicknames for a custom team name. The bot only registers the name when the user sends a command for the fist time.

* Don't do anything that is illegal or would bother people outside the game.

* The game is so far untested, make adjustments to the rules as you see fit.

If anyone is injured or causes any trouble because of this game, the creator(s) are not responsible. You are playing this at your own risk.

## Playing this in another city
This version of the game is designed for the city of Helsinki, but the game is general enough to fit other cities.

In general, if your city is large enougn and has good coverage with public transport, this game should work with it. Smaller cities could work as well with adjusted play time and rules.

To modify this game, simply change the `districts` in the `config.yaml` file and creating new challenges.

A feature that I designed specifically with Helsinki in mind is the "Metro Pass" item, which allows a team to use the metro system once. Helsinki already has good coverage of the city with the tram network, but the public transport might be different for other cities where this wouldn't make sense. The Metro Pass can be turned off by changing the `enabled` field under the `metro_pass` field to `false`.

## Contributing
Contributions are always welcome. You can contribute by making the code better or writing more challenges, for example.

The game is so far untested, so giving it a play would be a great way to contribute! If anyone ever decides to play this, I would be glad to hear on how it went.

This game is licensed under the MIT License. Anyone is free to take this and make their own version, if they so wish. More info in the `LICENSE` file.

Ideas:
* Support for multiple players per team
* Ability for teams to choose their own name and emoji
* Automatic game time handling (Displaying how much time is left in the status)
* Better and more modular item shop system
* Visual map of districts captured in status