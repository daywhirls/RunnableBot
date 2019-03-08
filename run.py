# Work with Python 3.6
import discord
from random import shuffle
import copy
import pickle
import os
import math
import creds # used for local testing

"""
##### 5 FIRE CEO BOT #####
Author: David / Runnable
Discord: Runnable#0001
GitHub: daywhirls

TODOS:
    -   Limit the bot to only be usable in certain channel
    -   Have bot continuously update current-queue channel upon
        receiving an update in the bot commands channel
    -   Fix math issue with splitting teams
    -   Make group splitting work for infinite amount of groups:
            1)  [loop]  shuffle queue
            2)          divide evenly into numberOfGroups amt of groups
            3)
    ^   OR
            give 2 commands: splitEven and group 8s
"""

# LOCAL authentication
TOKEN = creds.TOKEN

# HEROKU Config Var
#TOKEN = str(os.environ.get('TOKEN'))

client = discord.Client()

queue = []
splits = [] # list of smaller group lists
queue.append(('Runnable', 25, '<@!285861225491857408>')) # PASTE THIS FOR TESTING
queue.append(('Runnable2', 25, '<@!285861225491857408>'))
queue.append(('Runnable3', 8, '<@!285861225491857408>'))
queue.append(('Runnable4', 38, '<@!285861225491857408>'))
queue.append(('Runnable5', 38, '<@!285861225491857408>'))
queue.append(('Runnable6', 38, '<@!285861225491857408>'))
queue.append(('Runnable7', 38, '<@!285861225491857408>'))
queue.append(('Runnable8', 38, '<@!285861225491857408>'))
queue.append(('Runnable9', 38, '<@!285861225491857408>'))
queue.append(('Runnable11', 38, '<@!285861225491857408>'))
queue.append(('Runnable22', 38, '<@!285861225491857408>'))
queue.append(('Runnable33', 38, '<@!285861225491857408>'))
queue.append(('Runnable44', 38, '<@!285861225491857408>'))
queue.append(('Runnable55', 38, '<@!285861225491857408>'))
queue.append(('Runnable66', 38, '<@!285861225491857408>'))
queue.append(('Runnable77', 38, '<@!285861225491857408>'))

# Cheese 35 = AVERAGE VALUE needed for 5 fires
# Fires = (TotalValue / NumOfPeople)
def convertSuitValue(level):
    return int(level) + 28

# create a data structure or textfile to store queued people
# overwrites previous queue
def wipeQueue():
    queue.clear()

# TODO: Don't pass half fires to minimumValue.
        # split groups first, then check each group's fire count

# Takes total fireValue and numberOfGroups and returns minimum value needed
# for each group to have the highest possible even fire amount
# first param numGroups or queueSize??
def minimumValue(numGroups, queueSize, fireValue):
    # hardcoded max groupsize = 2 for now, fireValue = half the total value
    print("fireValue: " + str(fireValue))
    print("queueSize: " + str(queueSize))
    print("numGroups: " + str(numGroups))
    numFires = fireValue // (queueSize / 2)
    print("minimumValue(): " + str(numFires))
    # numFires is the highest each group can be
    if numFires < 17:
        return 1
    elif numFires < 33:
        return 2
    elif numFires < 48:
        return 3
    elif numFires < 63:
        return 4
    else:
        return 5

# repeatedly shuffles queue until all groups satisfy the minumum fireValue
# minumumValue is called before this, and that value is fireValue
def shuffleGroups(numGroups, minFires):
    print("MinFires: " + str(minFires))
    satisfied = False
    tempList = copy.copy(queue)
    group1 = []
    group2 = []

    while not satisfied:
        print("Shuffling list...")
        shuffle(tempList)

        # break into 2 groups
        group1 = tempList[::2]
        group2 = tempList[1::2]

        # check both groups fires using calculateFires(numberInGroup / fireVal)
        groupOneFires = getCountFires(group1)
        groupTwoFires = getCountFires(group2)

        #check both groups fires to see if they equal minFires
        if groupOneFires >= minFires and groupTwoFires >= minFires:
            satisfied = True

    return group1, group2, groupOneFires, groupTwoFires

