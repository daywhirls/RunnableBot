# Work with Python 3.6
import discord
from random import shuffle
import copy
import pickle
import os
# import creds # used for local testing

"""
##### 5 FIRE CEO BOT #####

DESIGN:
    SCHEDULE POLL
        - On a timer, make a poll once a week for people to vote on 2 runs
        - Once that expires, record results, post the official schedule.
    QUEUE
        - One hour before it begins, start assembling team(s)
        - Accept 1 parameter asking what their suit is, handle user errors
        - Parse their suit level in accordance with fire chart to calculate fires
        - Balance teams so everyone gets highest amount of fires
        - Announce teams by @'ing all users and show how many fires each group is
        - Allow people to continue adding themselves to queue if needed after time starts
        - Allow someone to add someone to the list that isn't them
        - If someone new gets added, let users resort the group
        - Currently only handles splitting into 2 groups, for now just
            check if its > 16 and if so, be like sorry fam lol

    HELP
        - Detailed HELP Message

"""
# LOCAL authentication
# TOKEN = creds.TOKEN

# HEROKU Config Var
TOKEN = str(os.environ.get('TOKEN'))

client = discord.Client()

queue = []
queue.append(('<@!285861225491857408>', 30))
queue.append(('<@!285861225491857408>', 8))
queue.append(('<@!285861225491857408>', 20))
queue.append(('<@!285861225491857408>', 8))
queue.append(('<@!285861225491857408>', 8))
queue.append(('<@!285861225491857408>', 12))
queue.append(('<@!285861225491857408>', 8))

# Cheese 8 = 36
# Cheese 50 = 78
# Cheese 35 = AVERAGE VALUE needed for 5 fires
# Fires = (TotalValue / NumOfPeople)
def convertSuitValue(level):
    return int(level) + 28

# create a data structure or textfile to store queued people
# overwrites previous queue
def createQueue():
    queue.clear()

# Takes total fireValue and numberOfGroups and returns minimum value needed
# for each group to have the highest possible even fire amount
# first param numGroups or queueSize??
def minimumValue(numGroups, queueSize, fireValue):
    # hardcoded max groupsize = 2, fireValue = half the total value
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

# Populates queue with dummy data for testing
def saveQueue():
    with open('mylist', 'wb') as f:
        pickle.dump(queue, f)

def readQueue():
    with open('mylist', 'rb') as f:
        queue = pickle.load(f)


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

def getCountFires(group):
    queueSize = 0
    totalValue = 0
    fires = 0
    avgFireVal = 0

    for i in queue:
        queueSize += 1
        totalValue += convertSuitValue(i[1])
    avgFireVal = totalValue/queueSize
    fires = calculateFires(avgFireVal)
    print("getCountFires(): " + str(fires))
    return fires

# divide total number of queued people by 8 to see how to balance people.
# find combo of values that is most equally spread across numberOfGroups.
# This only gets called if queue > 8
def balanceGroups():

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
        print("About to get groups...")
        groupOne, groupTwo, g1Fires, g2Fires = shuffleGroups(2, minimumValue(2, queueSize, halfway))
        print("Got groups! Holy shit!!!")

        # Append first group to return msg
        msg = "Group 1: [" + str(g1Fires) + "] Fires\n";
        for i in groupOne:
            msg += i[0] + "\t\t\t\t[BC " + str(i[1]) + "]\n"

        # Append second group to return msg
        msg += "\n\nGroup 2: [" + str(g2Fires) + "] Fires\n";
        for i in groupTwo:
            msg += i[0] + "\t\t\t\t[BC " + str(i[1]) + "]\n"

        return msg

    # This msg returns if there is no need to split groups (only 1 group)
    msg = "Toons: " + str(queueSize) + "\nFires: " + str(calculateFires(fires))
    return msg

# returns true if user already exists in queue, false otherwise.
# use this in '!ceo' code to either update value or add new person
def checkList(tuple):
    return False

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
        level = message.content[5:]
        if not level.isdigit():
            msg = "Idk wtf you said. use !help for usage fam"
        elif int(level) >= 8 and int(level) <= 50:
            queue.append(('{0.author.mention}'.format(message), int(level)))
            msg = '{0.author.mention}'.format(message) + ' is queued for CEO!'
            #msg = "Your value is " + str(convertSuitValue(int(level))) + "."
        else:
            msg = 'Your suit level must be between from 8 to 50. Try again.'

        await client.send_message(message.channel, msg)

    elif message.content.startswith('!help'):
        msg = "Type `!ceo [Big Cheese Level]` to queue for the CEO.\n ```Ex: !ceo 50```"
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!queue'):
        print(str(queue))
        if not queue:
            msg = "List is empty! use `!ceo [BC level]` to add someone!"
        else :
            msg = ""
            for i in queue:
                msg += i[0] + "\t\t\t\t[BC " + str(i[1]) + "]\n"
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!go'):
        msg = balanceGroups()
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!save'):
        saveQueue()
        msg = "Saved to file!"
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!load'):
        readQueue()
        msg = "Read in file!"
        print(queue)
        await client.send_message(message.channel, msg)

    elif message.content.startswith('!wipe'):
        createQueue()
        msg = "Emptied Queue!"
        await client.send_message(message.channel, msg)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.run(TOKEN)
