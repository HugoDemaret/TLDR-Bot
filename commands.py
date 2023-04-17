import asyncio
import csv

import discord
from discord import Embed
from matplotlib import pyplot as plt

import tldr
import mood
import mod
import socialGraph
from utils import printExceptions


# •====================•
#    GENERAL COMMANDS
# •====================•

def prefix(bot, message, guildData, mots) -> None:
    """
    Changes the prefix of the bot
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :param mots: the message's content split into words
    :return: None
    """
    if len(mots) == 0:  # User only wants to consult the prefix
        bot.send_message(f"**{message.author.display_name}**, the prefix is **{guildData.prefix}**", message.channel)
        return

    if mots[1] == "set":
        # User wants to change the prefix
        if not message.author.guild_permissions.administrator:  # Only admins can change the prefix
            bot.send_message(
                f"**{message.author.display_name}**, you must be a server administrator to change the prefix :/",
                message.channel)
            return

        if len(mots) != 3:  # Too many arguments
            bot.send_message(f"**{message.author.display_name}**, the prefix cannot contain any space :/",
                             message.channel)
            return

        guildData.prefix = message.clean_content[len(guildData.prefix):].split()[2]
        bot.send_message(f"Prefix set to **{guildData.prefix}**", message.channel)
        return

    bot.send_message(f"This isn't a valid command (`see {guildData.prefix}help prefix`)", message.channel)


async def bye(bot, message):
    """
    Closes the bot
    :param bot: the bot
    :param message: the message to process
    :return: None
    """
    bot.save()
    await bot.socialGraphWorker.save()
    # mood.resetMoods()
    await message.channel.send("Cya! :D")
    await bot.close()
    exit(0)


