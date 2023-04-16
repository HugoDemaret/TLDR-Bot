import asyncio
import csv
import enum
import os
import time

import discord
from dotenv import load_dotenv
from huggingface_hub import login
from transformers import pipeline

from utils import printExceptions

# Login to huggingface to access custom model
# load_dotenv()
# login(token=os.getenv("HUGGINGFACE_TOKEN"))

# Custom model
# classifier = pipeline("text-classification", model="Luc-Salvon/discord_mood_analysis", return_all_scores=True)

# Stable model
classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", return_all_scores=True)


# •===================•
#    DATA STRUCTURES
# •===================•

class Mood(enum.Enum):
    """
    Enumeration representing the different available moods


    Each mood has the following attributes:
    - moodName: Name of the mood (displayed on role)
    - emotionName: Name of the associated emotion (returned by transformer)
    - colour: Colour of the associated role
    - position: Position in a list of each mood
    - emoji: Emoji associated to the mood
    """

    def __init__(self, moodName: str, emotionName: str, colour: discord.Colour, position: int, emoji: str):
        self.moodName = moodName  # Name of the mood (displayed on role)
        self.emotionName = emotionName  # Name of the associated emotion (returned by transformer)
        self.colour = colour  # Colour of the associated role
        self.position = position  # Position in a list of each mood
        self.emoji = emoji  # Emoji associated to the mood

    ANGRY       = ("angry",     "anger",        discord.Colour.from_str("#ff3939"), 0, "😡")
    DISGUSTED   = ("disgusted", "disgust",      discord.Colour.from_str("#ee8100"), 1, "🤢")
    AFRAID      = ("afraid",    "fear",         discord.Colour.from_str("#00b7df"), 2, "😱")
    HAPPY       = ("happy",     "joy",          discord.Colour.from_str("#28d025"), 3, "😄")
    NEUTRAL     = ("neutral",   "neutral",      discord.Colour.from_str("#aabcc0"), 4, "😐")
    SAD         = ("sad",       "sadness",      discord.Colour.from_str("#8d47ff"), 5, "😢")
    SURPRISED   = ("surprised", "surprise",     discord.Colour.from_str("#ffca0e"), 6, "😮")
    SLEEPY      = ("sleepy",    "sleepiness",   discord.Colour.from_str("#ff5cb8"), 7, "😴")


# •==================•
#    ROLES MANAGING
# •==================•
@printExceptions
def rolesPresent(guild: discord.Guild) -> bool:
    """
    Checks if the mood roles are already on the guild
    :param guild: the guild to check
    :return: True if the roles are present, False if not
    """
    moodNames = set([mood.moodName for mood in Mood])
    for role in guild.roles:
        if role.name in moodNames:
            return True
    return False


@printExceptions
async def createRoles(bot, guild: discord.Guild) -> None:
    """
    Creates all the mood roles on the guild
    :param bot: the bot
    :param guild: the guild to put the roles in
    """
    print("i be here")
    # Creation of all the roles
    for mood in Mood:
        asyncio.run_coroutine_threadsafe(guild.create_role(name=mood.moodName, colour=mood.colour, mentionable=True), bot.loop).result()
    print("heya da roles are created but no order sadge")
    # Reordering of roles positions, mood roles need to be at the top so the colouring is not overshadowed
    moodRoleNames = set([mood.moodName for mood in Mood])
    positions = {}
    priorityPosition = 100

    for role in guild.roles:
        if role.colour == discord.Colour.default():  # Transparent roles get most priority
            positions[role] = priorityPosition + role.position
        elif role.name in moodRoleNames:  # Then mood roles
            positions[role] = priorityPosition - len(Mood) + \
                              [mood.position for mood in Mood if mood.moodName == role.name][0]
        else:  # Other coloured roles at the end (not to overshadow mood roles colouring)
            positions[role] = role.position
    print("positions computed")

    asyncio.run_coroutine_threadsafe(guild.edit_role_positions(positions), bot.loop)
    print("Reordered yay")


@printExceptions
async def removeRoles(bot, guild: discord.Guild) -> None:
    """
    Removes all the mood roles from the guild
    :param bot: the bot
    :param guild: the guild
    """
    moodNames = [mood.moodName for mood in Mood]
    for role in guild.roles:
        if role.name in moodNames:
            asyncio.run_coroutine_threadsafe(role.delete(), bot.loop).result()


# •=================•
#    TIMED UPDATES
# •=================•


