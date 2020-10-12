from bson.json_util import dumps
import pymongo


# appends one entry to mongoDB queue
def addToQueue(db, entry):
    try:
        db['queue'].insert_one(entry)
    except pymongo.errors.DuplicateKeyError:
        # this should never happen, because I check toonExists before this
        return -1


def removeFromQueue(db, entry):
    db['queue'].delete_one({'_id': entry})


def toonExistsInDB(db, entry):
    return True if db['queue'].find_one({"_id": entry}) is not None else False


def isDatabaseEmpty(db):
    return db['queue'].count() == 0


def getQueueAsList(db):
    doc = list(db['queue'].find({})) # returns list of dictionaries
    queue = []
    for entry in doc:
        queue.append((
            entry['_id'],
            entry['level'],
            entry['sender']))
    return queue

def wipeDB(db):
    db['queue'].drop()

def logWeeklySchedule(db, schedule):
    print(schedule)
    db['schedule'].drop()
    db['schedule'].insert_one(schedule[0])
    db['schedule'].insert_one(schedule[1])

def getRunTimes(db):

    times = []
    times.append(db['schedule'].find_one({"_id": 'weekday'})['time'])
    times.append(db['schedule'].find_one({"_id": 'weekend'})['time'])

    runTimes = []
    for args in times:
        args = args.split(' ')
        # Get the hour and zero-pad if necessary.
        # pingServerForRun uses ("%A %I") strftime format (ex: Friday 09)
        day = args[0]
        hour = args[1].split(':')[0]
        hour = str(int(hour) - 1)  # We want to alert an hour before the run
        hour = str(int(hour) + 12)  # All runs are after noon, so just add on
        # +12 for easy handling, since the server msg format is only 1-12.

        runTimes.append((day + " " + hour))

    return runTimes