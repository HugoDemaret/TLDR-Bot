import asyncio
import json
import os
import time
from threading import Thread

import discord
from dotenv import load_dotenv

import messageProcess
import mod
import mood
import socialGraph
import utils

load_dotenv()


class GuildData:
    def __init__(self, id, prefix, consentChannelId, consentMessageId, timedMoodRefreshes, moodRefreshTime,
                 moodResetTime, moodMessageThreshold, moodMessageDepth, moodTraining, tldrTimeGap, badWords, permUser,
                 permGroup, muted_users, moderators):  # , every other settings):
        """
        Constructor
        :param id: the guild's ID
        :param prefix: the guild's prefix
        :param consentChannelId: id of the channel which contains the consent message
        :param consentMessageId: id of the consent message
        :param timedMoodRefreshes: True if server operates on time-based mood refreshes, False if it operates on message-based
        :param moodRefreshTime: time between two mood refreshes
        :param moodResetTime: time between two resets
        :param moodMessageThreshold: number of messages for mood to start computing
        :param moodMessageDepth: maximum number of messages considered for mood
        :param moodTraining: links userIDs to whether their messages will be used for training (defaults to True)
        :param tldrTimeGap: time between two messages to be considered as part of the same conversation, in minutes
        :param badWords: list of bad words
        :param permUser: list of users with permanent access to the bot
        :param permGroup: list of roles with permanent access to the bot
        :param muted_users: list of users who are muted
        """
        self.id = id
        self.prefix = prefix
        self.displayName = dict()
        self.users = set()
        self.consentMessageId = consentMessageId
        self.consentChannelId = consentChannelId
        # every other settings

        # •===========================•
        #        Mood Parameters
        # •===========================•

        self.moods: dict[int, mood.Mood] = {}  # Links userIDs to their assigned mood (no mood -> not in here)
        self.userMessages: dict[int, list[str]] = {}  # Links userIDs to their last messages' contents
        #  • Up to moodMessageDepth messages if message-based refresh
        #  • Messages since last refresh if time-based refreshes
        self.userActive: dict[
            int, bool] = {}  # Links userIDs to a boolean (whether they've been active since last mood reset, not in here -> inactive)
        self.timedMoodRefreshes = timedMoodRefreshes  # True if time-based refreshed, False if message-based
        # Time-based refreshes:
        self.moodRefreshTime = moodRefreshTime  # Time between two mood refreshes
        self.moodResetTime = moodResetTime  # Time between two resets
        # Message-based refreshes:
        self.moodMessageThreshold = moodMessageThreshold  # Number of messages for mood to start computing
        self.moodMessageDepth = moodMessageDepth  # Maximum number of messages considered for mood
        self.moodTraining: dict[int, bool] = {int(k): v for k, v in
                                              moodTraining.items()}  # Links userIDs to whether their messages will be used for training (defaults to True)
        self.emotionCheckMessages: dict[
            int, mood.Mood] = {}  # List of messages whose emotion is to be checked, and their associated mood

        # •===========================•
        #       TLDR Parameters
        # •===========================•

        self.tldrTimeGap = tldrTimeGap  # Time between two messages to be considered as part of the same conversation, in minutes

        # •===========================•
        #    Social Graph Parameters
        # •===========================•

        # •===========================•
        #      AutoMod Parameters
        # •===========================•

        self.badWords = badWords
        self.permUser = permUser
        self.permGroup = permGroup
        self.muted_users = {int(k): v for (k, v) in muted_users.items()}
        self.moderators = moderators

    def toDict(self) -> dict:
        """
        Returns a dict representation of the object
        :return: dict
        """
        return {
            'id':                   self.id,
            'prefix':               self.prefix,
            'consentMessageId':     self.consentMessageId,
            'consentChannelId':     self.consentChannelId,
            # every other settings
            'timedMoodRefreshes':   self.timedMoodRefreshes,
            'moodRefreshTime':      self.moodRefreshTime,
            'moodResetTime':        self.moodResetTime,
            'moodMessageThreshold': self.moodMessageThreshold,
            'moodMessageDepth':     self.moodMessageDepth,
            'moodTraining':         self.moodTraining,
            'tldrTimeGap':          self.tldrTimeGap,
            'badWords':             list(self.badWords),
            'permUser':             list(self.permUser),
            'permGroup':            list(self.permGroup),
            'muted_users':          self.muted_users,
            'moderators':           list(self.moderators),
        }


