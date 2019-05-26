from bson.json_util import dumps
import pymongo

# TODO: refactor this so I don't have to pass mongoClient[dbName] to every
# function


# TODO: grabs every document from collection in JSON/dict format,
#       returns msg formatted nicely to display on Discord
def printQueue():
    pass


# appends one entry to mongoDB queue
def addToQueue(db, entry):
    try:
        db['queue'].insert_one(entry)
    except pymongo.errors.DuplicateKeyError:
        # this should never happen, because I check toonExists before this
        return -1


def toonExistsInDB(db, entry):
    return True if db['queue'].find_one({"_id": entry}) is not None else False


def wipeDB(db):
    db['queue'].drop()
