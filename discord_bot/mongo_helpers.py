from bson.json_util import dumps
import pymongo

# updates TTRClient queue[] with mongoDB queue
def getQueue():
    pass

# appends one entry to mongoDB queue
def addToQueue(db, entry):
    # entry = {"Name": "Runnable", "Level": 50}

    try:
        collection = db['queue']
        collection.insert_one(entry)
    except pymongo.errors.DuplicateKeyError:
        # this should never happen, because I check toonExists before this
        return -1

def toonExists(db, entry):
    collection = db['queue']
    return True if collection.find_one({"_id": entry}) is not None else False
