from telegram import Update, ReplyKeyboardMarkup

from src.database import Database, MAX_SUBSCRIPTION_COUNT
from src.utils.schedule import ButtonVariants


async def default_keyboard(update: Update) -> ReplyKeyboardMarkup:
    database = Database()
    chat_id = update.effective_chat.id
    subscription, count = await database.get_schedule_subscriptions(chat_id)

    keyboard: list[list[str]] = [
        [ButtonVariants.GROUP_SCHEDULE],
        [ButtonVariants.TEACHER_SCHEDULE]
    ]

    if count < MAX_SUBSCRIPTION_COUNT:
        keyboard.append([ButtonVariants.SUBSCRIBE])

    if subscription:
        keyboard.append([ButtonVariants.UNSUBSCRIBE])

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
