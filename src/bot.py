from telegram import Update
from telegram.ext import Application, ApplicationBuilder

from src.handlers.schedule_anounce import start_schedule_check
from src.handlers.start import start_handler
from src.handlers.inline import inline_query_handler
from src.logger_config import logger
from src.handlers.schedule_conversation import schedule_conversation_handler
from src.handlers.schedule_subscription import schedule_subscription_handler

class AkttBot:
    def __init__(self, token: str) -> None:
        self._application: Application = (ApplicationBuilder().token(token)
                                          .post_init(start_schedule_check)
                                          .build())

    def start_bot(self) -> None:
        handlers: list = [
            start_handler(),
            inline_query_handler(),
            schedule_conversation_handler(),
            schedule_subscription_handler(),
        ]

        self._application.add_handlers(handlers)
        self._application.run_polling(allowed_updates=Update.ALL_TYPES)
        logger.info("Bot started.")