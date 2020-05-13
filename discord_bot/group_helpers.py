from math import ceil
from copy import copy
from re import compile

from ttr_helpers import calculateFires, convertSuitValue, getCountFires

GROUP_SIZE = 8


def howManyGroups(queue):
    num = len(queue)
    return ceil(num / GROUP_SIZE)


def populateSplits(numGroups, splits):
    # splits = [[] for i in range(numGroups)]
    for i in range(numGroups):
        splits.append([])


def balanceGroups(numGroups, queue, splits, fireNums):
    tempList = copy(queue)
    # splits = [[] for i in range(numGroups)]
    populateSplits(numGroups, splits)
    # fireNums = []

    # sort queue and evenly distribute them across numGroups amount of groups
    # tempList.sort()
    tempList.sort(key=lambda x: x[1], reverse=True)

    # distribute members to the teams
    splitList = 0  # increment this to drop into each; reset to 0 if = len(splits)
    for i in tempList:
        splits[splitList].append(i)
        splitList += 1
        if splitList is len(splits):
            splitList = 0

    # calculate fires for each group
    for i in range(len(splits)):
        fireNums.append(getCountFires(splits[i]))

    # format message with groups to send to Discord
    msg = ""
    for i in range(len(splits)):
        tempMsg = ""
        # form msg string for one group, append it to final msg each time
        tempMsg = "__Group " + str(i + 1) + "__\t**" + str(fireNums[i]) + " Fires**\n"
        for j in splits[i]:
            tempMsg += j[0] + "\n"
        msg += tempMsg + "\n\n"

    return msg


def calculateWeeklySchedule(results):
    # using these to easily format final message by index of emoji reaction
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday"]
    weektimes = ["6", "7", "8", "9"]
    weekends = ["Friday", "Saturday"]
    weekendtimes = ["2", "3", "4", "5", "6", "7", "8", "9", "10"]

    weekendTime = results[0]
    weekend = results[1]
    weekTime = results[2]
    weekday = results[3]

    weekdayVotes = []
    weekTimeVotes = []
    weekendVotes = []
    weekendTimeVotes = []

    # grab the list of reactions from each message, calculate which ones win
    for reaction in weekday.reactions:
        weekdayVotes.append(reaction.count)

    for reaction in weekTime.reactions:
        weekTimeVotes.append(reaction.count)

    for reaction in weekend.reactions:
        weekendVotes.append(reaction.count)

    for reaction in weekendTime.reactions:
        weekendTimeVotes.append(reaction.count)

    msg = "This week's CEO Schedule:\n```"
    msg += weekdays[weekdayVotes.index(max(weekdayVotes))] + " at "
    msg += weektimes[weekTimeVotes.index(max(weekTimeVotes))] + ":00 PM EST\n"
    msg += weekends[weekendVotes.index(max(weekendVotes))] + " at "
    msg += weekendtimes[weekendTimeVotes.index(max(weekendTimeVotes))] + ":00 PM EST```"

    return msg

"""
Checks the poll results message in the server and returns  better-formatted time strings.
The times returned are one hour before the run, so RunBot can ping everyone a heads-up.
"""
def getRunAlertTimes(results):
    # I only care about what's in between ``1
    delimiter = compile('```[^```]*```')
    times = ''.join(delimiter.findall(results)).strip('```').split('\n')

    runTimes = []
    for run in times:
        args = run.split(' ')

        # Get the hour and zero-pad if necessary.
        # pingServerForRun uses ("%A %I") strftime format (ex: Friday 09)
        day = args[0]
        hour = args[2].split(':')[0]
        hour = str(int(hour) - 1) # We want to alert an hour before the run

        hour = str(int(hour) + 12) # All runs are after noon, so just add on
        # +12 for easy handling, since the server msg format is only 1-12.

        runTimes.append((day + " " + hour))

    return runTimes

def swapGroups(personOne, personTwo, splits, fireNums):
    personOneLocation = -1
    personTwoLocation = -1
    personOneLevel = -1
    personTwoLevel = -1

    # loop through every split group checking for both names given
    for i in range(len(splits)):
        for j in splits[i]:
            # j[0] is the names
            if j[0] == personOne:
                personOneLocation = i  # splits[i] is the group
                personOneLevel = j[1]
            elif j[0] == personTwo:
                personTwoLocation = i
                personTwoLevel = j[1]

    if personOneLocation is -1 or personTwoLocation is -1:
        msg = "**Failed**: One or neither people exist. Try again fam."

    elif personOneLocation == personTwoLocation:
        msg = "Uh.. These people are in the same group already fam. Wyd????"

    # UPDATE: Decided to (temporarily?) remove this check. High enough suits.
    # only let people swap identical lvls to prevent unfair splits
    #elif personOneLevel is not personTwoLevel:
    #    msg = "**Failed**. If this swap happens, one group will have lower fires than desired. You can only swap people that are the same level for now!"

    else:  # we gucci fam. Let's swap them bois
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
        for i in range(
            len(splits)
        ):  # TODO: Put this into printSplits(), not pasted twice
            tempMsg = ""
            # form msg string for one group, append it to final msg each time
            tempMsg = (
                "__Group " + str(i + 1) + "__\t**" + str(fireNums[i]) + " Fires**\n"
            )
            for j in splits[i]:
                tempMsg += j[0] + "\n"
            msg += tempMsg + "\n"

        return msg

    return msg
