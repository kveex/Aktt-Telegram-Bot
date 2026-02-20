from uuid import uuid4

from telegram import InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ContextTypes, InlineQueryHandler

from src.api_communicator import ApiCommunicator
from src.utils.schedule import ScheduleGroup, SubGroup


async def inline_query(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Позволяет вызвать бота упоминанием и получить группу с уточнением подгруппы"""

    api = ApiCommunicator()
    query = update.inline_query.query

    groups: list[str] = await api.get_groups_list()
    teachers: list[str] = await api.get_teachers_list()

    in_group: bool = query.lower() in groups
    in_teachers: bool = query in teachers

    if not query:
        return

    if in_group:
        schedule: ScheduleGroup = await api.get_student_schedule(query)

        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Обе подгруппы",
                input_message_content=InputTextMessageContent(
                    schedule.pretty_schedule
                )
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Первая подгруппа",
                input_message_content=InputTextMessageContent(
                    schedule.get_sub_group(SubGroup.FIRST).pretty_schedule
                )
            ),
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Вторая подгруппа",
                input_message_content=InputTextMessageContent
                (schedule.get_sub_group(SubGroup.SECOND).pretty_schedule
                 )
            )
        ]

        await update.inline_query.answer(results)

    elif in_teachers:
        schedule: ScheduleGroup = await api.get_teacher_schedule(query)
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"Расписание для {query}",
                input_message_content=InputTextMessageContent(
                    schedule.pretty_schedule
                )
            )
        ]

        await update.inline_query.answer(results)

def inline_query_handler() -> InlineQueryHandler:
    return InlineQueryHandler(inline_query)