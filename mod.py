import asyncio
import datetime
import json
import os
import re

import discord

from utils import printExceptions


class moderationInfo:
    """
    Class to store moderation data
    """

    def __init__(self, moderation_data):
        self.moderation_data = moderation_data


async def automod(message, guildData):
    """
    Processes auto moderation, on_message event
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """
    # print("yep")
    bannedWords = guildData.badWords
    if bannedWords is None:
        bannedWords = []
    for bad_word in bannedWords:
        if bad_word in message.content:
            addInfoInFile(message.mentions[0].id, message.guild.id, "tag", "Banned word detected")
            await message.delete()
            await message.channel.send(f"Banned word detected, {message.author.mention}")


@printExceptions
async def addBanword(bot, message, guildData):
    """
    Adds a banned word to the list
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """
    # print('add')
    bannedWord = message.content.split(' ')[3]
    listBannedWords = guildData.badWords
    if listBannedWords is None:
        listBadWords = []
    if bannedWord in listBadWords:
        asyncio.run_coroutine_threadsafe(message.channel.send('Bad word already in list'), bot.loop)
        return
    listBadWords.append(bannedWord)
    asyncio.run_coroutine_threadsafe(message.channel.send('Bad word added'), bot.loop)
    return


@printExceptions
async def removeBanword(bot, message, guildData):
    """
    Removes a banned word from the list
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """
    # print('remove')
    bannedWord = message.content.split(' ')[3]
    list_banned_words = guildData.badWords
    if list_banned_words is None:
        list_banned_words = []
    if bannedWord not in list_banned_words:
        asyncio.run_coroutine_threadsafe(message.channel.send('Bad word not in list'), bot.loop)
        return
    list_banned_words.remove(bannedWord)
    # message.channel.send('Bad word removed')
    asyncio.run_coroutine_threadsafe(message.channel.send('Bad word removed'), bot.loop)
    return


@printExceptions
async def listBanword(bot, message, guildData):
    """
    Lists the banned words
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """

    # print('list')
    list_banned_words = guildData.badWords
    if list_banned_words is None:
        list_banned_words = []
    asyncio.run_coroutine_threadsafe(message.channel.send('Bad words list:'), bot.loop)
    phrase = ''
    for word in list_banned_words:
        phrase += word + ', '
    asyncio.run_coroutine_threadsafe(message.channel.send(phrase), bot.loop)
    return


@printExceptions
def moderationAdd(message, guildData):
    """
    Adds a moderator role
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """
    # print("Hello yes it me I am here")
    # print(message)
    # print(guildData)
    if len(message.role_mentions) > 0:
        if message.role_mentions[0].id not in guildData.moderators:
            guildData.moderators.append(message.role_mentions[0].id)
            # print('moderator group added')
            return "Moderator added"
        elif message.role_mentions[0].id in guildData.moderators:
            guildData.moderators.remove(message.role_mentions[0].id)
            # print('moderator group revoked')
            return "Moderator revoked"
        # print('no user mentionned')


@printExceptions
def permBanword(message, guildData):
    """
    Adds a permission role
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """
    users = [user.id for user in message.guildData.members]
    roles = [role.id for role in message.guildData.roles]
    if len(message.mentions) > 0:
        # message.roles is not None
        if message.mentions[0].id in users:
            if message.mentions[0].id not in guildData.permUser:
                guildData.permUser.append(message.mentions[0].id)
                # print('user permission granted')
                # await message.channel.send(f"**{message.guild.get_role(message.mentions[0].id).name}**")
                return "Permissions granted"
            elif message.mentions[0].id in guildData.permUser:
                # print('user permission revoked')
                guildData.permUser.remove(message.mentions[0].id)
                return "Permissions revoked"
        # print(message.role_mentions)

    if len(message.role_mentions) > 0:
        if message.role_mentions[0].id in roles:
            if message.role_mentions[0].id not in guildData.permGroup:
                guildData.permGroup.append(message.role_mentions[0].id)
                # print('role permission granted')
                # await message.channel.send(f"**{message.guild.get_role(message.mentions[0].id).name}**")
                return "Permissions granted"
            elif message.role_mentions[0].id in guildData.permGroup:
                # print('role permission revoked')
                guildData.permGroup.remove(message.role_mentions[0].id)
                return "Permissions revoked"
        # print('no role mentionned')
    # await message.channel.send("you do not have permission to do that")