def helpCommand(bot, message, guildData, mots):
    """
    Sends the help embed
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :param mots: the message's content split into words
    :return: None
    """
    if len(mots) == 1:  # User wants an embed with the commands list
        title = "Commands List"
        description = f"""
            This server's prefix is **{guildData.prefix}**, use it before the following words to invoke a command.
            To see more info on a specific command, type {guildData.prefix}help <command>

            **General commands**

            • `help`
            • `prefix`

            **Chat summarisation commands**

            • `tldr`
            • `tldrsettings`

            **Mood analysis commands**

            • `mood`
            • `moods`
            • `moodsettings`
            • `moodroles`
            • `moodtraining`

            **Social graph commands**

            • `socialgraph`
            • `importance`
    
            **Automatic moderation commands**
            • `moderatesettings`
            • `muteuser`
            • `ban`
            • `unban`
            • `kick`
            """

        embed = Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return

    match mots[1]:

        # case "template":
        #     title = "template <argument> {optional argument}"
        #     description = f"""
        #         This is the description of the template.
        #
        #         **Subcommand:**
        #
        #         • subcommand
        #
        #         See `{guildData.prefix}help template <subcommand>` for more info.
        #
        #         **Arguments:**
        #
        #         • argument: an argument
        #         • optional argument: an optional argument
        #
        #         **Examples:**
        #
        #         • `{guildData.prefix}template`
        #         • `{guildData.prefix}template argument`
        #         • `{guildData.prefix}template argument optional`
        #         """

        # •===• General commands •===•

        case "help":
            title = "help {command}"
            description = f"""
                If no argument is written, displays a list of all the available commands.
                If a command name is written, displays info about this command.

                **Argument:**

                • command: the name of the command you want info on.

                **Examples:**

                • `{guildData.prefix}help`
                • `{guildData.prefix}help mood`
                • `{guildData.prefix}help prefix set`
                """

        case "prefix":
            if len(mots) == 2:
                title = "prefix {subcommand}"
                description = f"""
                    If no subcommand written the current prefix of the server.

                    **Subcommand:**

                    • set

                    See `{guildData.prefix}help prefix <subcommand>` for more info.

                    **Arguments:**

                    • argument: an argument
                    • optional argument: an optional argument

                    **Example:**

                    • `{guildData.prefix}prefix`
                    """

            else:
                if mots[2] == "set":
                    title = "prefix set <new_prefix>"
                    description = f"""
                        Sets the prefix to new_prefix.
                        You must be a server administrator to use this command.

                        **Argument:**

                        • new_prefix: what you want the new prefix to be (no spaces allowed)

                        **Examples:**

                        • `{guildData.prefix}prefix set !`
                        • `{guildData.prefix}prefix set TLDR!`
                        """
                else:
                    bot.send_message(
                        f"**{message.author.display_name}**, I couldn't find the command you asked for :/ (see {guildData.prefix}help prefix)",
                        message.channel)
                    return

        # •===• TL;DR commands •===•

        case "tldr":
            title = "TLDR"
            description = f"""
                Make the summarisation of the last chat or chats.
                If with no reply, the summarisation will start at the last message of the channel.
                If with a reply, the summarisation will start at the replied message.

                By default, the summarisation will be done on every message around the message of interest and 
                the summarisation will be done on the topic of the message of interest.

                **Arguments:**

                • position: 3 options, "before", "after" or "around" (default: "around"):
                    - "before" will make the summarisation on the messages before the message of interest.
                    - "after" will make the summarisation on the messages after the message of interest.
                    - "around" will make the summarisation on the messages around the message of interest.

                • quantity: the number of topics to summarise, by default 1 (the topic of the message of interest) 
                and can be "all" to summarise all the topics.

                **Examples:**

                • `{guildData.prefix}tldr`
                • `TLDR`
                • `{guildData.prefix}TLDR all`
                • `tldr before one`
                """

        case "tldrsettings":
            title = "tldrsettings"
            description = f"""
                Shows the current settings of the summarisation.

                **Example:**

                • `{guildData.prefix}tldrsettings`
                """

        # •===• Mood analysis commands •===•

        case "mood":
            title = "mood {user}"
            description = f"""
                Shows you the current mood of a user.
                To specify a user, either mention them or write their ID (developer mode required).
                If no user is specified, shows your own mood.

                **Arguments:**

                • user: either a user ID or a user mention

                **Examples:**

                • `{guildData.prefix}mood`
                • `{guildData.prefix}mood @TL;DR`
                • `{guildData.prefix}mood 1067151621152321586`
                """

        case "moods":
            title = "moods"
            description = f"""
                Creates and sends a bar chart and a pie chart to show the distribution of moods on the server.

                **Example:**

                • `{guildData.prefix}moods`
                """

        case "moodsettings":
            if len(mots) == 2:
                title = "moodsettings {subcommand}"
                description = f"""
                    If no subcommand is written, displays the current state of the mood settings.

                    **Subcommands:**

                    • refreshmethod
                    • refreshtime
                    • resettime
                    • threshold
                    • depth

                    See `{guildData.prefix}help moodsettings <subcommand>` for more info.

                    **Example:**

                    • `{guildData.prefix}moodsettings`
                    """
            else:
                match mots[2]:
                    case "refreshmethod":
                        title = "moodsettings refreshmethod <method>"
                        description = f"""
                            Changes the way the users' moods are refreshed.

                            You must be a server administrator to use this command.

                            **Argument:**

                            • Method: The number of the method you want to apply:
                            \t1: Mood refreshes for all users at time intervals which length you can set (see {guildData.prefix}help moodsettings resreshtime)
                            \t2: Mood refreshed when a user sends a message

                            **Examples:**

                            • `{guildData.prefix}moodsettings refreshmethod 1`
                            • `{guildData.prefix}moodsettings refreshmethod 2`
                            """

                    case "refreshtime":
                        title = "moodsettings refreshtime <time>"
                        description = f"""
                            Changes the time between two mood refreshes.
                            The new time can not exceed 180 minutes.

                            You must be a server administrator to use this command.

                            **Argument:**

                            • time: the new time between two mood refreshes (in minutes)

                            **Example:**

                            • `{guildData.prefix}moodsettings refreshtime 20`
                            """

                    case "resettime":
                        title = "moodsettings resettime <time>"
                        description = f"""
                            Changes the time between two mood resets.
                            The new time can not exceed 180 minutes.
                            During a mood reset, every user which did not send a message since the last reset will lose their mood. This allows the moods not to be too outdated.

                            You must be a server administrator to use this command.

                            **Argument:**

                            • time: the new time between two mood resets (in minutes)

                            **Example:**

                            • `{guildData.prefix}moodsettings resettime 30`
                            """

                    case "threshold":
                        title = "moodsettings threeshold <message_number>"
                        description = f"""
                            Changes the number of messages a user needs to send before their mood stars being computed.

                            **Argument:**

                            • message_number: the new number of messages required

                            **Example:**

                            • `{guildData.prefix}moodsettings threshold 10`
                            """

                    case "depth":
                        title = "moodsettings depth <message_number>"
                        description = f"""
                            Changes the maximum number of last messages considered in order to compute a user's mood.
                            The higher this value is the more precise their mood will be. 
                            However a number of messages too high slows down the reactivity of the mood change when a user's mood changes.

                            You must be a server administrator to use this command.

                            **Argument:**

                            • message_number: the new maximum number of messages considered

                            **Example:**

                            • `{guildData.prefix}moodsettings depth 30`
                            """

                    case _:
                        bot.send_message(
                            f"**{message.author.display_name}**, I couldn't find the command you asked for :/ (see {guildData.prefix}help moodsettings)",
                            message.channel)
                        return

        case "moodroles":
            if len(mots) == 2:
                title = "moodroles {subcommand}"
                description = f"""
                    If no subcommand is written, displays the current state of the mood roles.

                    **Subcommands:**

                        • toggle
                        • reset

                    See `{guildData.prefix}help moodroles <subcommand>` for more info.

                    **Example:**

                    • `{guildData.prefix}moodroles`
                    """

            else:
                match mots[2]:
                    case "toggle":
                        title = "moodroles toggle"
                        description = f"""
                            Toggles the use of the mood roles:
                            \t• If mood roles are currently enabled they will be disabled, and deleted from this server.
                            \t• If mood roles are currently disabled they will be enabled and automatically created.

                            You must be a server administrator to use this command.

                            **Example:**

                            • `{guildData.prefix}moodroles toggle`
                            """

                    case "reset":
                        title = "moodroles reset"
                        description = f"""
                            Resets this server's mood roles: they will be deleted and created again.

                            You must be a server administrator to use this command.

                            **Example:**

                            • `{guildData.prefix}moodroles reset`
                            """

                    case _:
                        bot.send_message(
                            f"**{message.author.display_name}**, I couldn't find the command you asked for :/ (see `{guildData.prefix}help moodroles`)",
                            message.channel)
                        return

        case "moodtraining":
            if len(mots) == 2:
                title = "moodtraining {subcommand}"
                description = f"""
                    If no subcommand is written, displays the current state of the mood training for you.
                    Mood training enabled means that your messages will be used to train the AI and improve its mood prediction.

                    **Subcommands:**

                        • toggle
                        • count

                    See `{guildData.prefix}help moodtraining <subcommand>` for more info.

                    **Example:**

                    • `{guildData.prefix}moodtraining`
                    """

            else:
                match mots[2]:
                    case "toggle":
                        title = "moodtraining toggle"
                        description = f"""
                            Toggles the usage of your messages for training the mood analysis AI:
                            \t• If mood training is currently enabled for you it will be disabled.
                            \t• If mood training is currently disabled for you it will be enabled.

                            **Example:**

                            • `{guildData.prefix}moodtraining toggle`
                            """
                    case "count":
                        title = "moodtraining count"
                        description = f"""
                        Displays the number of entries per emotion in the mood training dataset.

                        **Example:**

                        • `{guildData.prefix}moodtraining count`
                        """
                    case _:
                        bot.send_message(
                            f"**{message.author.display_name}**, I couldn't find the command you asked for :/ (see `{guildData.prefix}help moodtraining`)",
                            message.channel)
                        return

        # •===• Social graph commands •===•
        case "socialgraph":
            title = "socialgraph {optional argument}"
            description = f"""
                        If no argument is provided, displays the whole social graph, centered on the author.

                        **Arguments:**

                        • optional : user - The user to center the graph on
                        • optional : distance - The max distance for a user to be shown. Put 'all' to put everyone (defaults to 2) (ex: distance of 2 will show up to the people that interacted with the people you interacted with)
                        

                        **Examples:**

                        • `{guildData.prefix}socialgraph`
                        • `{guildData.prefix}socialgraph @user`
                        • `{guildData.prefix}socialgraph @user 1`
                        • `{guildData.prefix}socialgraph @user all`
                        """

        case "importance":
            title = "importance {optional argument}"
            description = f"""
                If no argument is provided, displays the importance of the author.

                **Arguments:**

                • optional argument: user

                **Examples:**

                • `{guildData.prefix}importance`
                • `{guildData.prefix}importance @user`
                """
        case "sentiment":
            title = "sentiment {optional argument}"
            description = f"""
                        If no argument is provided, displays the sentiment of the author.

                        **Arguments:**

                        • optional argument: user

                        **Examples:**

                        • `{guildData.prefix}sentiment`
                        • `{guildData.prefix}sentiment @user`
                        """

        # •===• Automod commands •===•
        case "moderatesettings":
            if len(mots) == 2:
                title = "moderatesettings {subcommand}{subcommand}{value}"
                description = f"""
                        If no subcommand is written, displays all the available commands.

                        **Subcommands:**

                        • banword
                        • perm

                        **Settings (banword):**

                        • add
                        • remove
                        • print
                        • perm

                        **Example:**

                        • `{guildData.prefix}moderatesettings banword <subsection> <value>`
                        • `{guildData.prefix}moderatesettings perm <group>`
                        """
            else:
                match mots[2]:
                    case "banword":
                        if len(mots) == 3:
                            title = "banword {subcommand}{word}"
                            description = f"""
                                Toggles the use of the mood roles:
                                \t• If mood roles are currently enabled they will be disabled, and deleted from this server.
                                \t• If mood roles are currently disabled they will be enabled and automatically created.

                                You must be a server administrator to use this command.

                                **Example:**

                                • `{guildData.prefix}moderatesettings banword`
                                """
                        else:
                            match mots[3]:
                                case "add":
                                    title = "banword add <word>"
                                    description = f"""
                                        Adds a word to the list of banned words.
                                        \tYou must be a server administrator to use this command.
                                        \tIf the word is already in the list, a message will pop up saying the word is already in the list.

                                        **Exemples:**

                                        • `{guildData.prefix}banword add fuck`
                                        """
                                case "remove":
                                    title = "banword remove <word>"
                                    description = f"""
                                        Removes a word from the list of banned words.
                                        \tYou must be a server administrator to use this command.
                                        \tIf the word is not in the list, a message will pop up saying the word is not in the list.

                                        **Exemples:**
                                        • `{guildData.prefix}banword remove fuck`   
                                        """
                                case "print":
                                    title = "banword print"
                                    description = f"""
                                        Prints the list of banned words.
                                        \tYou must be a server administrator to use this command.

                                        **Exemples:**
                                        • `{guildData.prefix}banword print`  
                                        """
                                case "perm":
                                    title = "banword perm <user | group>"
                                    description = f"""
                                        Changes the permission level required to use a banned word.
                                        \tYou must be a server administrator to use this command.
                                        \tThe user or group must be mentioned, not just their name.
                                        \tIf the user or group is already in the list, their permission level will be removed.

                                        **Exemples:**
                                        • `{guildData.prefix}banword perm @user`
                                        • `{guildData.prefix}banword perm @group`
                                        """
                    case "perm":
                        if len(mots) == 3:
                            title = "perm {group}"
                            description = f"""
                                \t• adds a group to the list of authorized groups.
                                \t• removes a group from the list of authorized groups.
                                \t• this commands need to be used with a group mention.
                                \t• if the group is already in the list, it will be removed.
                                \t• if the group is not in the list, it will be added.
                                \t• you must be a server administrator to use this command.
                                \t• if your are the owner of the server, you can use this command.
                                
                                You must be a server administrator to use this command or the guild owner.
        
                                **Example:**
        
                                • `{guildData.prefix}moderatesettings perm @moderators`
                                """

        case "muteuser":
            if len(mots) == 2:
                title = "muteuser <user> <time>"
                description = f"""
                    Mutes a user for a given amount of time.
                    \tThe user will not be able to send messages in any channel of the server.
                    \tThe user will be able to send messages again after the given time has passed.
                    \tIf the user is already muted, the mute will be extended by the given time.
                    \tIf the user is already muted and the given time is 0, the mute will be removed.
                    \tYou must be a server administrator or a user with an authorized role to use this command.
                    \tThe user must be mentioned, not just their name.
                    \tThe time must be given following this rule : <number><type>.
                    \tThe type can be one of the following : m, h, d, w, M, y (y=year(s) ,M=month(s) ,w=week(s) ,d=day(s) ,m=minute(s)).

                    **Examples:**
                    • `{guildData.prefix}muteuser @user 1d`
                    • `{guildData.prefix}muteuser @user 1y5d69m`
                    """
        case "unmuteuser":
            if len(mots) == 2:
                title = "unmuteuser <user>"
                description = f"""
                    Unmutes a user.
                    \tThe user will be able to send messages in any channel of the server.
                    \tYou must be a server administrator or a user with an authorized role to use this command.
                    \tThe user must be mentioned, not just their name.
                    **Examples:**
                    • `{guildData.prefix}unmuteuser @user`
                    """
        case "ban":
            if len(mots) == 2:
                title = "ban <user>"
                description = f"""
                    Bans a user from the server.
                    \tThe user will not be able to join the server again.
                    \tYou must be a server administrator or a user with an authorized role to use this command.
                    \tThe user must be mentioned, not just their name.
                    **Examples:**
                    • `{guildData.prefix}ban @user`
                    """
        case "unban":
            if len(mots) == 2:
                title = "unban <user>"
                description = f"""
                    Unbans a user from the server.
                    \tThe user will be able to join the server again.
                    \tYou must be a server administrator or a user with an authorized role to use this command.
                    \tThe user must be mentioned, not just their name.
                    **Examples:**
                    • `{guildData.prefix}unban @user`
                    """
        case "kick":
            if len(mots) == 2:
                title = "kick <user>"
                description = f"""
                    Kicks a user from the server.
                    \tThe user will be able to join the server again.
                    \tYou must be a server administrator or a user with an authorized role to use this command.
                    \tThe user must be mentioned, not just their name.
                    **Examples:**
                    • `{guildData.prefix}kick @user`
                    """
        case "getinfo":
            if len(mots) == 2:
                title = "getinfo <user>"
                description = f"""
                    Gets the info on the user and his/her infractions 
                    \tYou must be a server administrator or a user with an authorized role to use this command.
                    \tThe user must be mentioned, not just their name.
                    **Examples:**
                    • `{guildData.prefix}getinfo @user`
                    """

        case _:
            bot.send_message(
                f"**{message.author.display_name}**, I couldn't find the command you asked for :/ (see {guildData.prefix}help)",
                message.channel)
            return

    embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
    asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)


