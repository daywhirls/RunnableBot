"""
    Checks the user's role to verify whether they are trustworthy enough to
    wipe the queue
"""
def verifyRole(author):
    acceptedRoles = ["Aged Gouda", "Cheese Executives", "Cheese Graters", "Holey Swiss", "GOAT Cheese", "staff", "Cheese++", "Chief Cheeses"]
    for name in author.roles:
        if name.name in acceptedRoles:
            return True
    return False

"""
The 'Fire Value' is the BC level + 28.
Ex: BC 50 fire value is 78.
"""
def convertSuitValue(level):
    return int(level) + 28

"""
Iterates through the specified group of toons and determines how many fires
that group will receive based on all their suit levels
"""
def getCountFires(group):
    queueSize = 0
    totalValue = 0
    fires = 0
    avgFireVal = 0

    for i in group:
        queueSize += 1
        totalValue += convertSuitValue(i[1])
    avgFireVal = totalValue / queueSize
    fires = calculateFires(avgFireVal)
    return fires

"""
Takes the 'Value' associated with the cheese levels in the group and returns
the amount of fires.

Ex: If everyone in the group averages to be BC 35, the avg value is 63 (5 fires)
"""
def calculateFires(avgFireVal):
    x = int(avgFireVal)
    if x < 17:
        return 2
    elif x < 33:
        return 3
    elif x < 48:
        return 4
    elif x < 63:
        return 5
    else:
        return 6