# Makes sure the user's role has acceptable permissions
def verifyRole(role):
    roles = ['The Chief Cheese', 'Cheese Executive Officer', 'Aged Gouda']
    return role in roles


def getCountFires(group):
    queueSize = 0
    totalValue = 0
    fires = 0
    avgFireVal = 0

    for i in group:
        queueSize += 1
        totalValue += convertSuitValue(i[1])
    avgFireVal = totalValue/queueSize
    fires = calculateFires(avgFireVal)
    return fires

# Too tired to remember how to get this with floor/ceiling/modulus fam
def howManyGroups():
    x = len(queue)
    if x <= 8:
        return 1
    elif x <= 16:
        return 2
    elif x <= 24:
        return 3
    elif x <= 32:
        return 4
    elif x <= 40:
        return 5
    elif x <= 48:
        return 6
    elif x <= 56:
        return 7
    elif x <= 64:
        return 8
    elif x <= 72:
        return 9
    elif x <= 80:
        return 10
    elif x <= 88:
        return 11
    elif x <= 96:
        return 12
    elif x <= 104:
        return 13
    else:
        return -1

# divide total number of queued people by 8 to see how to balance people.
# find combo of values that is most equally spread across numberOfGroups.
# This only gets called if queue > 8
def balanceGroups(numGroups):
    '''
    # read in the entire queue
    # calculate total number of people and total value
    queueSize = 0
    totalValue = 0
    fires = 0

    for i in queue:
        queueSize += 1
        totalValue += convertSuitValue(i[1])
    fires = totalValue/queueSize

    # if queueSize > 8, figure out how to split evenly
    if queueSize > 8:
        g1Fires = 0
        g2Fires = 0
        # for now, assume there won't be more than 16 queue up.
        halfway = totalValue / 2
        groupOne, groupTwo, g1Fires, g2Fires = shuffleGroups(2, minimumValue(2, queueSize, halfway))

        # Append first group to return msg
        msg = "Group 1: [" + str(g1Fires) + "] Fires\n";
        for i in groupOne:
            msg += i[0] + "\t\t\t[BC " + str(i[1]) + "]\n"

        # Append second group to return msg
        msg += "\n\nGroup 2: [" + str(g2Fires) + "] Fires\n";
        for i in groupTwo:
            msg += i[0] + "\t\t\t[BC " + str(i[1]) + "]\n"

        return msg

    # This msg returns if there is no need to split groups (only 1 group)
    msg = "One Group. Everyone in Queue goes!\nToons: " + str(queueSize) + "\nFires: " + str(calculateFires(fires))
    return msg
    '''

    tempList = copy.copy(queue)
    splits = [[] for i in range(numGroups)]
    fireNums = []

    # sort queue and evenly distribute them across numGroups amount of groups
    #tempList.sort()

    tempList.sort(key=lambda x: x[1])

    # distribute members to the teams
    splitList = 0 # increment this to drop into each; reset to 0 if = len(splits)
    for i in tempList:
        splits[splitList].append(i)
        splitList += 1
        if splitList is len(splits):
            splitList = 0

    # print statements for testing
    #print("Number of groups: " + str(numGroups))
    #print("Number of split lists created: " + str(len(splits)))
    #print("Len of splits[0]: " + str(len(splits[0])))
    #print("Len of splits[1]: " + str(len(splits[1])))

    # calculate fires for each group
    for i in range(len(splits)):
        fireNums.append(getCountFires(splits[i]))

    #format message with groups to send to Discord
    msg = ""
    for i in range(len(splits)):
        tempMsg = ""
        # form msg string for one group, append it to final msg each time
        tempMsg = "Group " + str(i+1) + ": [" + str(fireNums[i]) + "] Fires\n";
        for j in splits[i]:
            tempMsg += j[0] + "\t\t\t[BC " + str(j[1]) + "]\n"
        msg += tempMsg + "\n\n"

    return msg