# •=========•
#    TL;DR
# •=========•

async def tldrCommand(bot, message: discord.Message, guildData) -> None:
    """
    Summarizes a message.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :return: None
    """
    prefix: str = guildData.prefix

    if not message.content.startswith(prefix + 'tldr') and not message.content.startswith('tldr'):
        return

    messageBot = await message.reply("Summarizing...")

    args = message.content.split(' ')
    position = "around"
    quantity = "one"

    if len(args) > 1:
        args = args[1:]
        if "before" in args or "above" in args:
            position = "above"
        elif "after" in args or "below" in args:
            position = "below"

        if "all" in args or "every" in args:
            quantity = "all"

    if message.type == discord.MessageType.reply:
        message = await message.channel.fetch_message(
            message.reference.message_id)  # bot.fetchMessage(message.channel, message.reference.message_id)
    else:
        channel = message.channel
        message = [msg async for msg in channel.history(limit=2, before=message)][0]

    asyncio.run_coroutine_threadsafe(tldr.doTldr(bot, message, messageBot, quantity=quantity, position=position),
                                     bot.tldrLoop)


def tldrSettings(bot, message: discord.Message, guildData) -> None:
    """
    Changes the tldr settings.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :return: None
    """
    prefix = guildData.prefix
    mots = message.clean_content[len(prefix):].split()
    if len(mots) == 1:
        title = "tldrsettings"
        description = f"""
        • TLDR Time Gap: **{guildData.tldrTimeGap}** minutes 
        """

        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return

    if not message.author.guild_permissions.administrator:  # Only admins can change mood settings
        bot.send_message(
            f"**{message.author.display_name}**, you must be a server administrator to use this command :/",
            message.channel)
        return

    if len(mots) != 3:  # Not enough or too many arguments
        bot.send_message(
            f"**{message.author.display_name}**, you didn't put the right number of arguments (see {guildData.prefix}help moodsettings)",
            message.channel)
        return

    if mots[1] == "timegap":
        try:
            newTimeGap = int(mots[2])
        except ValueError:
            bot.send_message(f"**{message.author.display_name}**, the time gap must be an integer", message.channel)
            return
        if newTimeGap < 0:
            bot.send_message(f"**{message.author.display_name}**, the time gap must be positive", message.channel)
            return
        guildData.tldrTimeGap = newTimeGap
        bot.send_message(f"**{message.author.display_name}**, the time gap has been set to {newTimeGap} minutes",
                         message.channel)
        return


