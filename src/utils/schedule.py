from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

class ButtonVariants(StrEnum):
    GROUP_SCHEDULE = "Расписание для группы"
    TEACHER_SCHEDULE = "Расписание для преподавателя"
    SUBSCRIBE = "Подписка на расписание"
    UNSUBSCRIBE = "Отписка от расписания"

class ScheduleStates(StrEnum):
    OK = "OK"
    DISTANT = "DISTANT"
    EMPTY = "EMPTY"

class SubGroup(StrEnum):
    FIRST = "FIRST"
    SECOND = "SECOND"
    BOTH = "BOTH"

    @property
    def display_name(self) -> str:
        names = {
            SubGroup.FIRST: "Первая",
            SubGroup.SECOND: "Вторая",
            SubGroup.BOTH: "Обе"
        }
        return names.get(self, "Неизвестно")

    @classmethod
    def from_display_name(cls, display_name: str) -> "SubGroup":
        names = {
            "Первая": "FIRST",
            "Вторая": "SECOND",
            "Обе": "BOTH"
        }
        return cls(names.get(display_name, display_name))

    @property
    def to_int(self):
        values = {
            SubGroup.FIRST: 1,
            SubGroup.SECOND: 2,
            SubGroup.BOTH: 0
        }
        return values[self]


@dataclass(frozen=True, order=True)
class ScheduleItem:
    time: str
    subject_name: str
    group_name: str
    teacher_name: str
    room_number: str
    sub_group: SubGroup
    state: ScheduleStates

@dataclass(frozen=True, order=True)
class ScheduleGroup:
    schedule_date: str
    group_name: str
    teacher_name: str
    schedule_items: list[ScheduleItem]

    @property
    def _schedule_date_obj(self) -> datetime:
        return datetime.strptime(self.schedule_date, "%Y-%m-%d")

    @property
    def pretty_schedule(self) -> str:
        months: list[str] = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]

        time = self._schedule_date_obj
        text = f"Расписание на {time.day} {months[time.month - 1]} {time.year}\n"
        text += f"Для преподавателя: {self.teacher_name}\n\n" if self.teacher_name else ""
        text += f"Для группы: {self.group_name}\n\n" if self.group_name else ""

        for schedule_item in self.schedule_items:
            sub_group: str = schedule_item.sub_group.display_name
            text += f"- {schedule_item.time} | {schedule_item.subject_name}\n"
            text += f"- Кабинет: {schedule_item.room_number}\n"
            text += f"- Преподаватель: {schedule_item.teacher_name}\n" if schedule_item.teacher_name != self.teacher_name else ""
            text += f"- Группа: {schedule_item.group_name}\n" if schedule_item.group_name != self.group_name else ""
            text += f"- Подгруппа: {sub_group}\n" if schedule_item.sub_group != SubGroup.BOTH else ""
            text += "-------------------------------\n"

        if not self.schedule_items:
            text += "Нет расписания"

        return text

    def get_sub_group(self, sub_group: SubGroup) -> "ScheduleGroup":
        new_schedule_items: list[ScheduleItem] = []
        if sub_group == SubGroup.BOTH: return self
        for item in self.schedule_items:
            if item.sub_group == sub_group or item.sub_group == SubGroup.BOTH:
                new_schedule_items.append(item)
        return ScheduleGroup(self.schedule_date, self.group_name, self.teacher_name, new_schedule_items)



async def _build_schedule_item(schedule_item_info: dict) -> ScheduleItem:
    time: str = schedule_item_info.get("time", "")
    subject_name: str = schedule_item_info.get("subjectName", "")
    group_name: str = schedule_item_info.get("groupName", "")
    teacher_name: str = schedule_item_info.get("teacherName", "")
    room_number: str = schedule_item_info.get("roomNumber", "")
    sub_group: SubGroup = SubGroup(schedule_item_info.get("subGroup", ""))
    state: ScheduleStates = ScheduleStates(schedule_item_info.get("state"))

    return ScheduleItem(
        time=time,
        subject_name=subject_name,
        group_name=group_name,
        teacher_name=teacher_name,
        room_number=room_number,
        sub_group=sub_group,
        state=state
    )

async def build_schedule_group(schedule_group_info: dict) -> ScheduleGroup:
    schedule_date: str = schedule_group_info.get("scheduleDate", "")
    group_name: str = schedule_group_info.get("groupName", "Не указана")
    teacher_name: str = schedule_group_info.get("teacherName", "Не указан")
    schedule_items_info: list[dict] = schedule_group_info.get("scheduleItems", [])

    schedule_items: list[ScheduleItem] = []
    for schedule_item_info in schedule_items_info:
        schedule_items.append(await _build_schedule_item(schedule_item_info))

    return ScheduleGroup(
        schedule_date=schedule_date,
        group_name=group_name,
        teacher_name=teacher_name,
        schedule_items=schedule_items
    )
