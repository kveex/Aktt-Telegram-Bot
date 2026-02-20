from telegram.ext import Application, ContextTypes

from src.api_communicator import ApiCommunicator
from src.database import Database, ScheduleSubscription
from src.utils.schedule import ScheduleGroup


async def send_schedule_message(context: ContextTypes.DEFAULT_TYPE):
    api = ApiCommunicator()
    database = Database()

    changed: bool = await api.check_changed()

    if not changed:
        return

    subscriptions: list[ScheduleSubscription] = await database.get_all_schedule_subscriptions()

    for subscription in subscriptions:
        if subscription.group_name:
            group_schedule: ScheduleGroup = await api.get_student_schedule(subscription.group_name)
            await context.bot.send_message(chat_id=subscription.chat_id, text=group_schedule.pretty_schedule)

        if subscription.teacher_name:
            teacher_schedule: ScheduleGroup = await api.get_teacher_schedule(subscription.teacher_name)
            await context.bot.send_message(chat_id=subscription.chat_id, text=teacher_schedule.pretty_schedule)


async def start_schedule_check(app: Application, minutes: int = 30):
    if minutes <= 0:
        raise AttributeError("Неправильно указан промежуток между проверками!")

    if app.job_queue is not None:
        app.job_queue.run_repeating(
            callback=send_schedule_message,
            interval=minutes * 60,
            first=10,
            name="schedule_check"
        )