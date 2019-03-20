# Work with Python 3.6
import discord # 0.16.12
import asyncio
from random import shuffle
import copy
import pickle
import os
import schedule # 0.6.0
from datetime import datetime
from datetime import date
#import creds # used for local testing

"""
##### 5 FIRE CEO BOT #####
Author: David / Runnable
Discord: Runnable#0001
GitHub: daywhirls

TODO:
    - Store the poll messages each week so the reactions can be counted
      to determine and announce the winning days/times.
    - implement schedule[] FIFO queue that stores day/times of each run
      and uses event scheduler to ping #run-schedule before each run starts,
      wipes queue, and then pops off that run and waits for the next one.

"""

# LOCAL authentication
#TOKEN = creds.TOKEN

# HEROKU Config Var
TOKEN = str(os.environ.get('TOKEN'))

client = discord.Client()

queue = []
splits = [] # list of smaller group lists
fireNums = []

# each week after schedule vote is counted, store the run times here.
# will be used for pinging everyone, wiping queue, etc.
# treat as a FIFO queue. handle the first one, erase it, etc.
schedule = []

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

# erase previous split groups before re-splitting
def wipeSplits():
    splits.clear()

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

def populateSplits(numGroups):
    #splits = [[] for i in range(numGroups)]
    for i in range(numGroups):
        splits.append([])

def replaceTuple(new):
    return 1

# Swap two people who are the same level ONLY between groups
# group1 and group2 are indexes of group in splits[]
# persons come from splits[i][0]
# groups come from splits[i]
# So need both group indexes inside splits[].
# After that, search for the person and check their levels
# to confirm that they're the same. If not, exit with fail msg
# Also do basic checking to make sure groups exist & people exist in them
def swapGroups(personOne, personTwo):
    personOneLocation = -1
    personTwoLocation = -1
    personOneLevel = -1
    personTwoLevel = -1

    # confirm both people actually exist in lists
    #print(str(len(splits)))

    '''
    for group in range(len(splits)):
        print("Looping thru splits[group]: " + str(splits[group][0]))
        if splits[group][0] == personOne:
            personOneLocation = group
        elif splits[group][0] == personTwo:
            personTwoLocation = group
    '''
    # loop through every split group checking for both names given
    for i in range(len(splits)):
        for j in splits[i]:
            # j[0] is the names
            if j[0] == personOne:
                personOneLocation = i # splits[i] is the group
                personOneLevel = j[1]
            elif j[0] == personTwo:
                personTwoLocation = i
                personTwoLevel = j[1]

    if personOneLocation is -1 or personTwoLocation is -1:
        msg = "**Failed**: One or neither people exist. Try again fam."

    elif personOneLocation == personTwoLocation:
        msg = "Uh.. These people are in the same group already fam. Wyd????"

    # only let people swap identical lvls to prevent unfair splits
    elif personOneLevel is not personTwoLevel:
        msg = "**Failed**. If this swap happens, one group will have lower fires than desired. You can only swap people that are the same level for now!"

    else: # we gucci fam. Let's swap them bois
        count = 0
        for i in splits[personOneLocation]:
            if i[0] == personOne:
                new = list(i)
                new[0] = personTwo
                # convert back to tuple and replace old one
                splits[personOneLocation][count] = tuple(new)
            count += 1
        count = 0
        for i in splits[personTwoLocation]:
            if i[0] == personTwo:
                new = list(i)
                new[0] = personOne
                i = tuple(new)
                splits[personTwoLocation][count] = tuple(new)
            count += 1

        msg = "**Success**. Swapped " + personOne + " and " + personTwo + ".\n"
        msg += "__Note__: Re-splitting the queue will override this swap.\n\n"
        for i in range(len(splits)): # TODO: Put this into printSplits(), not pasted twice
            tempMsg = ""
            # form msg string for one group, append it to final msg each time
            tempMsg = "__Group " + str(i+1) + "__\t**" + str(fireNums[i]) + " Fires**\n";
            for j in splits[i]:
                # TODO: Swap the level and names around so it looks nice.
                # TODO: If lvl is 8 or 9, add a 0 in front of it for formatting
                #tempMsg += j[0] + "\t\t\t[BC " + str(j[1]) + "]\n"
                tempMsg += j[0] + "\n"
            msg += tempMsg + "\n"

        return msg

    return msg

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
    #splits = [[] for i in range(numGroups)]
    populateSplits(numGroups)
    #fireNums = []

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
            # TODO: Swap the level and names around so it looks nice.
            # TODO: If lvl is 8 or 9, add a 0 in front of it for formatting
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