# •=================•
#    MOOD ANALYSIS
# •=================•
def moodCommand(bot, message, guildData) -> None:
    """
    Displays the mood of a user.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :return: None
    """
    mots = message.clean_content[len(guildData.prefix):].split()
    if len(mots) == 1:  # No user specified: target is message author
        try:
            bot.send_message(
                f"**{message.author.display_name}**, you are **{guildData.moods[message.author.id].moodName}**",
                message.channel)
        except KeyError:
            bot.send_message(f"**{message.author.display_name}**, you currently don't have any assigned mood",
                             message.channel)
        return
    elif len(message.mentions) != 0:  # A user was mentioned
        targetID = message.mentions[0].id
    else:  # A user id may have been specified
        try:
            targetID = int(mots[1])  # We check if the id is at least a number
        except ValueError:  # If not the id is not valid
            bot.send_message(
                f"**{message.author.display_name}**, please enter a valid id (see `{guildData.prefix}help mood`)",
                message.channel)
            return
    if targetID not in guildData.moods:  # If the target has no assigned mood ...
        try:  # ... but is on the server
            target = message.guild.get_member(targetID)
            bot.send_message(f"**{target.display_name}** has no assigned mood :/", message.channel)
            return
        except AttributeError:  # ... and isn't on the server
            bot.send_message(f"**{message.author.display_name}**, this user isn't on this server :/", message.channel)
            return
    # The user has an assigned mood
    bot.send_message(
        f"**{message.guild.get_member(targetID).display_name}** is **{guildData.moods[targetID].moodName}**",
        message.channel)


def moods(bot, message, guildData) -> None:
    """
    Displays the moods of all users.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :return: None
    """
    if len(guildData.moods) == 0:
        bot.send_message(
            f"**{message.author.display_name}**, no one here has an assigned mood, I can't create charts :/",
            message.channel)
        return
    # Generate the different lists for the bar chart
    names = [""] * len(mood.Mood)
    count = [0] * len(mood.Mood)
    colours = [""] * len(mood.Mood)
    for imood in mood.Mood:
        names[imood.position] = imood.moodName
        colours[imood.position] = str(imood.colour)
    for moodVal in guildData.moods.values():
        count[moodVal.position] += 1
    # Creates the bar chart
    barChart = plt.bar(names, count, color=colours)
    # Puts the value for each bar on top of it
    for bar in barChart:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, height, height, ha='center', va='bottom')
    # Saves the bar chart
    plt.title(f"Number of users per mood on {message.guild.name}")
    plt.savefig("mood_bar.png")
    plt.close()
    # Suppresses mood values at 0
    while 0 in count:
        index = count.index(0)
        count.pop(index)
        names.pop(index)
        colours.pop(index)
    # Percentage values for the pie chart
    percentages = [round(100 * count[i] / sum(count), 2) for i in range(len(count))]
    # Creates the pie chart
    fig, ax = plt.subplots()
    ax.pie(percentages, labels=names, colors=colours, autopct='%1.1f%%', startangle=90)
    # Saves the pie chart
    plt.title(f"Percentage of users per mood on {message.guild.name}")
    plt.savefig("mood_pie.png")
    plt.close()
    # Displays the images on Discord
    asyncio.run_coroutine_threadsafe(message.channel.send("Here's some charts about this server's moods!", files=(
        discord.File("image/mood_bar.png"), discord.File("image/mood_pie.png"))), bot.loop)


