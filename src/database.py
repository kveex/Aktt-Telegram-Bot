import os
from typing import Optional
from enum import StrEnum

from dotenv import load_dotenv
from postgrest import CountMethod

from src.utils.schedule import SubGroup
from dataclasses import dataclass

from supabase import AsyncClient

MAX_SUBSCRIPTION_COUNT = 5

class Tables(StrEnum):
    SCHEDULE_SUBSCRIPTIONS = "schedule_subscriptions"

@dataclass(frozen=True, order=True)
class ScheduleSubscription:
    id: int
    chat_id: int
    group_name: Optional[str]
    teacher_name: Optional[str]
    sub_group: SubGroup

async def _build_schedule_subscription_obj(subscription_info: dict) -> ScheduleSubscription:
    subscription_id: int = subscription_info.get("id")
    chat_id: int = subscription_info.get("chat_id")
    group_name: Optional[str] = subscription_info.get("group_name", None)
    teacher_name: Optional[str] = subscription_info.get("teacher_name", None)
    sub_group: SubGroup = SubGroup(subscription_info.get("sub_group")) or SubGroup.BOTH

    if group_name is None and teacher_name is None:
        raise AttributeError(f"В данных из базы не найдено ни учителя, ни группы!\n{subscription_info}")

    return ScheduleSubscription(
        id=subscription_id,
        chat_id=chat_id,
        group_name=group_name,
        teacher_name=teacher_name,
        sub_group=sub_group
    )


class AlreadyExistingSubscriptionError(Exception):
    pass


class SubscriptionLimitError(Exception):
    pass


class Database:
    instance = None
    _supabase: Optional[AsyncClient] = None

    def __new__(cls):
        if not cls.instance:
            load_dotenv()
            url: str = os.getenv("SB_URL", None)
            key: str = os.getenv("SB_KEY", None)
            cls.instance = super().__new__(cls)
            cls._supabase = AsyncClient(url, key)
        return cls.instance

    async def make_subscription(self, chat_id: int, group_name: Optional[str] = None, teacher_name: Optional[str] = None, sub_group: SubGroup = SubGroup.BOTH):

        subscriptions, count = await self.get_schedule_subscriptions(chat_id)

        if group_name is None and teacher_name is None:
            raise AttributeError("Группа или учитель обязательно должны быть указаны!")

        if count >= MAX_SUBSCRIPTION_COUNT:
            raise SubscriptionLimitError("Нельзя добавить больше 5 подписок!")

        # for subscription in subscriptions:
        #     if subscription.chat_id == chat_id:
        #         if subscription.group_name == group_name or subscription.teacher_name == teacher_name:
        #             if subscription.sub_group == sub_group:
        #                 raise AlreadyExistingSubscriptionError("Подписка на эту группу или преподавателя уже есть!")
        for s in subscriptions:
            if s.chat_id != chat_id:
                continue
            if group_name is not None and s.group_name == group_name and s.sub_group == sub_group:
                raise AlreadyExistingSubscriptionError("Подписка на эту группу уже есть!")
            if teacher_name is not None and s.teacher_name == teacher_name:
                raise AlreadyExistingSubscriptionError("Подписка на этого преподавателя уже есть!")

        json: dict = {
            "chat_id": chat_id,
            "group_name": group_name,
            "teacher_name": teacher_name,
            "sub_group": sub_group
        }

        response = await self._supabase.table(Tables.SCHEDULE_SUBSCRIPTIONS).insert(json=json).execute()

        return True if response.data else False

    async def get_schedule_subscriptions(self, chat_id: int) -> tuple[list[ScheduleSubscription], int]:
        response = await (self._supabase.table(Tables.SCHEDULE_SUBSCRIPTIONS)
                          .select("*", count=CountMethod.exact)
                          .eq("chat_id", chat_id)
                          .order("id")
                          .execute())

        data: list = response.data
        count: int = response.count

        return [await _build_schedule_subscription_obj(info) for info in data], count

    async def get_all_schedule_subscriptions(self) -> list[ScheduleSubscription]:
        response = await self._supabase.table(Tables.SCHEDULE_SUBSCRIPTIONS).select("*").execute()

        data = response.data

        return [await _build_schedule_subscription_obj(info) for info in data]

    async def remove_subscription(self, subscription_id: int) -> bool:
        response = await self._supabase.table(Tables.SCHEDULE_SUBSCRIPTIONS).delete().eq("id", subscription_id).execute()

        return True if response.data else False