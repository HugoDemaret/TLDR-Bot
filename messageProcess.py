from os import getenv

from dotenv import load_dotenv

from commands import *
import socialGraph


async def on_messageDiscord(bot, message: discord.Message, guildData) -> None:
    """
    Processes messages for discord
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """
    if len(message.mentions) != 0 and message.mentions[0] == bot.user and len(message.clean_content.split()) > 1 and \
            message.content.split()[1] == "prefix":
        bot.send_message(f"My prefix is `{guildData.prefix}`\nSee `{guildData.prefix}help` for the list of commands you can use :D", message.channel)
        return

    if message.clean_content.startswith(guildData.prefix):  # Message is a command
        mots = message.clean_content[len(guildData.prefix):].lower().split()

        match mots[0]:
            case "prefix":
                prefix(bot, message, guildData, mots)

            case "bye":
                load_dotenv()
                try:
                    if message.author.id in map(int, getenv("BYE_USERS").split(",")):
                        await bye(bot, message)
                except AttributeError:
                    pass

            case "help":
                helpCommand(bot, message, guildData, mots)

        bot.save()


async def on_messageTldr(bot, message: discord.Message, guildData) -> None:
    """
    Processes messages for tldr
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    """
    msg = message.clean_content
    msgTokens = message.clean_content.split()
    if len(msgTokens) == 0:
        return
    msgFirstToken = msgTokens[0]
    msgFirstTokenLower = msgFirstToken.lower()

    if msgFirstToken.startswith(guildData.prefix):  # Message is a command

        msgFirstToken = msgFirstToken[len(guildData.prefix):]
        match msgFirstToken:
            case "tldr":
                await tldrCommand(bot, message, guildData)
                return
            case "tldrsettings":
                tldrSettings(bot, message, guildData)
                bot.save()

    if msgFirstTokenLower == "tldr":
        await tldrCommand(bot, message, guildData)
        return
    return


def on_messageMood(bot, message: discord.Message, guildData) -> None:
    """
    Processes the mood of a message
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    """
    if message.clean_content.startswith(guildData.prefix):  # Message is a command
        mots = message.clean_content[len(guildData.prefix):].lower().split()
        # Sorts commands:
        match mots[0]:
            case "mood":
                moodCommand(bot, message, guildData)
                return
            case "moods":
                moods(bot, message, guildData)
                return
            case "moodsettings":
                moodsettings(bot, message, guildData, mots)
                bot.save()  # Save the bot if not returned (= change was made)
            case "moodroles":
                moodroles(bot, message, guildData, mots)
                return
            case "moodtraining":
                moodtraining(bot, message, guildData, mots)
                bot.save()  # Save the bot if not returned (= change was made)

    else:  # Message is not a command -> process the message for mood analysis
        asyncio.run_coroutine_threadsafe(mood.processMessage(bot, message), bot.moodLoop)


async def on_messageSocialGraph(bot, message, guildData) -> None:
    """
    Processes messages for social graph
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    :return: None
    """
    if message.content.startswith(guildData.prefix):
        await socialGraphCommand(bot, message, guildData)
        return
    #if message is a reply
    repliedMessage = None
    if message.type == discord.MessageType.reply:
        repliedMessage = await message.channel.fetch_message(message.reference.message_id)

    asyncio.run_coroutine_threadsafe(socialGraph.SocialGraphWorker.on_message(bot.socialGraphWorker,
                                                                              message,
                                                                              repliedMessage),
                                     bot.socialGraphLoop)
    return


def on_messageAutoMod(bot, message, guildData):
    """
    Processes auto moderation
    :param bot: the bot
    :param message: the message to process
    :param guildData: the data associated to the guild the message was sent in
    """
    # if message is not a command -> process the message for auto moderation
    if message.clean_content.startswith(guildData.prefix) is False:  # Message is not a command
        asyncio.run_coroutine_threadsafe(mod.automod(message, guildData), bot.autoModLoop)

    if message.clean_content.startswith(guildData.prefix):
        mots = message.clean_content[len(guildData.prefix):].lower().split()
        match mots[0]:
            case "moderatesettings":
                moderatesettings(bot, message, guildData,mots)
                bot.save()
                return
            case "muteuser":
                muteuser(bot, message, guildData, mots)
                # asyncio.run_coroutine_threadsafe(muteuser(bot, message, guildData), bot.autoModLoop)
                bot.save()
                return
            case "unmuteuser":
                unmuteUser(bot, message, guildData, mots)
                #asyncio.run_coroutine_threadsafe(unmuteuser(bot, message, guildData), bot.autoModLoop)
                bot.save()
                return