# throw the voting msg id's into a data structure so the bot can return
# to it at the end of the day to calculate winning schedules and send to schedule[]
def savePoll():
    return False


# test channel = '553420403033505792'
# official channel = '553493689880543242'
async def schedulePoll():
    await client.wait_until_ready()
    message_channel=client.get_channel('553493689880543242') # not used yet swag
    while not client.is_closed:
        now = datetime.today().strftime('%a %H:%M')
        if now == 'Sun 02:00':
            time = 82800 # sleep 23 hours and then check every minute

            today = datetime.today().strftime('%B %d, %Y')
            msg = "__**Week of " + today + "**__\n\n"

            msg += "**Choose __Weekday__ Schedule**:\n"
            msg += "🇦  Monday\n"
            msg += "🇧  Tuesday\n"
            msg += "🇨  Wednesday\n"
            msg += "🇩  Thursday\n"

            reactions = ['🇦', '🇧', '🇨', '🇩']

            weekday = await client.send_message(client.get_channel('553493689880543242'), msg)
            for choice in reactions:
                await client.add_reaction(weekday, choice)

            msg = "`What Week Day Time? (P.M. EST)`"
            reactions = ['6⃣', '7⃣', '8⃣', '9⃣']
            weekdayTime = await client.send_message(client.get_channel('553493689880543242'), msg)
            for choice in reactions:
                await client.add_reaction(weekdayTime, choice)

            # send something in between these so it's not so jumbled together
            #msg = "**-~-~-~-~-~-~-~-~-~-**\n**-~-~-~-~-~-~-~-~-~-**"
            #await client.send_message(client.get_channel('553420403033505792'), msg)

            msg = "**Choose __Weekend__ Schedule**:\n"
            msg += "🇦  Friday\n"
            msg += "🇧  Saturday\n"

            reactions = ['🇦', '🇧']

            weekend = await client.send_message(client.get_channel('553493689880543242'), msg)
            for choice in reactions:
                await client.add_reaction(weekend, choice)

            msg = "`What Weekend Time? (P.M. EST)`"
            reactions = ['2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']
            weekendTime = await client.send_message(client.get_channel('553493689880543242'), msg)
            for choice in reactions:
                await client.add_reaction(weekendTime, choice)


        else:
            print("Not time yet..")
            time = 60 # check every minute

        await asyncio.sleep(time)



async def my_background_task():
    await client.wait_until_ready()
    channel = discord.Object(id='channel_id_here')
    while not client.is_closed:
        print("Hello, world!")
        #await client.send_message(channel, counter)
        await asyncio.sleep(5) # task runs every 5 seconds


@client.event
async def on_message(message):
    #await client.change_presence(game=discord.Game(name="I'm being updated!"))
    await client.change_presence(game=discord.Game(name="5 Fire C.E.O."))
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
            wipeSplits()
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

    elif message.content.startswith('!swap'):
        msg = ""
        cmd = message.content.split()
        if len(cmd) is not 3:
            msg = "**Failed**: Must give 2 arg. Example: `!swap Runnable Static`"
        elif not splits:
            msg = "**Failed**: The queue hasn't been split yet fam."
        else:
            msg = swapGroups(cmd[1], cmd[2])

        await client.send_message(message.channel, msg)

    elif message.content.startswith('!help'):
        msg = "**Welcome to RunBot by  <@!285861225491857408>**\n\n"

        msg += "𝟏)\tUse `!add` in #run-queue to register for the CEO each run.\n"
        msg += "𝟐)\tIf more than 8 people sign up, `!split` will auto organize groups so everyone gets the highest possible amount of fires.\n"
        msg += "\n__**COMMANDS**__\n\n"

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
        #msg += "__NOTE__: To prevent trolling, you can only remove people you personally added to the queue.\n"
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

        # !swap
        msg += "`!swap`\n"
        msg += "Use this to swap two people between two groups.\n"
        msg += "```Usage:\t  !swap [Name1] [Name2]\n"
        msg += "Example:\t!swap Runnable Static```\n"
        msg += "__NOTE__: To prevent unbalancing groups, for now, you can only swap people around who are the same level.\n\n\n"

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

client.loop.create_task(schedulePoll())
client.run(TOKEN)
