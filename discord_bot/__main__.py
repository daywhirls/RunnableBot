from ttr_client import TTRClient
from ttr_token import TOKEN

from mongo_tokens import (
    db,
    dbName
)

from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO)

"""
Grab the Discord auth token, start our logger, and launch the epic RunBot
"""
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("Initializing MongoClient")
    mongoClient = MongoClient(db)
    mongoDB = mongoClient[dbName] # database
    logger.info("Initializing TTR Bot")
    client = TTRClient(TOKEN, mongoDB) # init _token, calls discord.Client init
    logger.info("Starting TTR Client")
    client.run() # calls superclass (discord.Client)'s run function