def moodsettings(bot, message, guildData, mots) -> None:
    """
    Displays or changes the mood settings.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The message's words.
    :return: None
    """
    if len(mots) == 1:  # No subcommand -> displays current state
        title = "Current mood settings"
        description = f"""
        • Mood refresh method:             **{'time-based refreshes' if guildData.timedMoodRefreshes else 'message-based refreshes'}**
        • Time between two mood refreshes: **{guildData.moodRefreshTime}** minutes
        • Time between two mood resets:    **{guildData.moodResetTime}** minutes
        • Message refresh threshold:       **{guildData.moodMessageThreshold}** messages
        • Message refresh depth:           **{guildData.moodMessageDepth}** messages
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return
    if not message.author.guild_permissions.administrator:  # Only admins can change mood settings
        bot.send_message(
            f"**{message.author.display_name}**, you must be a server administrator to use this command :/",
            message.channel)
        return
    if len(mots) != 3:  # Not enough or too many arguments
        bot.send_message(
            f"**{message.author.display_name}**, you didn't put the right number of arguments (see `{guildData.prefix}help moodsettings`)",
            message.channel)
        return
    match mots[1]:  # Switch according to the subcommand
        case "refreshmethod":
            moodsettings_refreshmethod(bot, message, guildData, mots)
        case "refreshtime":
            moodsettings_refreshtime(bot, message, guildData, mots)
        case "resettime":
            moodsettings_resettime(bot, message, guildData, mots)
        case "threshold":
            moodsettings_threshold(bot, message, guildData, mots)
        case "depth":
            moodsettings_depth(bot, message, guildData, mots)
        case _:
            bot.send_message(
                f"**{message.author.display_name}**, I couldn't recognise your command (see {guildData.prefix}help moodsettings)",
                message.channel)
            return


def moodsettings_refreshmethod(bot, message, guildData, mots) -> None:
    """
    Changes the mood refresh method.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The message's words.
    :return: None
    """
    match mots[2]:
        case '1':  # -> time-based mood updates
            if guildData.timedMoodRefreshes:
                answer = "This server already operates based on **time-based** mood refreshes :/"
            else:
                guildData.timedMoodRefreshes = True
                bot.moodUpdates[bot.moodUpdateMinute + guildData.moodRefreshTime].append((
                    message.guild.id,
                    True))
                answer = "This server now operates based on **time-based** mood refreshes."
        case '2':  # -> message-based mood updates
            if guildData.timedMoodRefreshes:
                guildData.timedMoodRefreshes = False
                for i in range(bot.moodUpdateMinute + 1, bot.moodUpdateMinute + guildData.moodRefreshTime + 1):
                    for updateQuery in bot.moodUpdates[i]:
                        if updateQuery[1] and updateQuery[0] == message.guild.id:
                            bot.moodUpdates[i].remove(updateQuery)
                            break
                answer = "This server now operates on **message-based** mood refreshes."
            else:
                answer = "This server already operates based on **message-based** mood refreshes :/"
        case _:  # Wrong input
            answer = f"Invalid mode. See `{guildData.prefix}help moodsettings refreshmethod`"
    bot.send_message(answer, message.channel)


def moodsettings_refreshtime(bot, message, guildData, mots) -> None:
    """
    Changes the time between two mood refreshes.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The message's words.
    :return: None
    """
    try:
        newValue = int(mots[2])
    except ValueError:
        bot.send_message(f"Please enter a number (`see {guildData.prefix}help moodsettings refreshtime`)",
                         message.channel)
        return
    if newValue > 180:
        bot.send_message("Mood updates can only be operated **up to 180 minutes**. Please enter a lower time.",
                         message.channel)
        return
    guildData.moodRefreshTime = newValue
    bot.send_message(
        f"Mood refreshes will now operate every **{newValue}** minutes (if this server operates on time-based refreshes)",
        message.channel)


def moodsettings_resettime(bot, message, guildData, mots) -> None:
    """
    Changes the time between two mood resets.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The message's words.
    :return: None
    """
    try:
        newValue = int(mots[2])
    except ValueError:
        bot.send_message(f"Please enter a number (see `{guildData.prefix}help moodsettings resettime`)",
                         message.channel)
        return
    if newValue > 180:
        bot.send_message("Mood updates can only be operated **up to 180 minutes**. Please enter a lower time.",
                         message.channel)
        return
    guildData.moodResetTime = newValue
    bot.send_message(f"Mood resets will now operate every **{newValue}** minutes", message.channel)


def moodsettings_threshold(bot, message, guildData, mots) -> None:
    """
    Changes the number of messages needed to compute a mood.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The message's words.
    :return: None
    """
    try:
        newValue = int(mots[2])
    except ValueError:
        bot.send_message(f"Please enter a number (see `{guildData.prefix}help moodsettings threshold`)",
                         message.channel)
        return
    guildData.moodMessageThreshold = newValue
    bot.send_message(
        f"Mood will now compute from **{newValue}** messages sent (if this server operates on message-based refreshes)",
        message.channel)


def moodsettings_depth(bot, message, guildData, mots) -> None:
    """
    Changes the number of messages to consider when computing a mood.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The message's words.
    :return: None
    """
    try:
        newValue = int(mots[2])
    except ValueError:
        bot.send_message(f"Please enter a number (see `{guildData.prefix}help moodsettings depth`)", message.channel)
        return
    guildData.moodMessageDepth = newValue
    bot.send_message(
        f"Mood will now compute from up to **{newValue}** last messages (if this server operates on message-based refreshes)",
        message.channel)


def moodroles(bot, message, guildData, mots) -> None:
    """
    Displays the mood roles status, or enables or disables them.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The message's words.
    :return: None
    """
    if len(mots) == 1:
        title = "Current mood roles status"
        description = f"""
        The mood roles are currently **{'enabled' if mood.rolesPresent(message.guild) else 'disabled'}**
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return
    if not message.author.guild_permissions.administrator:  # Only admins can change mood settings
        bot.send_message(
            f"**{message.author.display_name}**, you must be a server administrator to use this command :/",
            message.channel)
        return
    if len(mots) != 2:  # Not enough or too many arguments
        bot.send_message(
            f"**{message.author.display_name}**, you didn't put the right number of arguments (see `{guildData.prefix}help moodroles)`",
            message.channel)
        return
    match mots[1]:
        case "toggle":
            if mood.rolesPresent(message.guild):
                asyncio.run_coroutine_threadsafe(mood.removeRoles(bot, message.guild), bot.moodLoop)
                bot.send_message(f"Mood roles have been **disabled**", message.channel)
            else:
                asyncio.run_coroutine_threadsafe(mood.createRoles(bot, message.guild), bot.moodLoop)
                bot.send_message(f"Mood roles have been **enabled**", message.channel)
        case "reset":
            asyncio.run_coroutine_threadsafe(mood.removeRoles(bot, message.guild), bot.moodLoop)
            asyncio.run_coroutine_threadsafe(mood.createRoles(bot, message.guild), bot.moodLoop)
            bot.send_message(f"Mood roles have been **reset**", message.channel)
        case _:
            bot.send_message(
                f"The subcommand you asked for doesn't exit :/ (see `{guildData.prefix}help moodroles` for more help)",
                message.channel)