@printExceptions
async def muteuser(bot, message, guildData):
    """
    Mutes a user
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """

    # print('muteuser')
    user = message.mentions[0]
    userID = user.id
    # print(userID)

    # if the time is 0, the user is unmuted
    # print(type(message.mentions[0]))
    if message.content.split(' ')[2] == '0':
        if str(userID) in guildData.muted_users.keys():
            await unmuteUser1(bot, message, guildData)
            return
    # print('mute')
    # print(guildData.muted_users)
    if str(userID) in guildData.muted_users.keys():
        # print('already muted')
        return
    # print('try to mute')
    if message.content.split(' ')[2] != '0':
        message_content = message.content
        arguments = re.split('\s+', message_content)[2:]
        # print(arguments)
        # define a dictionary of time unit multipliers in seconds
        time_units = {'y': 31536000, 'M': 2592000, 'w': 604800, 'd': 86400, 'h': 3600, 'm': 60}

        # define a regular expression pattern to extract the values for each time unit
        pattern = r'(?:(?P<y>\d+)y)?(?:(?P<M>\d+)M)?(?:(?P<w>\d+)w)?(?:(?P<d>\d+)d)?(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?'

        # use the pattern to match and extract the values from the phrase
        match = re.match(pattern, arguments[0])

        # loop over the named groups in the match object and convert each time unit to seconds
        time_seconds = 0
        for name, value in match.groupdict().items():
            if value is not None:
                time_seconds += int(value) * time_units[name]

        # convert time in seconds to minutes
        time_minutes = round(time_seconds / 60)
        # add all roles except @everyone to a list

        rolesids = [role.id for role in message.guild.get_member(userID).roles]
        # print(f"Taille : {len(rolesids)}")
        guildData.muted_users[userID] = [time_minutes, rolesids]

        # add the role called MUTED to the user
        roleM = discord.utils.get(message.guild.roles, name="MUTED")
        asyncio.run_coroutine_threadsafe(message.guild.get_member(userID).add_roles(roleM), bot.loop).result()

        # remove all roles from the user
        rolesToRemove = [role for role in message.guild.get_member(userID).roles if
                         role.name not in {"@everyone", "MUTED"}]
        # print(rolesToRemove)
        if rolesToRemove != []:
            for role in rolesToRemove:
                asyncio.run_coroutine_threadsafe(message.guild.get_member(userID).remove_roles(role), bot.loop).result()

        addInfoInFile(message.mentions[0].id, message.guild.id, "muted", "muted by " + message.author.name)

        bot.save()
        # print('muted')
        bot.send_message(f"**{message.mentions[0]}** has been muted for {time_minutes} minutes", message.channel)
    else:
        bot.send_message(f"**{message.mentions[0]}** is already muted", message.channel)


async def unmuteUser1(bot, message, guildData) -> None:
    """
    Unmutes a user
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """

    member = message.mentions[0]
    roles = [i for i in member.roles if i.name != "@everyone"]

    asyncio.run_coroutine_threadsafe(member.remove_roles(*roles), bot.loop)

    roleToAdd = guildData.muted_users[member.id][1]
    roleToAdd = [message.guild.get_role(roleId) for roleId in roleToAdd]
    roleToAdd = [role for role in roleToAdd if role is not None and role.name != "MUTED" and role.name != "@everyone"]
    asyncio.run_coroutine_threadsafe(member.add_roles(*roleToAdd), bot.loop)

    del guildData.muted_users[member.id]
    bot.save()
    bot.send_message(f"**{member}** has been unmuted", message.channel)


@printExceptions
def unmuteUser(bot, guildId, userID) -> None:
    """
    Unmutes a user
    :param bot: the bot
    :param guildId: the id of the guild the user is in
    :param userID: the id of the user to unmute
    :return: None
    """
    guildData = bot.guildsDict[guildId]
    thisGuild = bot.get_guild(guildId)
    member = discord.utils.get(thisGuild.members, id=int(userID))
    # print(f"Unmuting {member}")

    mutedRole = discord.utils.get(thisGuild.roles, name="MUTED")
    asyncio.run_coroutine_threadsafe(member.remove_roles(mutedRole), bot.loop)

    rolesToAdd = [role for role in thisGuild.roles if role.id in guildData.muted_users[userID][1]]
    for role in rolesToAdd:
        if (role.name != "@everyone") and (role.name != "MUTED"):
            # print(role)
            asyncio.run_coroutine_threadsafe(member.add_roles(role), bot.loop).result()
    del guildData.muted_users[userID]
    bot.save()


@printExceptions
async def updateMuted(bot):
    """
    Decrements the time of all the muted users for every minute
    :param bot: the bot to decrement the time for
    :return: None
    """
    # print("------------------")
    for guildID, guildData in bot.guildsDict.items():
        for userID, valInMutedUser in guildData.muted_users.items():
            valInMutedUser[0] -= 1
            bot.save()
            if valInMutedUser[0] <= 0:
                # print("Here :D")
                await unmuteUser(bot, guildID, userID)
        bot.save()