@printExceptions
async def updateMoods(bot) -> None:
    """
    Processes all the required mood updates from the specific minute (see bot.moodUpdates)
    Called every minute by bot.timeLoop()
    :param bot: the bot
    """
    minute = bot.moodUpdateMinute
    while len(bot.moodUpdates[minute]) > 0:  # For each required update
        update = bot.moodUpdates[minute].pop()
        if update[1]:  # Update is a mood refresh
            refreshMoods(bot, update[0])  # Operates the refresh
            # Schedules next refresh
            nextUpdate = (minute + bot.guildsDict[update[0]].moodRefreshTime) % 181
            bot.moodUpdates[nextUpdate].append(update)
        else:  # Update is a mood reset
            resetMoods(bot, update[0])  # Operates the reset
            # Schedules next reset
            nextUpdate = (minute + bot.guildsDict[update[0]].moodResetTime) % 181
            bot.moodUpdates[nextUpdate].append(update)


# •================•
#    MOOD UPDATES
# •================•
@printExceptions
def refreshMoods(bot, guildID: int) -> None:
    """
    Refreshes the mood of every active user from the specified guild
    :param bot: the bot
    :param guildID: the id of the guild to refresh the users' moods of
    """
    guildData = bot.guildsDict[guildID]
    for userID in guildData.userActive.keys():
        if len(guildData.userMessages[
                   userID]) != 0:  # If a user has sent messages since last refresh we update their mood
            refreshMood(bot, userID, guildID)
            guildData.userMessages[userID].clear()


@printExceptions
def resetMoods(bot, guildID: int) -> None:
    """
    Resets the moods of the inactive users from the specified guild
    :param bot: the bot
    :param guildID: the id of the guild
    """
    guildData = bot.guildsDict[guildID]
    for userID in guildData.moods.keys():
        if not guildData.userActive[userID]:  # If a user has not been active
            resetMood(bot, userID, guildID)
            return
        guildData.userActive[userID] = False


@printExceptions
def refreshMood(bot, userID: int, guildID: int) -> None:
    """
    Refreshes the mood of a specific member of a specific guild
    :param bot: the bot
    :param userID: the id of the guild member
    :param guildID: the id of the guild
    """

    guildData = bot.guildsDict[guildID]

    # Mood computation
    mood = getMood(guildData.userMessages[userID])

    # Mood update
    oldMood = guildData.moods.get(userID, None)
    if mood != oldMood:  # User's mood changed -> need to update it
        guild = bot.get_guild(guildID)
        member = guild.get_member(userID)

        # Update user's mood in the moods dict
        guildData.moods[userID] = mood

        if oldMood is not None:  # Need to get rid of old mood role
            roleToRemove = discord.utils.get(guild.roles, name=oldMood.moodName)
            if roleToRemove is not None:  # If roles are enabled
                asyncio.run_coroutine_threadsafe(member.remove_roles(roleToRemove), bot.loop)

        # Add new mood role
        roleToAdd = discord.utils.get(guild.roles, name=mood.moodName)
        asyncio.run_coroutine_threadsafe(member.add_roles(roleToAdd), bot.loop)


@printExceptions
def resetMood(bot, userID: int, guildID: int) -> None:
    """
    Resets the mood of a specific member of a specific guild
    :param bot: the bot
    :param userID: the id of the member
    :param guildID: the id of the guild
    """
    guildData = bot.guildsDict[guildID]

    guild = bot.get_guild(guildID)
    member = guild.get_member(userID)
    moodNames = [mood.moodName for mood in Mood]
    try:
        for role in member.roles:
            if role.name in moodNames:
                asyncio.run_coroutine_threadsafe(member.remove_roles(role), bot.loop)
                break

    finally:
        guildData.moods.pop(userID)
        guildData.userActive.pop(userID)


