# Work with Python 3.6
import discord
from random import shuffle
import copy
import pickle
import os
#import creds # used for local testing

"""
##### 5 FIRE CEO BOT #####
Author: David / Runnable
Discord: Runnable#0001
GitHub: daywhirls

TODO:
    - Allow Discord server staff to remove anyone's entry (in case of trolling)
"""

# LOCAL authentication
#TOKEN = creds.TOKEN

# HEROKU Config Var
TOKEN = str(os.environ.get('TOKEN'))

client = discord.Client()

queue = []
splits = [] # list of smaller group lists

# MODIFY/PASTE THESE FOR TESTING
'''
queue.append(('Runnable', 25, '<@!285861225491857408>'))
queue.append(('Static', 50, '<@!285861225491857408>'))
queue.append(('Ferret', 8, '<@!285861225491857408>'))
queue.append(('Polar', 38, '<@!285861225491857408>'))
queue.append(('Trials', 10, '<@!285861225491857408>'))
queue.append(('Tarnation', 8, '<@!285861225491857408>'))
queue.append(('Anchovy', 50, '<@!285861225491857408>'))
queue.append(('Sheriff', 42, '<@!285861225491857408>'))
queue.append(('Vitamin', 38, '<@!285861225491857408>'))
queue.append(('Deer', 50, '<@!285861225491857408>'))
queue.append(('Gorilla', 50, '<@!285861225491857408>'))
queue.append(('Host', 38, '<@!285861225491857408>'))
queue.append(('Cold', 35, '<@!285861225491857408>'))
queue.append(('Noodle', 50, '<@!285861225491857408>'))
queue.append(('Yikes', 22, '<@!285861225491857408>'))
queue.append(('Forehead', 12, '<@!285861225491857408>'))
'''

# Cheese 35 = AVERAGE VALUE needed for 5 fires
# Fires = (TotalValue / NumOfPeople)
def convertSuitValue(level):
    return int(level) + 28

# create a data structure or textfile to store queued people
# overwrites previous queue
def wipeQueue():
    queue.clear()


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

    tempList = copy.copy(queue)
    splits = [[] for i in range(numGroups)]
    fireNums = []

    # sort queue and evenly distribute them across numGroups amount of groups
    #tempList.sort()
    tempList.sort(key=lambda x: x[1], reverse=True)

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
        tempMsg = "__Group " + str(i+1) + "__\t**" + str(fireNums[i]) + " Fires**\n";
        for j in splits[i]:
            #tempMsg += j[0] + "\t\t\t[BC " + str(j[1]) + "]\n"
            tempMsg += j[0] + "\n"
        msg += tempMsg + "\n\n"

    return msg


