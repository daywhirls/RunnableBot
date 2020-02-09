from ttr_client import TTRClient
from ttr_token import TOKEN
import logging

logging.basicConfig(level=logging.INFO)

"""
Grab the Discord auth token, start our logger, and launch the epic RunBot 
"""
if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("Initializing TTR Bot")
    client = TTRClient(TOKEN)
    logger.info("Starting TTR Client")
    client.run()