# returns the index of the user if they exist, or False if DNE
def checkList(name):
    for i in range(len(queue)):
        print(queue[i][0])
        if queue[i][0].lower() == name.lower():
            print("Match")
            return i
    return -1

def calculateFires(x):
    x = int(x)
    if x < 17:
        return 1
    elif x < 33:
        return 2
    elif x < 48:
        return 3
    elif x < 63:
        return 4
    else:
        return 5

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return

    # add user to list of people queuing up
    # if user is already in list, update their parameter
    # handle 2nd argument with their suit level & failing elegantly
    if message.content.startswith('!ceo'):
        cmd = message.content.split() # split by spaces
        msg = ""
        # make sure the message.content is 3 words: [arg name level]
        if len(cmd) is not 3 or not cmd[2].isdigit():
            msg = "**Failed**: Idk what you mean fam. Type `!ceo [Name] [Suit Level]`.\nExample:  `!ceo Runnable 50`\nPlease only use **one word** for your name here."
        elif int(cmd[2]) < 8 or int(cmd[2]) > 50:
            msg = "**Failed**: Your suit level must be between 8 and 50. Get rekt."
        elif checkList(cmd[1]) is not -1:
            msg = "**Failed**: This person already exists in the queue.\nIf you added them, you can update the entry by using !remove and re-adding them."
        else: # we gucci fam
            queue.append((str(cmd[1]), int(cmd[2]), '{0.author.mention}'.format(message)))
            msg = '{0.author.mention}'.format(message) + " added `" + str(cmd[1]) + " [BC " + str(cmd[2]) + "]` to the queue.\nTo edit the entry, type **!remove " + str(cmd[1]) + "** and then re-add it."

        await client.send_message(message.channel, msg)

    elif message.content.startswith('!queue'):
        if not queue:
            msg = "List is empty! use `!ceo [Name] [8-50]` to add someone!"
        else :
            msg = "```"
            for i in queue:
                msg += "[BC " + str(i[1]) + "]\t" + i[0] + "\n"
            msg += "```"
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!split'):
        numGroups = howManyGroups()
        if numGroups is -1:
            msg = "**Failed**: I can only handle spliting 104 toons at a time. Sorry fam."
        else:
            msg = balanceGroups(numGroups)
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!wipe'):
        msg = ""
        if verifyRole('{0.author.top_role}'.format(message)): # User has permission to wipe queue
            wipeQueue()
            msg = "Emptied Queue!"
        else:
            msg = "**Failed**: You do not have permission to wipe the queue."

        await client.send_message(message.channel, msg)

    elif message.content.startswith('!help'):
        msg = "Type `!ceo [Big Cheese Level]` to queue for the CEO.\n ```Ex: !ceo 50```"
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!remove'):
        msg = ""
        cmd = message.content.split() # split by spaces

        # Make sure cmd = 2, [!remove -name-]
        if len(cmd) is not 2:
            msg = "**Failed**: Must give 1 argument.\nExample: `!remove Runnable`"
            await client.send_message(message.channel, msg)
            return
        # Check queue for this person
        index = checkList(cmd[1])
        requestor = '{0.author.mention}'.format(message)
        if index is -1: # returns False if DNE
            msg = "This person does not exist fam.\nTry again or type **!queue** to view the queue."
        # Verify the person removing the entry actually added it in the first place
        elif queue[index][2] != requestor:
            msg = "**Failed**: You cannot remove someone that you didn't add to the queue.\n```Get rekt.```"
        else:
            del queue[index]
            msg = "**Success**. `" + cmd[1] + "` has been removed from the Queue."

        await client.send_message(message.channel, msg)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)
