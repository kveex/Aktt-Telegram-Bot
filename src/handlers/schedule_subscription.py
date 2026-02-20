from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, filters, MessageHandler, CommandHandler

from src.api_communicator import ApiCommunicator
from src.database import Database, AlreadyExistingSubscriptionError, SubscriptionLimitError
from src.utils import default_keyboard
from src.utils.schedule import SubGroup, ButtonVariants

SUB, GROUP, TEACHER, SUBGROUP, UNSUB = range(5)

api = ApiCommunicator()
database = Database()

async def unsubscribe(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id: int = update.effective_chat.id

    subscriptions, _ = await database.get_schedule_subscriptions(chat_id)

    if not subscriptions:
        return ConversationHandler.END

    keyboard: list[list[str]] = []

    i: int = 1

    for subscription in subscriptions:
        text = f"{i}. "
        text += f"Преподаватель: {subscription.teacher_name} " if subscription.teacher_name else f"Группа: {subscription.group_name.upper()} "
        text += f"Подгруппа: {subscription.sub_group.display_name}\n" if subscription.group_name else ""

        keyboard.append([text])
        i += 1

    keyboard.append(["Отмена"])

    markup: ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text("Нажми на подписку, которую нужно удалить:", reply_markup=markup)

    return UNSUB

async def unsub_number_received(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    received_number_string: str = update.message.text.replace(".", "")
    chat_id: int = update.effective_chat.id

    if received_number_string.lower() == "отмена":
        return await cancel(update, _)

    try:
        received_number: int = int(received_number_string.split(" ")[0]) - 1
    except ValueError:
        await update.message.reply_text("Что-то неправильно введено, нужно написать имеено число, например 2, "
                                        "попробуй снова\nИспользуй /cancel чтобы отменить")
        return UNSUB

    subscriptions, _ = await database.get_schedule_subscriptions(chat_id)

    subscription_id = subscriptions[received_number].id

    deleted: bool = await database.remove_subscription(subscription_id)

    markup: ReplyKeyboardMarkup = await default_keyboard(update)

    if not deleted:
        await update.message.reply_text(
            "Что-то пошло не так во время создания подписки, программисту опять что-то чинить :D", reply_markup=markup
        )
        return ConversationHandler.END

    await update.message.reply_text("Подписка удалена!", reply_markup=markup)

    return ConversationHandler.END

async def subscribe(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Напиши название группы или имя преподавателя по примеру (Дианов В.П.)")
    return SUB


async def name_received(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    name: str = update.message.text

    groups_list: list[str] = await api.get_groups_list()
    teachers_list: list[str] = await api.get_teachers_list()

    if name.lower() in groups_list:
        return await ask_sub_group(update, _)
    elif name in teachers_list:
        return await received_teacher_info(update, _)
    else:
        await update.message.reply_text("Указанная группа или преподаватель не найдены :/")
        return ConversationHandler.END


async def ask_sub_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group_name: str = update.message.text.lower()

    groups_list: list[str] = await api.get_groups_list()

    if group_name not in groups_list:
        await update.message.reply_text(
            "Этой группы нет в списке, попробуй ещё раз:\nИспользуй /cancel чтобы отменить")
        return GROUP

    context.user_data["GROUP"] = group_name

    keyboard: list[list[str]] = [
        [SubGroup.FIRST.display_name, SubGroup.SECOND.display_name],
        [SubGroup.BOTH.display_name]
    ]

    reply_markup: ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(text="Выбери подгруппу ниже:", reply_markup=reply_markup)

    return SUBGROUP


async def received_group_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group_name: str = context.user_data["GROUP"]
    sub_group: SubGroup = SubGroup.from_display_name(update.message.text)

    context.user_data.clear()

    markup: ReplyKeyboardMarkup = await default_keyboard(update)

    try:
        created: bool = await database.make_subscription(update.effective_chat.id, group_name, None, sub_group)
    except (AlreadyExistingSubscriptionError, SubscriptionLimitError) as e:
        await update.message.reply_text(str(e), reply_markup=markup)
        return ConversationHandler.END


    if not created:
        await update.message.reply_text(
            "Что-то пошло не так во время создания подписки, программисту опять что-то чинить :D", reply_markup=markup
        )
        return ConversationHandler.END

    markup: ReplyKeyboardMarkup = await default_keyboard(update)

    await update.message.reply_text(f"Подписка на расписание группы {group_name} оформлена успешно!",
                                    reply_markup=markup)

    return ConversationHandler.END


async def received_teacher_info(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    teacher_name: str = update.message.text

    markup: ReplyKeyboardMarkup = await default_keyboard(update)

    try:
        created: bool = await database.make_subscription(update.effective_chat.id, None, teacher_name)
    except (AlreadyExistingSubscriptionError, SubscriptionLimitError) as e:
        await update.message.reply_text(str(e), reply_markup=markup)
        return ConversationHandler.END

    if not created:
        await update.message.reply_text(
            "Что-то пошло не так во время создания подписки, программисту опять что-то чинить :D", reply_markup=markup
        )
        return ConversationHandler.END

    markup: ReplyKeyboardMarkup = await default_keyboard(update)

    await update.message.reply_text(f"Подписка на расписание преподавателя {teacher_name} оформлена успешно!",
                                    reply_markup=markup)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    markup: ReplyKeyboardMarkup = await default_keyboard(update)

    await update.message.reply_text("Работа с подписками отменена.", reply_markup=markup)
    context.user_data.clear()
    return ConversationHandler.END


def schedule_subscription_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters=filters.Text([ButtonVariants.SUBSCRIBE]), callback=subscribe),
            MessageHandler(filters=filters.Text([ButtonVariants.UNSUBSCRIBE]), callback=unsubscribe),
        ],
        states={
            SUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_received)],
            UNSUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, unsub_number_received)],
            GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sub_group)],
            TEACHER: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_teacher_info)],
            SUBGROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_group_info)],
        },
        fallbacks=[
            CommandHandler('cancel', cancel)
        ]
    )
