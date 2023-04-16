import asyncio
import json
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from transformers import pipeline
import mood
import utils
import discord
from utils import printExceptions

"""
Models import
"""

model_path = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
sentiment_task = pipeline("sentiment-analysis", model=model_path, tokenizer=model_path)




# •======================•
#    SOCIAL GRAPH CLASS
# •======================•


class SocialGraph:
    """
    This class represents a social graph
    :nbPeople: the number of people in the social graph
    :nbMessage: the number of messages
    :tagMinValue: the minimum value of a tag
    :importanceDict: the importance dict
    :agreementDict: the agreement dict
    :taggedDict: the tagged dict
    :guildData: the guild data
    :nbMessage_at_time: the number of messages at time
    :importanceMaxValue: the maximum importance value
    :importanceInitValue: the initial importance value
    :interactions: the interactions
    """
    # •======================•
    #    CONSTRUCTOR
    # •======================•

    def __init__(self,
                 nbPeople: int,
                 nbMessage: int,
                 tagMinValue: float,
                 importanceDict: dict[int, float],
                 agreementDict: dict,
                 taggedDict: dict[int, list[float]],
                 guildData,
                 nbMessage_at_time: dict[int, int],
                 importanceMaxValue: float,
                 importanceInitValue: float,
                 interactions: dict[int, dict[int, int]]
                 ):
        """
        Constructor
        :param nbPeople: the number of people in the social graph
        :param nbMessage: the number of messages
        :param tagMinValue: the minimum value of a tag
        :param importanceDict: the importance dict
        :param agreementDict: the agreement dict
        :param taggedDict: the tagged dict
        :param guildData: the guild data
        :param nbMessage_at_time: the number of messages at time
        :param importanceMaxValue: the maximum importance value
        :param importanceInitValue: the initial importance value
        :param interactions: the interactions
        """

        self.nbMessage = nbMessage
        self.tagMinValue = tagMinValue
        self.importanceDict = importanceDict
        self.agreementDict = agreementDict
        self.taggedDict = taggedDict
        self.guildData = guildData
        self.nbMessage_at_time = nbMessage_at_time
        self.channelQueueDict = dict()
        self.importanceInitValue = importanceInitValue
        self.importanceMaxValue = importanceMaxValue
        self.interactions = interactions

    # •======================•
    #    GETTERS AND SETTERS
    # •======================•

    """"
    Getters
    """
    @printExceptions
    def get_nb_message(self) -> int:
        """
        Gets the number of messages
        :return: the number of messages
        """
        return self.nbMessage

    @printExceptions
    def get_graph(self):
        """
        Gets the social graph
        :return: the social graph
        """
        return self

    @printExceptions
    def get_nb_people(self) -> int:
        """
        Gets the number of people in the social graph
        :return: the number of people in the social graph
        """
        return len(self.guildData.users)

    @printExceptions
    def get_user_importance(self, user: discord.Member) -> float:
        """
        Gets the importance of a user
        :param user: the user
        :return: the importance of the user
        """
        nbPeople = self.get_nb_people()
        if user.id not in self.importanceDict:
            return 1. / nbPeople
        return self.importanceDict[user.id]

    @printExceptions
    def get_sentiment(self, userId):
        """
        Return the sentiment of the user
        :param userId: the user id
        :return: the sentiment of the user
        """
        if userId not in self.agreementDict:
            self.agreementDict[userId] = [0] * 2
            return "neutral"
        if self.agreementDict[userId][1] == 0:
            return "neutral"
        sentimentInt = self.agreementDict[userId][0] / self.agreementDict[userId][1]
        if sentimentInt > 0:
            return "positive"
        elif sentimentInt < 0:
            return "negative"
        else:
            return "neutral"

    @printExceptions
    def get_agreement(self, userId1: int, userId2: int) -> float:
        """
        Return the agreement between two users
        :param userId1: the first user
        :param userId2: the second user
        :return: the agreement between the two users
        """
        if userId1 not in self.agreementDict:
            self.agreementDict[userId1] = [0] * 2
        if userId2 not in self.agreementDict:
            self.agreementDict[userId2] = [0] * 2
        return (self.agreementDict[userId1][0] + self.agreementDict[userId2][0]) / (self.agreementDict[userId1][1] + self.agreementDict[userId2][1])

    """
    Setters
    """

    @printExceptions
    def set_nb_message(self, nbMessage: int) -> None:
        """
        Sets the number of messages
        :param nbMessage: the number of messages
        :return: None
        """
        self.nbMessage = nbMessage

    # •======================•
    #   ADDERS AND REMOVERS
    # •======================•


    """
    Adders
    """
    @printExceptions
    def add_user(self, userId: int) -> None:
        """
        Adds a user to the social graph
        :param userId: the user to add
        :return: None
        """
        if userId not in self.importanceDict:
            self.importanceDict[userId] = 1. / self.get_nb_people()
        if userId not in self.taggedDict:
            self.taggedDict[userId] = [0.]
        if userId not in self.nbMessage_at_time:
            self.nbMessage_at_time[userId] = 0
        if userId not in self.interactions:
            self.interactions[userId] = dict()
        if userId not in self.agreementDict:
            self.agreementDict[userId] = [0]*2

    @printExceptions
    def add_message_channel_queue(self, message: discord.Message) -> None:
        """
        Adds a message to the channel queue
        :param message: the message
        :return: None
        """
        channelId = message.channel.id

        if channelId not in self.channelQueueDict:
            self.channelQueueDict[channelId] = []

        while len(self.channelQueueDict[channelId]) >= 10:
            self.channelQueueDict[channelId].pop(0)

        self.channelQueueDict[channelId].append(message)

    """
    Removers
    """

    @printExceptions
    def remove_user(self, userId: int) -> None:
        """
        Removes a user from the social graph
        :param userId: the user to remove
        :return: None
        """
        self.importanceDict.pop(userId)
        self.taggedDict.pop(userId)
        self.nbMessage_at_time.pop(userId)
        self.interactions.pop(userId)
        self.agreementDict.pop(userId)

        #print(len(self.interactions))

        for userId2 in self.interactions.keys():
            if userId in self.interactions[userId2]:
                self.interactions[userId2].pop(userId)




    # •======================•
    #    FETCH TAGGED USERS
    # •======================•

    @printExceptions
    def power_law(self, message, channelQueue) -> dict:
        """
        Computes the probability of a user to be the author of the next message
        :param message: the message
        :param channelQueue: the queue of the channel
        :return: a dict with the id of the user as key and the probability as value
        """
        # simple version of a power law distribution (scaled times 2)
        # we get the time difference between the last message and the current message
        probaDict = {}
        for i in range(1, len(channelQueue) + 1):
            p = 1 / i
            actualMessage = channelQueue[-i]
            actualMessageAuthorId = actualMessage.author.id
            if actualMessageAuthorId != message.author.id:
                if actualMessage.author.id not in probaDict:
                    probaDict[actualMessageAuthorId] = p
                else:
                    probaDict[actualMessageAuthorId] = max(probaDict[actualMessageAuthorId], p)
        return probaDict
    @printExceptions
    def fetch_tagged_members(self, message: discord.Message, repliedMessage) -> dict:
        """
        Fetches the tagged members of the message
        :param message: the message
        :param repliedMessage: the replied message
        :return: a dict with the id of the tagged members as key and the value 1 as value
        """



        # if author talks to a group of people by mentioning them, we update their importance

        taggedMembers = message.mentions

        # get the id of the members in a set
        taggedMembersId = {member.id for member in taggedMembers if member.id != message.author.id}

        # add to taggedMembersId the id of the members in the roles mentioned
        for role in message.role_mentions:
            taggedMembersId = taggedMembersId | {member.id for member in role.members if member.id != message.author.id}

        # replied message author
        if repliedMessage is not None:
            taggedMembersId = taggedMembersId | {repliedMessage.author.id if repliedMessage.author.id != message.author.id else None}

        # fills the taggedMembersValue dict with the value 1 for every member in taggedMembersId
        taggedMembersValues = {memberId: 1. for memberId in taggedMembersId}
        # we return the dict
        return taggedMembersValues

    @printExceptions
    def fetch_probable_chatting_buddy(self, message: discord.Message) -> dict:
        """
        Fetches the probable chatting buddy of the author of the message
        :param message: the message
        :return: a dict with the id of the probable chatting buddy as key and the probability as value
        """
        channelId = message.channel.id
        if channelId not in self.channelQueueDict:
            return {}
        channelQueue = self.channelQueueDict[channelId]
        # if the queue is empty, we return an empty dict
        if len(channelQueue) == 0:
            return {}
        # we get the last message in the queue
        lastMessage = channelQueue[-1]
        # if the last message was sent by the same author, we return an empty dict
        if lastMessage.author.id == message.author.id:
            return {}

        # PowerLaw
        probaDict = self.power_law(message, channelQueue)

        return probaDict


    # •======================•
    #    IMPORTANCE METHODS
    # •======================•

    @printExceptions
    def evaluate_importance(self, authorId: int, memberId: int, taggedMemberValues: dict[int, float]) -> float:
        """
        Evaluates the importance of a member
        :param authorId: the id of the author of the message
        :param memberId: the id of the member we want to evaluate the importance
        :param taggedMemberValues: a dict with the id of the members as keys and the value 1 as values
        :return: the importance of the member
        """
        # we get the importance of the members
        importance = self.importanceDict[memberId]
        prevNbMessage = self.nbMessage_at_time[memberId]
        actualNbMessage = max(self.nbMessage_at_time.values())
        if actualNbMessage == 0:
            actualNbMessage = 1
        # we get the number of people the member talked to
        importance = ((importance * prevNbMessage) + (self.importanceDict[authorId] * taggedMemberValues[memberId]))
        return importance / actualNbMessage

    @printExceptions
    def update_importance(self, authorId: int, taggedMembersValues: dict[int, float]) -> None:
        """
        Updates the importance of the members in the taggedMembersValues dict
        :param authorId: the id of the author of the message
        :param taggedMembersValues: a dict with the id of the members as keys and the value 1 as values
        :return: None
        """
        nbMsg = self.get_nb_message()
        # if the author is not in the importanceDict, we add them with the importanceInitValue
        if authorId not in self.importanceDict:
            self.importanceDict[authorId] = 1/len(self.importanceDict)
            self.nbMessage_at_time[authorId] = nbMsg

        # we update the importance of the people the author talked to
        # print("updateimportance : start ", self.importanceDict, "\n", taggedMembersValues, "taggedMembersValues")
        for memberId in taggedMembersValues:
            # if the member is not in the importanceDict, we add him with the importanceInitValue
            if memberId not in self.importanceDict:
                self.importanceDict[memberId] = 1/len(self.importanceDict)
                self.nbMessage_at_time[memberId] = nbMsg

            if memberId != authorId:
                # we update the importance of the member
                self.importanceDict[memberId] = self.evaluate_importance(authorId, memberId, taggedMembersValues)
                # print("updateimportance : end ",self.importanceDict[memberId])
                self.nbMessage_at_time[memberId] = nbMsg
        self.importanceMaxValue = max(self.importanceDict.values())



    # •======================•
    #    AGREEMENT METHODS
    # •======================•

    @printExceptions
    def evaluate_agreement(self, message) -> int:
        """
        Evaluate the agreement of the message
        :param message: the message
        :return: 1 if positive, -1 if negative, 0 if neutral
        """
        agreement = sentiment_task(message.content)[0]["label"]
        match agreement:
            case "positive":
                return 1
            case "negative":
                return -1
            case "neutral":
                return 0

    @printExceptions
    def update_agreement(self, message, taggedMembersValues: dict[int, float]) -> None:
        """
        Update the agreement of the people the author talked to
        :param message: the message
        :param taggedMembersValues: the dict of the tagged members
        :return: None
        """
        # we update the agreement of the people the author talked to
        if message.author.id not in self.agreementDict:
            self.agreementDict[message.author.id] = [0] * 2
        self.agreementDict[message.author.id][0] += self.evaluate_agreement(message)
        self.agreementDict[message.author.id][1] += 1



    # •==========================•
    #   GRAPH APPEARANCE METHODS
    # •==========================•

    @printExceptions
    def vertex_size_user(self, importanceValue) -> float:
        """ Return the size of the vertex for a user
        :param importanceValue: the importance of the user
        :return: the size of the vertex for a user
        """
        if self.importanceMaxValue == 0.0:
            return 1000 / len(self.importanceDict)
        return (importanceValue/self.importanceMaxValue)*(10000 / len(self.importanceDict))

    @printExceptions
    def vertex_sizes(self, users):
        """
        Return the sizes of the vertices
        :param users: the users
        :return: the sizes of the vertices
        """
        return [self.vertex_size_user(self.importanceDict[user]) for user in users]

    @printExceptions
    def vertex_colour(self, users) -> list:
        """
        Return the colours of the vertices
        :param users: the users
        :return: the colours of the vertices
        """
        colours = []
        for user in users:
            if user in self.guildData.moods:
                colours.append(str(self.guildData.moods[user].colour))
            else:
                colours.append("#dddddd")  # TODO: find better default colour for when a user has no assigned mood
        return colours

    @printExceptions
    def edge_colour(self, user1, user2) -> str:
        """
        Return the colour of the edge between user1 and user2
        :param user1: the first user
        :param user2: the second user
        :return: the colour of the edge
        """
        agreement = self.get_agreement(user1, user2)
        if agreement >= 0.65:
            return "#28d025"
        elif 0.25 <= agreement < 0.65:
            return "#53c959"
        elif 0.1 <= agreement < 0.25:
            return "#7fc38c"
        elif 0.1 > agreement >= -0.1:
            return "#aabcc0"
        elif -0.1 > agreement > -0.25:
            return "#28d025"
        elif -0.25 >= agreement > -0.65:
            return "#c69093"
        elif agreement <= -0.65:
            return "#ff3939"
        else:
            raise ValueError(f"Agreement value isn't considered : {agreement}")


    @printExceptions
    def edge_width(self, key, member) -> float:
        """
        Return the width of the edge between two users
        :param key: the first user
        :param member: the second user
        :return: the width of the edge
        """
        value = self.interactions[key][member]/(max(max(v.values()) for v in self.interactions.values() if len(v) > 0))
        return value * 5


    # •==========================•
    #   GRAPH EXPORT METHODS
    # •==========================•

    @printExceptions
    def export_user_graph_distance(self, user, distance) -> None:
        """
        Export the graph of the user and the people he talked to in a file
        :param user: the user
        :param distance: the distance in the graph
        :return: None
        """
        members = self.guildData.displayName
        #print(members)
        socialGraph = nx.DiGraph()
        socialGraph.add_nodes_from(members)
        cmap = utils.get_colourmap(str(mood.Mood.HAPPY.colour), str(mood.Mood.ANGRY.colour))
        for key in self.interactions:
            for member in self.interactions[key]:
                socialGraph.add_edge(key, member, weight=self.edge_width(key, member), color=self.edge_colour(key, member))

        #print(f'Interactions : {self.interactions}')

        socialGraph = nx.generators.ego_graph(socialGraph, user, radius=distance)

        members = {member : self.guildData.displayName[member] for member in socialGraph.nodes}
        colours = [socialGraph[u][v]['color'] for u, v in socialGraph.edges]
        weights = [socialGraph[u][v]['weight'] for u, v in socialGraph.edges]
        pos = nx.circular_layout(socialGraph, scale=0.8)
        pos[user] = np.array([0, 0])
        nx.draw(socialGraph, pos=pos, labels=members, with_labels=True, node_color=self.vertex_colour(members.keys()),
                node_size=self.vertex_sizes(members.keys()), edge_color=colours, width=weights,
                arrowsize=list(map(lambda x: 6 * x, weights)), arrowstyle='simple', connectionstyle="arc3,rad=0.15")
        plt.savefig("image/SocialGraphUserDistance.png", format="PNG")
        plt.close()

    @printExceptions
    def export_user_graph_all(self, user) -> None:
        """
        Exports the social graph of the server to a PNG file
        :param user: the user
        :return: None
        """
        members = self.guildData.displayName
        #print(members)
        socialGraph = nx.DiGraph()
        socialGraph.add_nodes_from(members)
        #cmap = utils.get_colourmap(str(mood.Mood.HAPPY.colour), str(mood.Mood.ANGRY.colour))
        for key in self.interactions:
            for member in self.interactions[key]:
                socialGraph.add_edge(key, member, weight=self.edge_width(key, member), color=self.edge_colour(key, member))

        #print(self.interactions)
        colours = [socialGraph[u][v]['color'] for u, v in socialGraph.edges]
        weights = [socialGraph[u][v]['weight'] for u, v in socialGraph.edges]
        pos = nx.circular_layout(socialGraph, scale=0.8)
        pos[user] = np.array([0, 0])
        nx.draw(socialGraph, pos=pos, labels=members, with_labels=True, node_color=self.vertex_colour(members.keys()),
                node_size=self.vertex_sizes(members.keys()), edge_color=colours, width=weights,
                arrowsize=list(map(lambda x: 6 * x, weights)), arrowstyle='simple', connectionstyle="arc3,rad=0.15")
        plt.savefig("image/SocialGraphUserAll.png", format="PNG")
        plt.close()

    @printExceptions
    def export_graph(self) -> None:
        """
        Exports the social graph to a PNG file
        :return: None
        """
        members = self.guildData.displayName
        #print(members)
        socialGraph = nx.DiGraph()
        socialGraph.add_nodes_from(members)
        for key in self.interactions:
            for member in self.interactions[key]:
                socialGraph.add_edge(key, member, weight=self.edge_width(key, member), color=self.edge_colour(key, member))

        #print(list(socialGraph.edges))
        #print(self.interactions)
        pos = nx.circular_layout(socialGraph, scale=0.8)
        colours = [socialGraph[u][v]['color'] for u, v in socialGraph.edges]
        weights = [socialGraph[u][v]['weight'] for u, v in socialGraph.edges]
        node_sizes = self.vertex_sizes(members.keys())
        node_colours = self.vertex_colour(members.keys())
        #print(f'Node colours : {len(node_colours)} : Node sizes : {len(node_sizes)} : Colours : {len(colours)} : Weights : {len(weights)} : Members : {len(members)}')
        nx.draw(socialGraph, pos=pos, labels=members, with_labels=True, node_color=node_colours,
                node_size= node_sizes, edge_color=colours, width=weights, arrowsize=list(map(lambda x: 6*x, weights)), arrowstyle='simple', connectionstyle="arc3,rad=0.15")
        plt.savefig("image/SocialGraph.png", format="PNG")
        plt.close()



    # •======================•
    #   COMMANDS METHODS
    # •======================•


    async def on_command_sentiment(self, message: discord.Message, user, bot) -> None:
        """
        Triggered when a user wants to know the sentiment of a message
        :param message: the message
        :param bot: the bot
        :return: None
        """

        self.add_user(user.id)
        self.add_user(message.author.id)
        sentiment = self.get_sentiment(user.id)
        replyMessage = f"Sentiment of {user.mention} is {sentiment}"
        asyncio.run_coroutine_threadsafe(message.reply(replyMessage), bot.loop)

    @printExceptions
    async def on_command_printall(self, message: discord.Message, bot) -> None:
        """
        Triggered when a user wants to know the socialgraph
        :param message: the message
        :param bot: the bot
        :return: None
        """
        self.add_user(message.author.id)
        self.export_graph()
        asyncio.run_coroutine_threadsafe(message.reply(file=discord.File("image/SocialGraph.png")), bot.loop)

    @printExceptions
    async def on_command_printuser_all(self, message: discord.Message, user, bot) -> None:
        """
        Triggered when a user wants to know the socialgraph of a user
        :param message: the message
        :param user: the user
        :param bot: the bot
        :return: None
        """
        self.add_user(user)
        self.add_user(message.author.id)
        self.export_user_graph_all(user)
        asyncio.run_coroutine_threadsafe(message.reply(file=discord.File("image/SocialGraphUserAll.png")), bot.loop)

    async def on_command_printuser_distance(self, message: discord.Message, user, distance, bot) -> None:
        """
        Triggered when a user wants to know the socialgraph of a user, up to a certain distance
        :param message: the message
        :param user: the user
        :param distance: the distance
        :param bot: the bot
        :return: None
        """
        self.add_user(user)
        self.add_user(message.author.id)
        self.export_user_graph_distance(user,distance)
        asyncio.run_coroutine_threadsafe(message.reply(file=discord.File("image/SocialGraphUserDistance.png")), bot.loop)

    async def on_command_importance(self, message, user, bot) -> None:
        """
        Triggered when a user wants to know the importance of another user
        :param message: the message
        :param user: the user
        :param bot: the bot
        :return: None
        """

        self.add_user(user.id)
        self.add_user(message.author.id)
        replyMessage = f"Importance of {user.mention} : {self.importanceDict[user.id]}"
        asyncio.run_coroutine_threadsafe(message.reply(replyMessage), bot.loop)


    # •======================•
    #   MESSAGE METHODS
    # •======================•

    # On every new message, we determine who the author is talking to and update (the people they talk to) importance's
    def on_message(self, message: discord.Message, repliedMessage) -> None:
        """
        On every new message, we determine who the author is talking to and update (the people they talk to) importance's
        :param message: the message
        :param repliedMessage: the message replied to
        :return: None
        """

        #if user is not in the socialgraph yet, we add them
        if repliedMessage is not None:
            self.add_user(repliedMessage.author.id)
        self.add_user(message.author.id)
        self.set_nb_message(self.get_nb_message() + 1)
        # if author talks to everyone, we update everyone's importance
        taggedMembersValues = self.fetch_tagged_members(message, repliedMessage)
        probablyTaggedMembersValues = self.fetch_probable_chatting_buddy(message)
        taggedMembersValues = {**probablyTaggedMembersValues, **taggedMembersValues}
        # for every member in taggedMembersValues, we add the value to the taggedDict

        for member in taggedMembersValues:
            if member in self.taggedDict:
                taggedList = list(self.taggedDict[member])
                taggedList.append(taggedMembersValues[member])
                self.taggedDict[member] = taggedList
            else:
                self.taggedDict[member] = list(taggedMembersValues[member])
        # we update the importance of the people the author talked to
        self.update_importance(message.author.id, taggedMembersValues)
        # we add the message to the channel history
        self.add_message_channel_queue(message)


        #print(f"Tagged members : {taggedMembersValues}")
        #add the interactions to the author and the people he talked to
        for member in taggedMembersValues:
            if message.author.id not in self.interactions:
                self.interactions[message.author.id] = {}
                self.interactions[message.author.id][member] = 0
            if member not in self.interactions[message.author.id]:
                self.interactions[message.author.id][member] = 0
            self.interactions[message.author.id][member] += 1

        self.update_agreement(message, taggedMembersValues)



    # •======================•
    #   UTILS METHODS
    # •======================•

    def purge(self) -> None:
        """
        Purges the social graph
        :return: None
        """

        deleteList = set()
        users = set(map(lambda x : x.id, self.guildData.users))

        for user in self.importanceDict.keys():
            if user not in users:
                deleteList.add(user)

        for user in deleteList:
            self.remove_user(user)


    def to_json(self) -> dict:
        """
        Returns the json of the social graph
        :return: the json of the social graph
        """
        return {
            "nbMessage":           self.nbMessage,
            "tagMinValue":         self.tagMinValue,
            "importanceInitValue": self.importanceInitValue,
            "importanceDict": {str(k): v for (k, v) in self.importanceDict.items()},
            "agreementDict": {str(k): v for (k, v) in self.agreementDict.items()},
            "taggedDict": {str(k): v for (k, v) in self.taggedDict.items()},
            "nbMessage_at_time": {str(k): v for (k, v) in self.nbMessage_at_time.items()},
            "importanceMaxValue": self.importanceMaxValue,
            "interactionsDict": {str(k): {str(kk): vv for (kk, vv) in v.items()} for (k, v) in self.interactions.items()}
        }



# •======================•
#    SOCIALGRAPHWORKER
# •======================•

class SocialGraphWorker:
    """
    Class SocialGraphWorker
    Generates the socialgraphs for each guild
    API to socialgraph
    :social_graphs: the social graphs
    """

    # Dict of the social graphs
    social_graphs: dict[str, SocialGraph] = dict()

    # •======================•
    #    CONSTRUCTORS
    # •======================•

    def __init__(self):
        """
        Constructor of the SocialGraphWorker class
        """
        self.social_graphs = dict()


    @printExceptions
    def constructor(self, data: dict, guilds_id: set[int], guildsDict: dict) -> None:
        """
        Constructor of the SocialGraphWorker class
        :param data: the data of the social graph
        :param guilds_id: the id of the guilds
        :param guildsDict: the guilds
        :return: None
        """
        self.social_graphs = dict()
        for guild_id in guilds_id:
            if str(guild_id) in data:
                guildInfo = data[str(guild_id)]
                nbPeople = len(guildsDict[guild_id].users)
                nbMessage = int(guildInfo["nbMessage"])
                tagMinValue = guildInfo["tagMinValue"]
                importanceInitValue = guildInfo["importanceInitValue"]
                importanceDict = {int(k): v for (k, v) in guildInfo["importanceDict"].items()}
                agreementDict = {int(k): v for (k, v) in guildInfo["agreementDict"].items()}
                taggedDict = {int(k): v for (k, v) in guildInfo["taggedDict"].items()}
                nbMessage_at_time = {int(k): v for (k, v) in guildInfo["nbMessage_at_time"].items()}
                importanceMaxValue = guildInfo["importanceMaxValue"]
                interactionsDict = {int(k): {int(kk): vv for (kk, vv) in v.items()} for (k, v) in guildInfo["interactionsDict"].items()}

                self.social_graphs[str(guild_id)] = SocialGraph(nbPeople,
                                                                tagMinValue,
                                                                nbMessage,
                                                                importanceDict,
                                                                agreementDict,
                                                                taggedDict,
                                                                guildsDict[guild_id],
                                                                nbMessage_at_time,
                                                                importanceMaxValue,
                                                                importanceInitValue,
                                                                interactionsDict
                                                                )
                self.social_graphs[str(guild_id)].purge()
            else:
                guildData = guildsDict[guild_id]
                SocialGraphWorker.create_default(self, guild_id, guildData)



    @printExceptions
    def create_default(self, guild_id: int, guildData) -> None:
        """
        Create a default social graph for a guild
        :param guild_id: the guild id
        :param guildData: the guild data
        :return: None
        """
        nbPeople = len(guildData.users)
        nbMessage = 0
        tagMinValue = 0.51  # TODO: change this value or load it via json
        try:
            initValue = 1 / nbPeople
        except ZeroDivisionError:
            initValue = 1
        importanceDict: dict[int, float] = dict()
        taggedDict: dict = dict()
        nbMessage_at_time: dict[int, int] = dict()
        interactionsDict: dict[int, dict[int, int]] = dict()
        importanceMaxValue = 0.0
        for user in guildData.users:
            importanceDict[user.id] = initValue
            taggedDict[user.id] = {}
            nbMessage_at_time[user.id] = 0
            interactionsDict[user.id] = dict()
        agreementDict = dict()
        self.social_graphs[str(guild_id)] = SocialGraph(nbPeople,
                                                        nbMessage,
                                                        tagMinValue,
                                                        importanceDict,
                                                        agreementDict,
                                                        taggedDict,
                                                        guildData,
                                                        nbMessage_at_time,
                                                        importanceMaxValue,
                                                        initValue,
                                                        interactionsDict
                                                        )

    # •======================•
    #       ADDERS
    # •======================•

    async def add_user(self, user: discord.User, guild) -> None:
        """
        Adds a user to the social graph
        :param user: the user to add
        :param guild: the guild the user is in
        :return: None
        """
        self.social_graphs[str(guild.id)].add_user(user.id)

    # •======================•
    #       REMOVERS
    # •======================•

    @printExceptions
    async def remove_user(self, user, guild) -> None:
        """
        Removes a user from the social graph
        :param user: the user to remove
        :param guild: the guild the user is in
        :return: None
        """
        self.social_graphs[str(guild.id)].remove_user(user.id)


    # •======================•
    #    COMMANDS HANDLERS
    # •======================•

    @printExceptions
    async def on_command_sentiment(self, message: discord.Message, user, bot) -> None:
        """
        Prints the sentiment of the user
        :param message: the message that triggered the command
        :param bot: the bot
        :return: None
        """
        await self.social_graphs[str(message.guild.id)].on_command_sentiment(message, user, bot)

    @printExceptions
    async def on_command_printall(self, message: discord.Message, bot) -> None:
        """
        Prints the social graph of the server
        :param message: the message that triggered the command
        :param bot: the bot
        :return: None
        """
        await self.social_graphs[str(message.guild.id)].on_command_printall(message,bot)

    @printExceptions
    async def on_command_printuser_all(self, message: discord.Message, userId: int, bot) -> None:
        """
        Prints the social graph of a user
        :param message: the message that triggered the command
        :param userId: the user to print the social graph of
        :param bot: the bot
        :return: None
        """
        #print("here in printuser socialgraphworker")
        await self.social_graphs[str(message.guild.id)].on_command_printuser_all(message, userId, bot)

    @printExceptions
    async def on_command_printuser_distance(self, message: discord.Message, userId: int, distance, bot) -> None:
        """
        Prints the social graph of a user at a certain distance
        :param message: the message that triggered the command
        :param userId: the user to print the social graph of
        :param distance: the distance
        :param bot: the bot
        :return: None
        """
        await self.social_graphs[str(message.guild.id)].on_command_printuser_distance(message, userId, distance, bot)

    @printExceptions
    async def on_command_importance(self, message: discord.Message, user, bot) -> None:
        """
        Prints the importance of a user
        :param message: the message that triggered the command
        :param user: the user to print the importance of
        :param bot: the bot
        :return: None
        """
        await self.social_graphs[str(message.guild.id)].on_command_importance(message,user, bot)

    # •======================•
    #    MESSAGE PROCESSING
    # •======================•

    @printExceptions
    async def on_message(self, message: discord.Message, repliedMessage: discord.Message):
        """
        Updates the social graph when a message is sent
        :param message: the message that was sent
        :param repliedMessage: the message that was replied to
        :return: None
        """
        self.social_graphs[str(message.guild.id)].on_message(message, repliedMessage)

    # •======================•
    #       UTILS
    # •======================•

    @printExceptions
    def isPresent(self, guild_id):
        """
        Checks if the social graph of a guild is present
        """
        return str(guild_id) in self.social_graphs


    @printExceptions
    async def save(self) -> None:
        """
        Saves the social graphs to a json file
        :return: None
        """
        # save to json file name data\social_graphs.json
        data = dict()
        for guild_id in self.social_graphs:
            data[guild_id] = self.social_graphs[guild_id].to_json()
        with open("data/social_graphs.json", "w") as f:
            json.dump(data, f, indent=4)


# •==============================•
#    SOCIAL GRAPH INITIALISATION
# •==============================•

@printExceptions
async def initiate_graph_worker(worker, data, guildsId: set[int], guildsDict) -> None:
    """
    Initiates the social graph worker
    :param worker: the worker
    :param data: the data
    :param guildsId: the guilds id
    :param guildsDict: the guilds dict
    :return: None
    """
    worker.constructor(data, guildsId, guildsDict)
