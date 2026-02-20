from dotenv import load_dotenv
import os

from src.api_communicator import ApiCommunicator
from src.bot import AkttBot
from src.database import Database


def main() -> None:
    load_dotenv()
    token: str = os.getenv("TG_BOT", None)

    bot = AkttBot(token)
    bot.start_bot()


if __name__ == "__main__":
    main()
