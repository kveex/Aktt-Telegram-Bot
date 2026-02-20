from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters

from src.api_communicator import ApiCommunicator
from src.utils.schedule import SubGroup, ButtonVariants, ScheduleGroup
from src.utils import default_keyboard

GROUP, TEACHER, SUBGROUP = range(3)

api = ApiCommunicator()


async def ask_group(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Напиши название группы:")
    return GROUP

async def ask_teacher(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Напишите имя преподавателя по примеру (Дианов В.П.)")
    return TEACHER

async def ask_sub_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group_name: str = update.message.text.lower()

    groups_list: list[str] = await api.get_groups_list()

    if group_name not in groups_list:
        await update.message.reply_text("Этой группы нет в списке, попробуйте ещё раз:\nИспользуйте /cancel чтобы отменить")
        return GROUP

    context.user_data["GROUP"] = group_name

    keyboard: list[list[str]] = [
        [SubGroup.FIRST.display_name, SubGroup.SECOND.display_name],
        [SubGroup.BOTH.display_name]
    ]

    reply_markup: ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(text="Выберите подгруппу ниже:", reply_markup=reply_markup)

    return SUBGROUP

async def received_group_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group_name: str = context.user_data["GROUP"]
    sub_group: SubGroup = SubGroup.from_display_name(update.message.text)

    group_schedule: ScheduleGroup = await api.get_student_schedule(group_name)

    markup: ReplyKeyboardMarkup = await default_keyboard(update)
    await update.message.reply_text(group_schedule.get_sub_group(sub_group).pretty_schedule, reply_markup=markup)

    context.user_data.clear()

    return ConversationHandler.END

async def received_teacher_info(update: Update, _: ContextTypes.DEFAULT_TYPE) -> int:
    teachers_list: list[str] = await api.get_teachers_list()
    teacher_name: str = update.message.text

    if teacher_name is None:
        return TEACHER

    if teacher_name not in teachers_list:
        await update.message.reply_text(f"Этого преподавателя нет в списке, попробуйте ещё раз:\nИспользуйте /cancel чтобы отменить")
        return TEACHER

    teacher_schedule: ScheduleGroup = await api.get_teacher_schedule(teacher_name)

    markup: ReplyKeyboardMarkup = await default_keyboard(update)

    await update.message.reply_text(teacher_schedule.pretty_schedule, reply_markup=markup)

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    markup: ReplyKeyboardMarkup = await default_keyboard(update)

    await update.message.reply_text("Отменено.", reply_markup=markup)
    context.user_data.clear()
    return ConversationHandler.END

def schedule_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters=filters.Text([ButtonVariants.GROUP_SCHEDULE]), callback=ask_group),
            MessageHandler(filters=filters.Text([ButtonVariants.TEACHER_SCHEDULE]), callback=ask_teacher)
        ],
        states={
            GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_sub_group)],
            TEACHER: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_teacher_info)],
            SUBGROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_group_info)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )