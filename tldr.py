import asyncio
import re
from datetime import timedelta

import discord
from sentence_transformers import SentenceTransformer

from utils import *

sentenceModel = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# sentenceModel = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')


# sentenceModel = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
summarizer = pipeline("summarization", model="knkarthick/MEETING_SUMMARY")


@printExceptions
async def doTldr(bot: discord.Client, message: discord.Message, messageToEdit: discord.Message, quantity: str = "one",
                 position: str = "around", timeGap: int = 5) -> None:
    """
    Main function of the tldr command, call every function needed to summarize the chat
    :param bot: The bot
    :param message: The message that call the command
    :param messageToEdit: The message to edit with the summary
    :param quantity: The quantity of summary to send
    :param position: The position of the summary
    :param timeGap: The time gap between the summary
    :return: None
    """
    # print("Starting tldr")

    messages, indexMessageInit = getChatByTime(bot, message, timeGap, positionParameter=position)
    # print("Got messages", len(messages))

    translatedMessages = getTranslatedMessage(messages)
    # print("Got Translated messages")  # , translatedMessages)

    # similarityMatrix = similarityAll(translatedMessages, messages)
    similarityMatrix = similarity(translatedMessages, messages)
    # print("Got similarity matrix")
    # dumpjsonMatrix(similarityMatrix)
    # printSimilarityMatrix(similarityMatrix)

    # print(np.min(similarityMatrix), np.max(similarityMatrix))
    clusters = clustering(messages, similarityMatrix, quantity, indexMessageInit)
    # print("Got clusters")
    # printCluster(clusters)

    summarises = summarize(clusters)
    # print("Got summarises")

    sendSummarises(bot, messageToEdit, summarises)

    # cheated(translatedMessages)


@printExceptions
def printSimilarityMatrix(similarityMatrix: np.array) -> None:
    """
    Print the similarity matrix
    Used to debug and test
    :param similarityMatrix: The similarity matrix
    :return: None
    """
    for i in range(len(similarityMatrix)):
        for j in range(len(similarityMatrix[i])):
            simi = similarityMatrix[i][j]
            if simi == -1:
                print("  .  ", end=" ")
                continue
            if simi >= 0:
                print(" ", end="")
            print("{:.2f}".format(simi), end=" ")

        print()


@printExceptions
def dumpjsonMatrix(similarityMatrix: np.array) -> None:
    """
    Dump the similarity matrix in json
    Used to debug and test
    :param similarityMatrix: The similarity matrix
    :return: None
    """

    import json
    with open('matrix.json', 'w') as outfile:
        json.dump(similarityMatrix.tolist(), outfile)


@printExceptions
def printCluster(clusters) -> None:
    """
    Print the clusters
    Used to debug and test
    :param clusters: The clusters
    :return: None
    """
    for i in range(len(clusters)):
        print("\n\nCluster ", i, ":\n")
        for message in clusters[i]:
            print(message.content)


@printExceptions
def postionParameter(position: str) -> tuple[bool, bool]:
    """
    Compute the postion parameter String to a tuple of boolean
    :param position: String of the position parameter
    :return: Tuple of boolean (above, below)
    """
    above = False
    below = False

    if position == "around":
        above = True
        below = True

    elif position == "above":
        above = True

    elif position == "below":
        below = True

    return above, below


@printExceptions
def quantityParameter(quantity: str) -> bool:
    """
    Compute the quantity parameter String to a boolean
    :param quantity: String of the quantity parameter
    :return: Boolean
    """
    if quantity == "one":
        return False
    else:
        return True


@printExceptions
async def getMessagesAfter(channel: discord.TextChannel, message: discord.Message, limit: int) -> list[discord.Message]:
    """
    Coroutines to get messages after a message
    :param channel: Channel to get the messages
    :param message: Message after which we want to get the messages
    :param limit: Limit of messages to get
    :return: List of messages
    """
    return [message async for message in channel.history(limit=limit, after=message)]


@printExceptions
async def getMessagesBefore(channel: discord.TextChannel, message: discord.Message, limit: int) -> \
        list[discord.Message]:
    """
    Coroutines to get messages before a message
    :param channel: Channel to get the messages
    :param message: Message before which we want to get the messages
    :param limit: Limit of messages to get
    :return: List of messages
    """
    return [message async for message in channel.history(limit=limit, before=message)]


@printExceptions
def remove_non_alphanumeric(text) -> str:
    """
    Process text to remove very special characters
    :param text: String to process
    :return: Processed string
    """
    pattern = r'[^a-zA-Z0-9\s.,!?@#%&*_+-=<>/$()\\]'
    return re.sub(pattern, '', text)


@printExceptions
def getChatByTime(bot: discord.Client, messageInit: discord.Message, timeGap: int, positionParameter="around") \
        -> tuple[list, int]:
    """
    Get messages from a channel around, after or before a message depending on the position parameter
    :param bot: Discord bot
    :param messageInit: Message around which we want to get the messages
    :param timeGap: Time gap in minutes
    :param positionParameter: Position parameter
    :return: List of messages, index of the messageInit in the list
    """
    above, below = postionParameter(positionParameter)
    channel = messageInit.channel
    messageCreatedTime = messageInit.created_at
    chat = []

    if above and below:
        limit = 200
    else:
        limit = 100

    if above:

        messagesAbove = asyncio.run_coroutine_threadsafe(getMessagesBefore(channel, messageInit, limit),
                                                         bot.loop).result()
        messagesAbove.insert(0, messageInit)
        date = messageCreatedTime
        cpt = 0
        for actualMessage in messagesAbove:

            if actualMessage.author.bot and cpt > 0:
                continue

            if actualMessage.created_at >= date + timedelta(minutes=-timeGap):
                chat.append(actualMessage)
                date = actualMessage.created_at
            else:
                break

            cpt += 1

        chat.reverse()

    if below:

        messagesBelow = asyncio.run_coroutine_threadsafe(getMessagesAfter(channel, messageInit, limit),
                                                         bot.loop).result()

        if not above:
            messagesBelow.insert(0, messageInit)

        date = messageCreatedTime

        for actualMessage in messagesBelow:

            if actualMessage.author.bot:
                continue

            if actualMessage.created_at <= date + timedelta(minutes=timeGap):
                chat.append(actualMessage)
                date = actualMessage.created_at
            else:
                break

    for message in chat:
        message.content = remove_non_alphanumeric(message.content)

    return chat, chat.index(messageInit)


@printExceptions
def getTranslatedMessage(messages: list[discord.Message]) -> list[str]:
    """
    create a list of translted messages
    :param messages: List of discord.Message
    :return: List of string
    """

    translatedMessages = []
    for message in messages:
        translation = toEnglish(message.clean_content)
        translatedMessages.append(translation)
        message.content = translation

    return translatedMessages


# def hausdorff_distance(list1:list[float], list2:list[float])->float:
#     list1 = np.array(list1).reshape((-1, 1))
#     list2 = np.array(list2).reshape((-1, 1))
#     distance1 = np.max()
#     distances1 = np.array([np.min(np.sqrt(np.sum((list2 - p)**2, axis=1))) for p in list1])
#     distances2 = np.array([np.min(np.sqrt(np.sum((list1 - p)**2, axis=1))) for p in list2])
#     return np.max([np.max(distances1), np.max(distances2)])
# """
#     Compute the Hausdorff distance between two lists of float
#     ::param list1: List of float
#     ::param list2: List of float
#     ::return: Float
# """

@printExceptions
def cosine_distance(list1: np.ndarray, list2: np.ndarray) -> np.float64:
    """
    Compute the cosine distance between two lists of float
    :param list1: List of float
    :param list2: List of float
    :return: float
    """
    dist = np.dot(list1, list2) / (np.linalg.norm(list1) * np.linalg.norm(list2))
    dist = round(dist, 4)
    dist = np.arccos(dist) / np.pi

    return dist


@printExceptions
def euclidean_distance(list1: np.ndarray, list2: np.ndarray) -> float:
    """
    Compute the euclidean distance between two lists of float
    :param list1: List of float
    :param list2: List of float
    :return: float
    """
    dist = np.linalg.norm(list1 - list2)
    return dist


@printExceptions
def distance(embeddingMessage1: np.ndarray, embeddingMessage2: np.ndarray):
    """
    Compute the distance between two messages
    :param embeddingMessage1: np.ndarray
    :param embeddingMessage2: np.ndarray
    :return: Float
    """
    # dist = cosine_distance(embeddingMessage1, embeddingMessage2)
    dist = euclidean_distance(embeddingMessage1, embeddingMessage2)
    # print(dist)
    return dist


@printExceptions
def similarity(tokenMessages: list[str],
               messages: list[discord.Message]) -> np.ndarray:
    """
    More like a distance matrix, 0 = same message, 1 = totally different, -1 = not computed
    :param tokenMessages: list of list of string
    :param messages: list of discord.Message
    :return: np.matrix of size len(messages) x len(messages) and embedding of messages
    """
    nbMessages = len(tokenMessages)

    similarityMatrix = np.full((nbMessages, nbMessages), -1.0)
    messagesId = [message.id for message in messages]

    # preprocess embeddings

    messageEmbeddings = sentenceModel.encode(tokenMessages)
    messageEmbeddings = messageEmbeddings / np.linalg.norm(messageEmbeddings, axis=1, keepdims=True)

    for i in range(nbMessages - 1, -1, -1):

        # print("msg ", i+1, " / ", nbMessages)
        actualMessage = tokenMessages[i]
        actualDiscordMessage = messages[i]
        # print(actualMessage)
        if actualDiscordMessage.type == discord.MessageType.reply:

            repliedMessageId = actualDiscordMessage.reference.message_id

            if repliedMessageId in messagesId:
                index = messagesId.index(repliedMessageId)
                similarityMatrix[i][index] = 0.
                similarityMatrix[index][i] = 0.
                continue
        if not actualMessage:
            continue
        # previous 10 messages
        for j in range(i - 1, i - 11, -1):
            if j < 0:
                break
            previousMessage: str = tokenMessages[j]
            if not previousMessage:
                continue
            # print(previousMessage)
            dist = distance(messageEmbeddings[i], messageEmbeddings[j])

            similarityMatrix[i][j] = dist
            similarityMatrix[j][i] = dist

    # print(type(similarityMatrix))
    return similarityMatrix


@printExceptions
def similarityAll(tokenMessages: list[str],
                  messages: list[discord.Message]) -> np.ndarray:
    """
    More like a distance matrix, 0 = same message, 1 = totally different, -1 = not computed
    :param tokenMessages: list of list of string
    :param messages: list of discord.Message
    :return: np.matrix of size len(messages) x len(messages) and embedding of messages
    """
    nbMessages = len(tokenMessages)

    similarityMatrix = np.full((nbMessages, nbMessages), -1.0)
    messagesId = [message.id for message in messages]
    # preprocess embeddings

    messageEmbeddings = sentenceModel.encode(tokenMessages)

    messageEmbeddings = messageEmbeddings / np.linalg.norm(messageEmbeddings, axis=1, keepdims=True)

    for i in range(nbMessages - 1, -1, -1):

        # print("msg ", i+1, " / ", nbMessages)
        actualMessage: str = tokenMessages[i]
        actualDiscordMessage = messages[i]
        # print(actualMessage)
        if actualDiscordMessage.type == discord.MessageType.reply:

            repliedMessageId = actualDiscordMessage.reference.message_id

            if repliedMessageId in messagesId:
                index = messagesId.index(repliedMessageId)
                similarityMatrix[i][index] = 0.
                similarityMatrix[index][i] = 0.
                continue

        if not actualMessage:
            continue

        # previous messages
        for j in range(i - 1, -1, -1):

            if j < 0:
                break
            previousMessage: str = tokenMessages[j]

            if not previousMessage:
                continue

            # print(previousMessage)
            dist = distance(messageEmbeddings[i], messageEmbeddings[j])

            similarityMatrix[i][j] = dist
            similarityMatrix[j][i] = dist

    # print(np.max(similarityMatrix), np.min(similarityMatrix))
    return similarityMatrix


@printExceptions
def findMinMatrix(similarityMatrix: np.ndarray) -> tuple[int, int, float]:
    """
    Find the minimum value of a matrix
    :param similarityMatrix: np.ndarray
    :return: int, int, float
    """
    min = 1000
    minI = -1
    minJ = -1
    for i in range(len(similarityMatrix)):
        for j in range(i + 1, len(similarityMatrix)):
            if similarityMatrix[i][j] < min:
                min = similarityMatrix[i][j]
                minI = i
                minJ = j
    return minI, minJ, min


@printExceptions
def wardDistance(cluster1, cluster2, similarityMatrix) -> float:
    """
    Compute the Ward distance between two clusters
    :param cluster1: list of int
    :param cluster2: list of int
    :param similarityMatrix: np.matrix
    :return: float
    """
    total = 0.
    for message1 in cluster1:
        for message2 in cluster2:
            total += similarityMatrix[message1][message2]
    n = len(cluster1) + len(cluster2)
    n = n * n
    return 2 * total / n - (len(cluster1) / n) - (len(cluster2) / n)


@printExceptions
def minTwoCluster(cluster1, cluster2, similarityMatrix) -> float:
    """
    Compute the distance between two clusters
    :param cluster1: list of int
    :param cluster2: list of int
    :param similarityMatrix: np.matrix
    :return: float
    """
    min = 1000.
    for message1 in cluster1:
        for message2 in cluster2:
            val = similarityMatrix[message1][message2]
            if val != -1.0 and val < min:
                min = similarityMatrix[message1][message2]
    return min


@printExceptions
def clusterSimilarity(similarityMatrix: np.ndarray,
                      clusters: list[np.ndarray]) -> np.ndarray:
    """
    Compute the similarity between clusters
    :param similarityMatrix: np.matrix
    :param clusters: list of np.ndarray
    :return: np.matrix
    """
    nbClusters = len(clusters)
    clusterSimilarityMatrix = np.full((nbClusters, nbClusters), -1.0)
    for i in range(nbClusters):
        for j in range(i + 1, nbClusters):
            if len(clusters[i]) == 0 or len(clusters[j]) == 0:
                continue
            if i == j:
                continue
            if clusterSimilarityMatrix[i][j] != -1.0:
                continue

            cluster1 = clusters[i]
            cluster2 = clusters[j]
            # dist = minTwoCluster(cluster1, cluster2, similarityMatrix)
            dist = wardDistance(cluster1, cluster2, similarityMatrix)
            clusterSimilarityMatrix[i][j] = dist
            clusterSimilarityMatrix[j][i] = dist
    # rintSimilarityMatrix(clusterSimilarityMatrix)
    return clusterSimilarityMatrix


@printExceptions
def clustering(messages: list[discord.Message],
               similarityMatrix: np.ndarray,
               quantity: str,
               messageInitIndex: int
               ) -> list[list[discord.Message]]:
    """
    Clustering of messages with hierarchical ascending classification
    :param messages: list of discord.Message
    :param similarityMatrix: np.matrix
    :param quantity: str
    :param messageInitIndex: int
    :return: list of list of discord.Message
    """
    # print("Clustering")
    all = quantityParameter(quantity)

    cluster = []
    for i in range(len(messages)):
        cluster.append([i])
    # print(len(cluster), " clusters")
    while len(cluster) > 1:
        clusterSimi = clusterSimilarity(similarityMatrix, cluster)
        minI, minJ, min = findMinMatrix(clusterSimi)
        if min > -0.1 and len(cluster) <= 3:  # TODO: change this value
            break
        cluster[minI] = cluster[minI] + cluster[minJ]
        cluster.pop(minJ)

        # print(len(cluster), "min", min, )

    # print(len(cluster), " clusters")

    if all:
        return [[messages[i] for i in c] for c in cluster]
    else:
        c = None
        for i in range(len(cluster)):
            if messageInitIndex in cluster[i]:
                c = cluster[i]
                break
    return [[messages[i] for i in c]]


@printExceptions
def summarize(messagesCluster: list[list[discord.Message]]) -> list[tuple[str, discord.Message]]:
    """
    Summarize Every cluster of messages
    :param messagesCluster: list of list of discord.Message
    :return: list of tuple of, Summary For one cluster and the first message of the cluster
    """
    summarises = []
    try:
        for cluster in messagesCluster:
            text = ""
            for m in cluster:
                if m.content == "":
                    continue
                if m.author.nick is None:
                    name = m.author.name
                else:
                    name = m.author.nick
                text += name + ": " + m.content + " \n"

            if len(text) > 1024:
                text = text[:1023]

            size = len(text) // 3
            if size > 512:
                size = 512
            elif size < 11:
                size = 11
            # print(size, len(text))
            sum = summarizer(text, max_length=size, min_length=size // 4, do_sample=False)
            summarises.append((sum[0]["summary_text"], cluster[0]))

    except Exception as e:
        print(e)

    return summarises


@printExceptions
def sendSummarises(bot: discord.Client,
                   messageToEdit: discord.Message,
                   listSummarise: list[tuple[str, discord.Message]]
                   ) -> None:
    """
    Send the summarises
    :param bot: discord.Client
    :param messageToEdit: discord.Message
    :param listSummarise: list of tuple of str and discord.Message
    :return: None
    """

    try:
        channel = messageToEdit.channel
        if channel is None:
            return
        messageRef = messageToEdit.reference
        if messageRef is None:
            return

        message = messageRef.resolved
        if message is None:
            return
        # delete message to edit
        asyncio.run_coroutine_threadsafe(messageToEdit.delete(), bot.loop)

        # Send a message tagging the message.author to notify them
        asyncio.run_coroutine_threadsafe(channel.send(message.author.mention + ' your TL;DR(s):'), bot.loop).result()

        # send summarises
        for i in range(len(listSummarise)):
            sum = listSummarise[i][0]
            msgtoReply = listSummarise[i][1]
            if len(sum) > 2000:
                sum = sum[:2000]
            asyncio.run_coroutine_threadsafe(msgtoReply.reply(sum, mention_author=False), bot.loop)

    except Exception as e:
        print(e)


@printExceptions
# CHEATED
def cheated(corpus):
    """
    Clustering of messages with hierarchical ascending classification but pre-implemented so it's cheating
    :param corpus: list of str
    :return: None
    """
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import AgglomerativeClustering

    print("\n\nCHEATED:\n")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    corpus_embeddings = embedder.encode(corpus)

    # Normalize the embeddings to unit length
    corpus_embeddings = corpus_embeddings / np.linalg.norm(corpus_embeddings, axis=1, keepdims=True)
    # print(np.min(corpus_embeddings), np.max(corpus_embeddings))
    # Perform clustering
    clustering_model = AgglomerativeClustering(n_clusters=None,
                                               distance_threshold=2)  # , affinity='cosine', linkage='average')
    clustering_model.fit(corpus_embeddings)
    cluster_assignment = clustering_model.labels_

    clustered_sentences = {}
    for sentence_id, cluster_id in enumerate(cluster_assignment):
        if cluster_id not in clustered_sentences:
            clustered_sentences[cluster_id] = []

        clustered_sentences[cluster_id].append(corpus[sentence_id])

    for i, cluster in clustered_sentences.items():
        print("Cluster ", i + 1)
        print(cluster)
        print("")
