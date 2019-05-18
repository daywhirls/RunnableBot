from ttr_client import TTRClient
from token import TOKEN
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("Initializing TTR Client")
    client = TTRClient(TOKEN)
    client.loop.add_task(client.schedulePoll())
    logger.info("Starting TTR Client")
    client.run()