def moodtraining(bot, message, guildData, mots) -> None:
    """
    Displays the mood training status, or enables or disables it for the user.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The message's words.
    :return: None
    """
    if len(mots) == 1:
        title = "Current mood training status"
        description = f"""
        **{message.author.display_name}** mood training is currently **{'enabled' if guildData.moodTraining else 'disabled'} for you**
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return

    if len(mots) != 2:  # Not enough or too many arguments
        bot.send_message(
            f"**{message.author.display_name}**, you didn't put the right number of arguments (see `{guildData.prefix}help moodtraining)`",
            message.channel)
        return

    match mots[1]:
        case "toggle":
            guildData.moodTraining[message.author.id] = not guildData.moodTraining[message.author.id]
            bot.send_message(
                f"**{message.author.display_name}**, mood training has been **{'enabled' if guildData.moodTraining[message.author.id] else 'disabled'}** for you",
                message.channel)

        case "count":
            # Load dataset
            with open("data/emotion_dataset.csv", "r") as f:
                reader = csv.reader(f)
                data = list(reader)

            # Count the number of entries per emotion
            emotions = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise", "sleepiness"]
            counts = [len([x for x in data if x[1] == emotion]) for emotion in emotions]

            # Create the pie chart
            colours = [[str(m.colour) for m in mood.Mood if m.emotionName == emotion][0] for emotion in emotions]
            fig, ax = plt.subplots()
            ax.pie(counts, labels=emotions, colors=colours, autopct='%1.1f%%', startangle=90)
            ax.title.set_text("Percentage of dataset entries per emotion")

            # Center and save the pie chart
            ax.axis('equal')
            fig.tight_layout()
            plt.savefig("mood_pie.png")
            plt.close()

            # Create the embed
            title = "Current mood training dataset status"
            description = f"""
            **Number of entries:** __{len(data) - 1}__

            **Number of entries per emotion:**

            • Anger: **{counts[0]}** entries
            • Disgust: **{counts[1]}** entries
            • Fear: **{counts[2]}** entries
            • Joy: **{counts[3]}** entries
            • Neutral: **{counts[4]}** entries
            • Sadness: **{counts[5]}** entries
            • Sleepiness: **{counts[7]}** entries
            • Surprise: **{counts[6]}** entries

            Please focus on sending messages containing **{emotions[counts.index(min(counts))]}** :D

            **The pie chart below shows the percentage of entries per emotion:**
            """

            # Sends the embed
            embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
            image = discord.File("image/mood_pie.png", filename="image/mood_pie.png")
            embed.set_image(url="attachment://mood_pie.png")
            asyncio.run_coroutine_threadsafe(message.channel.send(file=image, embed=embed), bot.loop)
            return
        case _:
            bot.send_message(
                f"The subcommand you asked for doesn't exit :/ (see `{guildData.prefix}help moodtraining` for more help)",
                message.channel)


# •================•
#    SOCIAL GRAPH
# •================•
async def socialGraphCommand(bot, message: discord.Message, guildData) -> None:
    """
    Displays the social graph of the user, or of the mentioned user.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :return: None
    """
    prefix = guildData.prefix
    if message.content.startswith(prefix + "socialgraph"):
        command = message.content.replace(prefix + "socialgraph", "")
        args = command.strip().split(" ")
        if len(args) == 0:
            asyncio.run_coroutine_threadsafe(bot.socialGraphWorker.on_command_printall(message, bot),
                                             bot.socialGraphLoop)
        else:
            mentions = message.mentions
            if len(mentions) == 0:
                asyncio.run_coroutine_threadsafe(bot.socialGraphWorker.on_command_printall(message, bot),
                                                 bot.socialGraphLoop)
            else:
                # print(args)
                if len(args) == 1:
                    asyncio.run_coroutine_threadsafe(
                        bot.socialGraphWorker.on_command_printuser_distance(message, mentions[0].id, 2, bot),
                        bot.socialGraphLoop)
                else:
                    distance = args[1]
                    if distance == "all":
                        asyncio.run_coroutine_threadsafe(
                            bot.socialGraphWorker.on_command_printuser_all(message, mentions[0].id, bot),
                            bot.socialGraphLoop)
                    else:
                        try:
                            distance = int(distance)
                            if distance >= 0:
                                asyncio.run_coroutine_threadsafe(
                                    bot.socialGraphWorker.on_command_printuser_distance(message, mentions[0].id,
                                                                                        distance, bot),
                                    bot.socialGraphLoop)
                            else:
                                raise ValueError
                        except ValueError:
                            bot.send_message(
                                f"{message.author.display_name} please enter a valid distance :/ (see {prefix}help socialgraph)",
                                message.channel)
    if message.content.startswith(prefix + "importance"):
        command = message.content.replace(prefix + "importance", "")
        args = command.split(" ")

        while "" in args:
            args.remove("")

        if len(args) == 0:
            asyncio.run_coroutine_threadsafe(bot.socialGraphWorker.on_command_importance(message, message.author, bot),
                                             bot.socialGraphLoop)
        else:
            mentions = message.mentions
            if len(mentions) == 0:
                asyncio.run_coroutine_threadsafe(
                    bot.socialGraphWorker.on_command_importance(message, message.author, bot),
                    bot.socialGraphLoop)
            else:
                asyncio.run_coroutine_threadsafe(bot.socialGraphWorker.on_command_importance(message, mentions[0], bot),
                                                 bot.socialGraphLoop)
    if message.content.startswith(prefix + "sentiment"):
        command = message.content.replace(prefix + "sentiment", "")
        args = command.split(" ")

        while "" in args:
            args.remove("")

        if len(args) == 0:
            asyncio.run_coroutine_threadsafe(bot.socialGraphWorker.on_command_sentiment(message, message.author, bot),
                                             bot.socialGraphLoop)
        else:
            mentions = message.mentions
            if len(mentions) == 0:
                asyncio.run_coroutine_threadsafe(
                    bot.socialGraphWorker.on_command_sentiment(message, message.author, bot),
                    bot.socialGraphLoop)
            else:
                asyncio.run_coroutine_threadsafe(bot.socialGraphWorker.on_command_sentiment(message, mentions[0], bot),
                                                 bot.socialGraphLoop)


# •===========•
#    AUTOMOD
# •===========•
def moderatesettings(bot, message, guildData, mots) -> None:
    """
    Manages the moderation settings.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The words of the message.
    :return: None
    """
    permed = False
    if len(mots) == 1:
        title = "moderatesettings commands"
        description = f"""
        `{guildData.prefix}moderatesettings banword` - Manage the banned words
        `{guildData.prefix}moderatesettings banword add <word>` - Add a word to the banned words list
        `{guildData.prefix}moderatesettings banword remove <word>` - Remove a word from the banned words list
        `{guildData.prefix}moderatesettings banword print` - List the banned words
        `{guildData.prefix}moderatesettings banword perm <user | group>` - Set the permission level (for the user or group specified) for the banned words
        `{guildData.prefix}moderatesettings perm <@group>` - add a group to the moderation list 
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return
    roles = [role.id for role in message.author.roles]
    for role in roles:
        if role in guildData.moderators:
            permed = True
    if message.author.id == message.guild.owner_id:
        permed = True
    if (not permed):
        bot.send_message(
            f"**{message.author.display_name}**, you're not allowed to use this command :/",
            message.channel)
        return

    match mots[1]:
        case "banword":
            if len(mots) == 2:
                bot.send_message(
                    f"**{message.author.display_name}**, you didn't put the right number of arguments (see `{guildData.prefix}help moderatesettings`)",
                    message.channel)
                return
            match mots[2]:
                case "add":
                    asyncio.run_coroutine_threadsafe(mod.addBanword(bot, message, guildData), bot.autoModLoop)
                case "remove":
                    asyncio.run_coroutine_threadsafe(mod.removeBanword(bot, message, guildData), bot.autoModLoop)
                case "print":
                    asyncio.run_coroutine_threadsafe(mod.listBanword(bot, message, guildData), bot.autoModLoop)
                case "perm":
                    phrase = mod.permBanword(message, guildData)
                    bot.send_message(phrase, message.channel)
                case _:
                    bot.send_message(
                        f"**{message.author.display_name}**, I couldn't recognise your command (see {guildData.prefix}help moodsettings)",
                        message.channel)
                    return
        case "perm":
            if len(mots) == 2:
                bot.send_message(
                    f"**{message.author.display_name}**, you didn't put the right number of arguments (see `{guildData.prefix}help moderatesettings perm`)",
                    message.channel)
            if len(mots) == 3:
                mod.moderationAdd(message, guildData)
                return