# •======================•
#    MESSAGE PROCESSING
# •======================•
@printExceptions
def getEmotions(messages: list[str]) -> list[dict[str: float]]:
    """
    Gets the emotions associated to a list of messages via a transformer
    :param messages: the list of messages to extract the emotions from
    :return: a list of dictionaries, each containing a "label" (emotion name) and "score" (probability of the emotion)
    """
    try:
        return classifier(". ".join(messages))  # Join messages together with a full stop in between to create sentences (almost no discord message ends with a full stop)
    except:  # Message is too long, we split it up and average the results
        emotions1 = getEmotions(messages[:len(messages) // 2])
        emotions2 = getEmotions(messages[len(messages) // 2:])
        return [{"label": emotions1[i]["label"], "score": (emotions1[i]["score"] + emotions2[i]["score"]) / 2} for i in
                range(len(Mood))]


@printExceptions
def getMood(messages: list[str]) -> Mood:
    """
    Gets the mood associated to a list of messages
    :param messages: the list of messages
    :return: the mood associated to the list of messages
    """
    emotions = getEmotions(messages)[0]
    maxScore = 0
    maxEmotion = ""

    for emotion in emotions:
        if emotion["label"] == "neutral":  # We nerf the power of the neutral emotion, otherwise it's too prominent
            emotion["score"] /= 2
        if emotion["score"] > maxScore:
            maxScore = emotion["score"]
            maxEmotion = emotion["label"]
    return [m for m in Mood if m.emotionName == maxEmotion][0]  # Gets the mood associated to maxEmotion


@printExceptions
async def processMessage(bot, message: discord.Message):
    """
    Processes a message for mood computation and sets up the message collection system for the dataset if needed
    :param bot: the bot
    :param message: the message to be processed
    """
    guildData = bot.guildsDict[message.guild.id]
    if guildData.timedMoodRefreshes:
        timeProcessing(bot, message)
    else:
        messageProcessing(bot, message)

    # Process the message for the dataset gathering
    if guildData.moodTraining[message.author.id]:
        setDatasetCollectionMessage(bot, message)


@printExceptions
def timeProcessing(bot, message: discord.Message) -> None:
    """
    Processes a message when guild mood refreshes are based on time
    :param bot: the bot
    :param message: the message to process
    """
    guildData = bot.guildsDict[message.guild.id]

    userID = message.author.id

    if userID not in guildData.userMessages:
        guildData.userMessages[userID] = []

    guildData.userMessages[userID].append(message.content)  # Adds the message to the user's list of messages
    guildData.userActive[userID] = True  # Sets the user as active


@printExceptions
def messageProcessing(bot, message: discord.Message) -> None:
    """
    Processes a message when guild mood refreshes based on messages
    :param bot: the bot
    :param message: the message to process
    """
    guildData = bot.guildsDict[message.guild.id]

    userID = message.author.id

    if userID not in guildData.userMessages:
        guildData.userMessages[userID] = []

    messages = guildData.userMessages[userID]
    messages.append(message.content)  # Adds the message to the user's list of messages
    guildData.userActive[userID] = True  # Sets the user as active

    while len(messages) > guildData.moodMessageDepth:  # Gets rid of messages too old
        messages.pop(0)

    if len(messages) >= guildData.moodMessageThreshold:  # Message-based refresh -> need to refresh if message threshold exceeded
        refreshMood(bot, userID, message.guild.id)


# •===================•
#    DATASET MANAGER
# •===================•

@printExceptions
def addCSV(messageContent: str, emotion: str) -> None:
    """
    Adds the message and its emotion to the csv file of the emotions dataset
    :param messageContent: the message
    :param emotion: the emotion
    """
    with open("data/emotion_dataset.csv", "a") as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow([messageContent, emotion])


@printExceptions
def setDatasetCollectionMessage(bot, message: discord.Message):
    """
    Sends the message to collect the user's message and emotion for the dataset
    :param bot: the bot
    :param message: the message
    """
    guildData = bot.guildsDict[message.guild.id]

    mood = getMood([message.content])
    messageContent = f"I believe this message's emotion is **{mood.emotionName} {mood.emoji}**.\n• **If I'm right**, please check the __checkmark__.\n• **if I'm wrong**, click the __right arrow__ then react with the __according emotion__.\n• **If you don't want this specific message to be processed**, please click the __red cross__.\n• **If you don't want me to process your messages at all**, type `{guildData.prefix}moodtraining toggle`\n\n*Note that the reactions can take a while to appear.\nAlso note that messages are stored anonymously, your stored messages can't be traced back to you.*\n**Thanks for helping me learn! :D**\n"
    sentMessage = asyncio.run_coroutine_threadsafe(message.channel.send(messageContent, reference=message),
                                                   bot.loop).result()
    emojiList = ["✅", "❌", "➡️"]
    for emoji in emojiList:
        asyncio.run_coroutine_threadsafe(sentMessage.add_reaction(emoji), bot.loop).result()
    guildData.emotionCheckMessages[sentMessage.id] = mood
