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