@printExceptions
def muteuser(bot, message, guildData, mots) -> None:
    """
    Mutes a user.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The words of the message.
    :return: None
    """
    if len(mots) == 1:
        title = "Current mute status"
        # print all the muted users in this server in the description
        description = f"""
        `{guildData.prefix}muteuser <user>` - Mute a user
        `currently muted users in this server: {guildData.muted_user}`
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return

    authorPermed, targetPermed = checkPermissions(message, guildData)

    if authorPermed and targetPermed:
        bot.send_message(
            f"**{message.author.display_name}**, can't mute a mod as a mod:/",
            message.channel)
        return
    if not authorPermed:
        bot.send_message(
            f"**{message.author.display_name}**, you must be a server administrator to use this command :/",
            message.channel)
        return
    if len(message.mentions) == 0:
        bot.send_message(
            f"**{message.author.display_name}**, you didn't mention any user (see `{guildData.prefix}help muteuser)`",
            message.channel)
        return
    if message.mentions[0] in message.guild.members:
        # print("user is in the server")
        if mots[2] == "0":
            asyncio.run_coroutine_threadsafe(mod.unmuteUser1(bot, message, guildData), bot.autoModLoop)
        else:
            asyncio.run_coroutine_threadsafe(mod.muteuser(bot, message, guildData), bot.autoModLoop)

    else:
        bot.send_message(
            f"**{message.author.display_name}**, this user is already muted",
            message.channel)
        return


def automod(bot, message, guildData) -> None:
    """
    Automatically moderates the message.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :return: None
    """
    asyncio.run_coroutine_threadsafe(mod.automod(message, guildData), bot.loop)


def unmuteUser(bot, message, guildData, mots) -> None:
    """
    Unmutes a user.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The words of the message.
    :return: None
    """
    if len(mots) == 1:
        title = "Current mute status"
        # print all the muted users in this server in the description
        mutedUsersString = "\n"
        for user in guildData.muted_users:
            mutedUsersString += f"{guildData.displayName[user]} muted for {guildData.muted_users[user][0]} minutes\n"

        description = f"""
        `{guildData.prefix}unmuteuser <user>` - Unmute a user
        `currently muted users in this server: {mutedUsersString}`
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return

    authorPermed = False
    roles = [role.id for role in message.author.roles]

    for role in roles:
        if role in guildData.moderators:
            authorPermed = True

    if message.author.id == message.guild.owner_id:
        authorPermed = True

    if not authorPermed:
        bot.send_message(
            f"**{message.author.display_name}**, you must be a server administrator to use this command :/",
            message.channel)
        return

    if len(message.mentions) == 0:
        bot.send_message(
            f"**{message.author.display_name}**, you didn't mention any user (see `{guildData.prefix}help muteuser)`",
            message.channel)
        return

    if message.mentions[0].id in guildData.muted_users:
        asyncio.run_coroutine_threadsafe(mod.unmuteUser1(bot, message, guildData), bot.loop)

    return