class Bot(discord.Client):
    """
    The bot class inherits from discord.Client
    :guidsId: a set of all guilds id the bot is in
    :guildsDict: a dict of all guildData the bot is in, with the guild id as key
    :tldrLoop: the loop for the tldr command
    :moodLoop: the loop for the mood command
    :socialGraphLoop: the loop for the social graph command
    :autoModLoop: the loop for the auto mod command
    :moodUpdates: a list of list of tuples (guildId, updateType) where updateType is True for refresh and False for reset
    :moodUpdateMinute: the current minute of the "clock" used to know when to update the moods
    :socialGraphWorker: the worker for the social graph command
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.guildsId: set[int] = set()
        self.guildsDict: dict[int, GuildData] = dict()

        self.tldrLoop = asyncio.new_event_loop()
        self.moodLoop = asyncio.new_event_loop()
        self.socialGraphLoop = asyncio.new_event_loop()
        self.autoModLoop = asyncio.new_event_loop()

        self.moodUpdates: list[list[tuple[int, bool]]] = [[] for _ in range(181)]
        # See it as a "clock" with the current minute pointing to a slot. Each minute we move on to the next slot.
        # If a guild's moods are to be refreshed/reset n minutes from now you will put a tuple (guildID, updateType) in
        #  the nth slot from the current one. -> when getting to a slot process all such tuples in it
        # updateType : True for refresh, False for reset
        # 181 slots -> you can put next mood refresh/reset at most 3 hours from now
        self.moodUpdateMinute: int = 0  # Current minute of the "clock"
        # SocialGraph
        self.socialGraphWorker = None

    async def on_ready(self) -> None:
        """
        Called when the bot is ready
        :return: None
        """

        # Get guilds ids and metadata from json
        try:
            with open('data/guilds.json', 'r') as f:
                data = json.load(f)
        except:
            data = {
                "guildsId":   [],
                "guildsDict": {}
            }

        self.guildsId = set(data["guildsId"])
        self.guildsDict = data["guildsDict"]

        temp = dict()
        for id in self.guildsDict:
            temp[int(id)] = GuildData(**self.guildsDict[id])
        self.guildsDict = temp
        del temp

        # print(self.guildsDict,self.guildsId)
        self.socialGraphWorker = socialGraph.SocialGraphWorker()

        # check for new guilds
        for guild in self.guilds:
            if guild.id not in self.guildsId:
                await self.guild_added(guild)

        # check for removed guilds
        actualGuildsId = {guild.id for guild in self.guilds}
        for id in self.guildsId:
            if id not in actualGuildsId:
                guild = await self.fetch_guild(id)
                await self.on_guild_remove(guild)

        self.save()

        # update users
        await self.fetch_reaction()

        print('Logged on as', self.user)

        for id in self.guildsDict:
            guildData = self.guildsDict[id]
            print(guildData.id)
            for user in guildData.users:
                print(str(user.id))

        # Load social graph
        await self.initialise_social_graphs()

        for guildID in self.guildsId:
            refreshTime, resetTime = self.guildsDict[guildID].moodRefreshTime, self.guildsDict[guildID].moodResetTime
            if self.guildsDict[guildID].timedMoodRefreshes:
                self.moodUpdates[refreshTime].append((guildID, True))
            self.moodUpdates[resetTime].append((guildID, False))

        # Launch loop threads for each section
        loops = [self.tldrLoop, self.moodLoop, self.socialGraphLoop, self.autoModLoop]
        for loop in loops:
            Thread(target=lambda x: x.run_forever(), args=(loop,), daemon=True).start()

        # Launches mood updates clock
        Thread(target=self.timeLoop, daemon=True).start()

        # Resets the mood roles for each guild
        for guildID in self.guildsId:
            guild = self.get_guild(guildID)
            asyncio.run_coroutine_threadsafe(mood.resetRoles(self, guild), self.moodLoop)

        # Catches up on new users whose mood training setting hasn't been initialised yet
        for guildID in self.guildsId:
            guildData = self.guildsDict[guildID]
            for user in guildData.users:
                if user.id not in guildData.moodTraining:
                    guildData.moodTraining[user.id] = False
        self.save()

        # check if the muted role is present and create it if not
        for guildID in self.guildsId:
            guild = self.get_guild(guildID)
            if not mod.rolesPresent(guild):
                asyncio.run_coroutine_threadsafe(mod.createRole(self, guild), self.autoModLoop)

    def save(self):
        data = {
            "guildsId":   list(self.guildsId),
            "guildsDict": {id: guildData.toDict() for id, guildData in self.guildsDict.items()}
        }
        with open('data/guilds.json', 'w') as f:
            json.dump(data, f, indent=4)

    async def initialise_social_graphs(self) -> None:
        """
        Loads the social graphs from a json file and initialises the social graph worker
        :return: None
        """
        try:
            with open('data/social_graphs.json', 'r') as f:
                data = json.load(f)
        except:
            data = {}

        asyncio.run_coroutine_threadsafe(
            socialGraph.initiate_graph_worker(self.socialGraphWorker,
                                              data,
                                              self.guildsId,
                                              self.guildsDict
                                              ),
            self.socialGraphLoop
        )

    async def on_message(self, message) -> None:
        """
        Called when a message is sent in a channel the bot can see
        :param message: The message sent
        :return: None
        """
        if message.author == self.user or message.author.bot:  # First part useless? self.user is bot
            return

        guildId = message.guild.id
        guildData = self.guildsDict[guildId]

        if message.author not in guildData.users:
            return

        message.content = utils.toEnglish(message.clean_content)
        # await message.channel.send(f"Language: {utils.getLanguage(message.clean_content)}, Message: {message.content}")

        # message.content = message.content.lower()

        await messageProcess.on_messageDiscord(self, message, guildData)
        await messageProcess.on_messageTldr(self, message, guildData)
        messageProcess.on_messageMood(self, message, guildData)
        await messageProcess.on_messageSocialGraph(self, message, guildData)
        messageProcess.on_messageAutoMod(self, message, guildData)

    async def on_message_edit(self, before, after) -> None:
        """
        Called when a message is edited
        :param before: The message before it was edited
        :param after: The message after it was edited
        :return: None
        """
        await self.on_message(after)

    async def on_raw_reaction_add(self, payload) -> None:
        """
        Called when a reaction is added
        :param payload: The payload of the reaction
        :return: None
        """

        user = await self.fetch_user(payload.user_id)

        if user == self.user or (user not in self.users) or user.bot:
            return

        guildId = payload.guild_id
        guildData = self.guildsDict[guildId]

        consentChannelId = guildData.consentChannelId
        consentMessageId = guildData.consentMessageId

        if payload.channel_id == consentChannelId and payload.message_id == consentMessageId:
            guildData.users.add(user)
            guildData.displayName[user.id] = user.display_name
            # add the user to the socialgraph
            asyncio.run_coroutine_threadsafe(self.socialGraphWorker.add_user(user, guildData), self.socialGraphLoop)
            guildData.moodTraining[user.id] = False
            self.save()

        # Process emotion messages reaction

        messageID = payload.message_id

        try:
            message = await self.get_channel(payload.channel_id).fetch_message(messageID)
        except discord.errors.NotFound:
            return

        reference = message.reference

        if reference is None:
            return

        reference = reference.resolved

        try:
            referencedMessage = await reference.fetch()
        except discord.errors.NotFound:
            return

        if messageID in guildData.emotionCheckMessages:
            emoji = payload.emoji.name
            if emoji == "✅":
                emotion = guildData.emotionCheckMessages[messageID].emotionName
                mood.addCSV(utils.toEnglish(referencedMessage.clean_content), emotion)
            elif emoji == "➡️":
                for emoji in [m.emoji for m in mood.Mood]:
                    try:
                        await message.add_reaction(emoji)
                    except discord.errors.NotFound:
                        pass
                return
            elif emoji in [m.emoji for m in mood.Mood]:
                emotion = [m.emotionName for m in mood.Mood if m.emoji == emoji][0]
                mood.addCSV(utils.toEnglish(referencedMessage.clean_content), emotion)

            try:
                await message.delete()
            except discord.errors.NotFound:
                pass
            guildData.emotionCheckMessages.pop(messageID)

    async def on_raw_reaction_remove(self, payload) -> None:
        """
        Called when a reaction is removed
        :param payload: The payload of the reaction
        :return: None
        """

        user = await self.fetch_user(payload.user_id)

        if user == self.user or (user not in self.users) or user.bot:
            return

        guildId = payload.guild_id
        guildData = self.guildsDict[guildId]

        consentChannelId = guildData.consentChannelId
        consentMessageId = guildData.consentMessageId

        if payload.channel_id != consentChannelId or payload.message_id != consentMessageId:
            return

        guildData.users.remove(user)
        guildData.moodTraining.pop(user.id)
        guildData.displayName.pop(user.id)
        asyncio.run_coroutine_threadsafe(self.socialGraphWorker.remove_user(user, guildData), self.socialGraphLoop)

    async def fetch_reaction(self) -> None:
        """
        Fetches the reaction of the consent message
        :return: None
        """
        for id in self.guildsId:
            guildData = self.guildsDict[id]
            chan = await self.fetch_channel(guildData.consentChannelId)
            print(id)
            message = await chan.fetch_message(guildData.consentMessageId)
            reaction = message.reactions[0]
            self.guildsDict[id].users = set(
                [user async for user in reaction.users() if user != self.user and not user.bot])
            self.guildsDict[id].displayName = {
                user.id: user.display_name async for user in reaction.users() if user != self.user and not user.bot}

    async def on_guild_join(self, guild) -> None:
        """
        Called when the bot joins a guild
        :param guild: The guild the bot joined
        :return: None
        """
        self.guildsId.add(guild.id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=False)
        }

        channel = None
        for chan in guild.channels:
            if chan.name == 'tldr-authorisation':
                channel = chan
                break

        if channel is None:
            channel = await guild.create_text_channel('tldr-authorisation', overwrites=overwrites)

        # muted_users = dict(tuple(guild.id,user.id),list(number,all the roles id he had))) = {(,): [,[]]}
        #: dict[tuple([int,int]), list[int,list[int]]] 
        muted_users = {}
        moderators = []
        bad_words = []
        permUser = []
        perGroup = []
        await channel.send(
            "Hey admins :eyes:, please check that all mood roles are on the top of the coloured roles order, if they're not please **put this bot's role at the top** and do `!moodroles reset`. If you don't want mood roles please do `!moodroles toggle`.\n**You might need to click the checkmark below for your commands to be registered.**\nThank you and feel free to delete this message when done :D")
        message = await channel.send(
            "Hey! I won't read your messages unless I have your consent. If you want to interact with me please click on the checkmark :D")
        self.guildsDict[
            guild.id] = GuildData(guild.id, '!', channel.id, message.id, True, 15, 30, 10, 30, {}, 5, bad_words, permUser, perGroup, muted_users, moderators)
        await message.add_reaction('✅')

        if not mood.rolesPresent(guild):
            asyncio.run_coroutine_threadsafe(mood.createRoles(self, guild), self.moodLoop)

        if not mod.rolesPresent(guild):
            asyncio.run_coroutine_threadsafe(mod.createRole(self, guild), self.autoModLoop)
        # Default social graph
        if not self.socialGraphWorker.isPresent(guild.id):
            guildData = self.guildsDict[guild.id]
            asyncio.run_coroutine_threadsafe(self.socialGraphWorker.create_default(guild.id, guildData),
                                             self.socialGraphLoop)
        self.save()

    def send_message(self, content: str, channel: discord.TextChannel) -> None:
        """
        Sends a messages to a specific channel
        :param content: textual content of the message
        :param channel: channel to send the message in
        """
        asyncio.run_coroutine_threadsafe(channel.send(content), self.loop)

    def reply_message(self, content: str, message: discord.Message) -> None:
        """
        Sends a messages to a specific channel
        :param content: textual content of the message
        :param message: message to reply to
        """
        asyncio.run_coroutine_threadsafe(message.reply(content), self.loop)

    def fetchMessage(self, channel: discord.TextChannel, messageId) -> discord.Message:
        """
        Fetches a message from a channel
        :param channel: channel to fetch the message from
        :param messageId: id of the message to fetch
        :return: the message
        """
        return asyncio.run_coroutine_threadsafe(channel.fetch_message(messageId), self.loop).result()

    def fetchHistoryBefore(self, channel, limit, message):
        """
        Fetches the history of a channel before a specific message
        :param channel: channel to fetch the history from
        :param limit: limit of messages to fetch
        :param message: message to fetch the history before
        :return: the history
        """
        return asyncio.run_coroutine_threadsafe(channel.history(limit=limit, before=message), self.loop).result()

    async def on_guild_remove(self, guild) -> None:
        """
        Called when the bot leaves a guild
        :param guild: The guild the bot left
        :return: None
        """
        id = guild.id
        self.guildsId.remove(id)
        del self.guildsDict[id]
        self.save()

    async def guild_added(self, guild) -> None:
        """
        Called when the bot joins a guild
        :param guild: The guild the bot joined
        :return: None
        """
        self.guildsId.add(guild.id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=False)
        }

        channel = None
        for chan in guild.channels:
            if chan.name == 'tldr-authorisation':
                channel = chan
                break

        if channel is None:
            channel = await guild.create_text_channel('tldr-authorisation', overwrites=overwrites)

        await channel.send(
            "Hey admins :eyes:, please check that all mood roles are on the top of the coloured roles order, if they're not please **put this bot's role at the top** and do `!moodroles reset`. If you don't want mood roles please do `!moodroles toggle`.\n**You might need to click the checkmark below for your commands to be registered.**\nThank you and feel free to delete this message when done :D")
        message = await channel.send(
            "Hey! I won't read your messages unless I have your consent. If you want to interact with me please click on the checkmark :D")
        self.guildsDict[
            guild.id] = GuildData(guild.id, '!', channel.id, message.id, True, 15, 30, 10, 30, {}, 5, [], [], [], {}, [])
        await message.add_reaction('✅')

        if not mood.rolesPresent(guild):
            asyncio.run_coroutine_threadsafe(mood.createRoles(self, guild), self.moodLoop)
        self.save()

    async def guild_removed(self, guildId) -> None:
        """
        Called when the bot leaves a guild
        :param guildId: The id of the guild the bot left
        :return: None
        """
        self.guildsId.remove(guildId)
        del self.guildsDict[guildId]
        self.save()

    def timeLoop(self):
        """
        Keeps track of time and calls the functions that need to be called every minute
        """
        self.moodUpdateMinute = 0
        while True:
            # Goes to next minute
            time.sleep(60)

            # Mood updates
            self.moodUpdateMinute = (self.moodUpdateMinute + 1) % 181  # Goes up to 3 hours
            asyncio.run_coroutine_threadsafe(mood.updateMoods(self), self.moodLoop)

            # AutoMod updates
            asyncio.run_coroutine_threadsafe(mod.updateMuted(self), self.autoModLoop)

            # Socialgraph save
            if self.moodUpdateMinute % 2 == 0:
                asyncio.run_coroutine_threadsafe(self.socialGraphWorker.save(), self.socialGraphLoop)


def main():
    """
    Main function of the bot
    Starts the bot
    """
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True
    intents.members = True
    bot = Bot(intents=intents)
    bot.run(os.getenv("TOKEN"))


main()
