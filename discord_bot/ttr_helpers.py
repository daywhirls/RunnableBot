def verifyRole(role):
    roles = ["The Chief Cheese", "Cheese Executive Officer", "Aged Gouda"]
    return role in roles


def convertSuitValue(level):
    return int(level) + 28


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


def calculateFires(avgFireVal):
    x = int(avgFireVal)
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