def kickUser(bot, message, guildData, mots) -> None:
    """
    Kicks a user.
    :param bot: The bot.
    :param message: The message.
    :param guildData: The guild data.
    :param mots: The words of the message.
    :return: None
    """
    if len(mots) == 1:
        title = "Current kick status"
        # print all the muted users in this server in the description
        description = f"""
        `{guildData.prefix}kickuser <user>` - Kick a user
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return
    authorPermed, targetPermed = checkPermissions(message, guildData)
    if authorPermed and targetPermed:
        bot.send_message(
            f"**{message.author.display_name}**, can't kick a mod as a mod:/",
            message.channel)
        return
    if not authorPermed:
        bot.send_message(
            f"**{message.author.display_name}**, you must be a server administrator to use this command :/",
            message.channel)
        return
    if len(message.mentions) == 0:
        bot.send_message(
            f"**{message.author.display_name}**, you didn't mention any user (see `{guildData.prefix}help kick)`",
            message.channel)
        return
    if message.mentions[0] in message.guild.members:
        asyncio.run_coroutine_threadsafe(mod.kickUser(bot, message, guildData), bot.loop)
        if len(mots) == 3:
            asyncio.run_coroutine_threadsafe(mod.addInfoInFile(bot, message, mots[3], bot.loop))
        else:
            asyncio.run_coroutine_threadsafe(mod.addInfoInFile(bot, message, "No reason specified", bot.loop))
    return


def banUser(bot, message, guildData, mots):
    if len(mots) == 1:
        title = "Current ban status"
        # print all the muted users in this server in the description
        description = f"""
        `{guildData.prefix}banuser <user>` - Ban a user
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return
    authorPermed, targetPermed = checkPermissions(message, guildData)
    if authorPermed and targetPermed:
        bot.send_message(
            f"**{message.author.display_name}**, can't ban a mod as a mod:/",
            message.channel)
        return
    if not authorPermed:
        bot.send_message(
            f"**{message.author.display_name}**, you must be a server administrator to use this command :/",
            message.channel)
        return
    if len(message.mentions) == 0:
        bot.send_message(
            f"**{message.author.display_name}**, you didn't mention any user (see `{guildData.prefix}help ban)`",
            message.channel)
        return
    if message.mentions[0] in message.guild.members:
        asyncio.run_coroutine_threadsafe(mod.banUser(bot, message, guildData), bot.loop)
    return


def unbanUser(bot, message, guildData, mots):
    if len(mots) == 1:
        title = "Current unban status"
        # print all the muted users in this server in the description
        description = f"""
        `{guildData.prefix}unbanuser <user>` - Unban a user
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return
    authorPermed, targetPermed = checkPermissions(message, guildData)
    if not authorPermed:
        bot.send_message(
            f"**{message.author.display_name}**, you must be a server administrator to use this command :/",
            message.channel)
        return
    if len(message.mentions) == 0:
        bot.send_message(
            f"**{message.author.display_name}**, you didn't mention any user (see `{guildData.prefix}help unban)`",
            message.channel)
        return
    if message.mentions[0] in message.guild.members:
        asyncio.run_coroutine_threadsafe(mod.unbanUser(bot, message, guildData), bot.loop)
    return

def getUserInfo(bot, message, guildData, mots):
    if len(mots) == 1:
        title = "Current getUserInfo status"
        # print all the user info in this server
        description = f"""
        `{guildData.prefix}getUserInfo <user>` - get the info of the user in this server
        """
        embed = discord.Embed(title=title, description=description, colour=discord.Colour.light_gray())
        asyncio.run_coroutine_threadsafe(message.channel.send(embed=embed), bot.loop)
        return
    authorPermed, targetPermed = checkPermissions(message, guildData)
    if not authorPermed:
        bot.send_message(
            f"**{message.author.display_name}**, you must be a server administrator to use this command :/",
            message.channel)
        return
    if len(message.mentions) == 0:
        bot.send_message(
            f"**{message.author.display_name}**, you didn't mention any user (see `{guildData.prefix}help unban)`",
            message.channel)
        return
    if message.mentions[0] in message.guild.members:
        asyncio.run_coroutine_threadsafe(mod.getInfractionInfo(bot, message, guildData), bot.loop)
    return

def checkPermissions(message, guildData):
    authorPermed = False
    targetPermed = False

    roles = [role.id for role in message.author.roles]
    for role in roles:
        if role in guildData.moderators:
            authorPermed = True
    if message.author.id == message.guild.owner_id:
        authorPermed = True

    roles = [role.id for role in message.mentions[0].roles]
    for role in roles:
        if role in guildData.moderators:
            targetPermed = True
    if message.mentions[0].id == message.guild.owner_id:
        targetPermed = True
    return authorPermed, targetPermed