# returns the index of the user if they exist, or False if DNE
def checkList(name):
    for i in range(len(queue)):
        if queue[i][0].lower() == name.lower():
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
    if message.author == client.user or message.server is None:
        return

    if message.content.startswith('!add'):
        cmd = message.content.split() # split by spaces
        msg = ""
        # make sure the message.content is 3 words: [arg name level]
        if len(cmd) is not 3 or not cmd[2].isdigit():
            msg = "**Failed**: Idk what you mean fam. Type `!add [Name] [Suit Level]`.\n__Example__:  `!add Runnable 50`\nPlease only use **one word** for your name here."
        elif int(cmd[2]) < 8 or int(cmd[2]) > 50:
            msg = "**Failed**: Your suit level must be between 8 and 50. Get rekt."
        elif checkList(cmd[1]) is not -1:
            msg = "**Failed**: This person already exists in the queue.\nIf you added them, you can update the entry by using !remove and re-adding them."
        else: # we gucci fam
            queue.append((str(cmd[1]), int(cmd[2]), '{0.author.mention}'.format(message)))
            msg = '{0.author.mention}'.format(message) + " added `" + str(cmd[1]) + " [BC " + str(cmd[2]) + "]` to the queue.\nTo edit the entry, type **!remove " + str(cmd[1]) + "** and then re-add it.\n\n"
            msg += "Current Queue:\n```"
            for i in queue:
                msg += "[BC " + str(i[1]) + "]\t" + i[0] + "\n"
            msg += "```"
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!queue'):
        if not queue:
            msg = "List is empty! use `!add [Name] [8-50]` to add someone!"
        else :
            msg = "```"
            for i in queue:
                msg += "[BC " + str(i[1]) + "]\t" + i[0] + "\n"
            msg += "```"
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!split'):
        if len(queue) is 0:
            msg = "**Failed**: There's nobody in the queue fam.\n```U cAnT dO tHaT```"
            await client.send_message(message.channel, msg)
            return
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

    elif message.content.startswith('!remove'):
        msg = ""
        cmd = message.content.split() # split by spaces

        # Make sure cmd = 2, [!remove -name-]
        if len(cmd) is not 2:
            msg = "**Failed**: Must give 1 argument.\n__Example__: `!remove Runnable`"
            await client.send_message(message.channel, msg)
            return
        # Check queue for this person
        index = checkList(cmd[1])
        requestor = '{0.author.mention}'.format(message)
        if index is -1: # returns False if DNE
            msg = "This person does not exist fam.\nTry again or type **!queue** to view the queue."
        # Verify the person removing the entry actually added it in the first place
        #elif queue[index][2] != requestor:
        #    msg = "**Failed**: You cannot remove someone that you didn't add to the queue.\n```Get rekt.```"
        else:
            del queue[index]
            msg = "**Success**. `" + cmd[1] + "` has been removed from the Queue."

        await client.send_message(message.channel, msg)

    elif message.content.startswith('!help'):
        msg = "**Welcome to RunBot by  <@!285861225491857408>**\n\n__**COMMANDS**__\n\n"

        # !add
        msg += "`!add`\n"
        msg += "Use this to add yourself or anyone else to the CEO queue!\n"
        msg += "```Usage:\t  !add [Name] [Suit Level]\n"
        msg += "Example:\t!add Runnable 50```\n"
        msg += "__NOTE__: Name must only be one word, and Suit level must be >= 8 and <= 50.\n\n\n"

        # !remove
        msg += "`!remove`\n"
        msg += "Use this to remove someone you added to the queue.\n"
        msg += "```Usage:\t  !queue [Name in Queue]\n"
        msg += "Example:\t!queue Runnable```\n"
        msg += "__NOTE__: To prevent trolling, you can only remove people you personally added to the queue.\n"
        msg += "__NOTE__: If you made a mistake or want to update your entry, use this to remove the old one, and then re-add it.\n\n\n"

        # !queue
        msg += "`!queue`\n"
        msg += "Use this to view everyone currently signed up for the CEO run.\n"
        msg += "```Usage:\t  !queue\n"
        msg += "Example:\t!queue```\n"
        msg += "__NOTE__: This command takes no arguments.\n\n\n"

        # !split
        msg += "`!split`\n"
        msg += "Use this to evenly split the queue into teams for the highest fires possible.\n"
        msg += "```Usage:\t  !split\n"
        msg += "Example:\t!split```\n"
        msg += "__NOTE__: This command takes no arguments.\n"
        msg += "__NOTE__: This bot is capable of evenly splitting up to 13 full groups (104 toons) evenly.\n\n\n"

        # !wipe
        msg += "`!wipe`\n"
        msg += "Use this to wipe the current queue and start from scratch.\n"
        msg += "```Usage:\t  !wipe\n"
        msg += "Example:\t!wipe```\n"
        msg += "__NOTE__: This command takes no arguments.\n"
        msg += "__NOTE__: To prevent trolling, **only** these roles can wipe the queue: "
        msg += "**The Chief Cheese, Cheese Executive Officer, Aged Gouda**"

        await client.send_message(message.channel, msg)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)