@printExceptions
async def createRole(bot, guild: discord.Guild) -> None:
    """
    Creates the different mood roles
    :param bot: the bot
    :param guild: the guild to put the roles in
    :return: None
    """
    # Creation of the role
    asyncio.run_coroutine_threadsafe(guild.create_role(name="MUTED", colour=discord.Colour.default(), mentionable=True),
                                     bot.loop).result()
    role = discord.utils.get(guild.roles, name="MUTED")
    asyncio.run_coroutine_threadsafe(role.edit(permissions=discord.Permissions.none()), bot.loop)


@printExceptions
def rolesPresent(guild: discord.Guild):
    """
    Checks if the mood roles are already on the guild
    :param guild: the guild to check
    :return: True if the roles are present, False if not
    :rtype: bool
    """
    for role in guild.roles:
        if role.name == "MUTED":
            return True
    return False


@printExceptions
async def banUser(bot, message, arguments):
    """
    Bans a user
    :param bot: the bot
    :param message: the message that called the command
    :param arguments: the arguments of the command
    :return: None
    """
    asyncio.run_coroutine_threadsafe(message.guild.ban(message.mentions[0], reason=arguments), bot.loop)
    addInfoInFile(message.mentions[0].id, message.guild.id, "ban", arguments)
    bot.send_message(f"**{message.mentions[0]}** has been banned for {arguments}", message.channel)
    bot.save()


@printExceptions
async def unbanUser(bot, message, arguments):
    """
    Unbans a user
    :param bot: the bot
    :param message: the message that called the command
    :param arguments: the arguments of the command
    :return: None
    """
    asyncio.run_coroutine_threadsafe(message.guild.unban(message.mentions[0], reason=arguments), bot.loop)
    bot.send_message(f"**{message.mentions[0]}** has been unbanned for {arguments}", message.channel)
    bot.save()


@printExceptions
async def kickUser(bot, message, arguments):
    """
    Kicks a user
    :param bot: the bot
    :param message: the message that called the command
    :param arguments: the arguments of the command
    :return: None
    """
    asyncio.run_coroutine_threadsafe(message.guild.kick(message.mentions[0], reason=arguments), bot.loop)
    addInfoInFile(message.mentions[0].id, message.guild.id, "kicks", arguments)
    bot.send_message(f"**{message.mentions[0]}** has been kicked for {arguments}", message.channel)
    bot.save()


@printExceptions
def addInfoInFile(userID, guild: discord.Guild, infractionInfo, reason) -> None:
    """
    Adds the guild to the bot's file
    :param userID: int:the id of the user
    :param guild: discord.Guild: the guild to add
    :param infractionInfo: str: the type of infraction
    :param reason: str:the reason of the infraction
    :return: None
    """
    # Check if the file exists
    if not os.path.exists("data/userInfo.json"):
        with open('data/userInfo.json', 'w') as f:
            json.dump({}, f, indent=4)

    with open('data/userInfo.json', 'r') as f:
        dataUser = {int(k): {int(kk): vv for (kk, vv) in v.items()} for (k, v) in json.load(f).items()}

    current_time = datetime.datetime.now()
    local_time = current_time.strftime("%d/%m/%Y %H:%M:%S")

    if guild not in dataUser:
        dataUser[guild] = {}

    if userID not in dataUser[guild]:
        dataUser[guild][userID] = {}

    if infractionInfo not in dataUser[guild][userID]:
        dataUser[guild][userID][infractionInfo] = {}

    dataUser[guild][userID][infractionInfo][reason] = local_time

    with open('data/userInfo.json', 'w') as f:
        json.dump(dataUser, f, indent=4)


@printExceptions
def getInfractionInfo(userID, guildID):
    """
    Gets the infraction info of a user
    :param userID: the user ID
    :param guildID: the guild ID
    :return: the infraction info
    """
    try:
        with open('data/userInfo.json', 'r') as f:
            dataUser = json.load(f)
    finally:
        data = dataUser[guildID][userID]
    bot.send_message(f"**Current Info on {message.mentions[0]}**: {data}", message.channel)


@printExceptions
def getUserInfoInEveryServer(userID):
    """
    Gets the info of a user in every server
    :param userID: the user ID
    :return: the info of the user in every server
    """
    try:
        with open('data/userInfo.json', 'r') as f:
            dataUser = json.load(f)
    finally:
        data = []
        for guild in dataUser:
            if str(userID) in dataUser[guild]:
                data.append(dataUser[guild][userID])
    return data
