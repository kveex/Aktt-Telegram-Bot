from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from src.utils import default_keyboard

async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    user_name: str = update.effective_user.full_name

    markup: ReplyKeyboardMarkup = await default_keyboard(update)

    text: str = (f"Здравствуй, {user_name}!\n\nЭтот бот поможет тебе получить информацию о расписании. Можешь "
                 f"использовать кнопки ниже или оформить подписку на расписание, оно будет приходить автоматически "
                 f"примерно в то же "
                 f"время, как его обновят на сайте.\n\nПрошу учесть, что расписание иногда может быть некорректным, "
                 f"так как формируется из расписания на сайте, которое кишит опечатками :(")

    await update.message.reply_text(
        text=text,
        reply_markup=markup
    )

def start_handler() -> CommandHandler:
    return CommandHandler('start', start)