from datetime import datetime
from typing import Optional
from httpx import AsyncClient, Response
from src.utils.schedule import ScheduleGroup, build_schedule_group, SubGroup


class ApiCommunicator:
    instance = None
    _address: str
    _port: int
    _http_client: AsyncClient
    _last_edit_datetime: Optional[datetime]

    def __new__(cls, address: str = "http://localhost", port: int = 16311):
        if not cls.instance:
            cls.instance = object.__new__(cls)
            cls._address: str = address
            cls._port: int = port
            cls._http_client: AsyncClient = AsyncClient()
            cls._last_edit_datetime: Optional[datetime] = None

        return cls.instance

    async def get_groups_list(self) -> list[str]:
        response: Response = await self._http_client.get(f"{self._address}:{self._port}/api/schedule/groups")
        response.raise_for_status()

        data: dict = response.json()
        return data.get("groupsList")

    async def get_teachers_list(self) -> list[str]:
        response: Response = await self._http_client.get(f"{self._address}:{self._port}/api/schedule/teachers")
        response.raise_for_status()

        data: dict = response.json()
        return data.get("teachersList")

    # region Student schedule creation
    async def _get_student_schedule_info(self, group_name: str) -> dict:
        response: Response = await self._http_client.get(f"{self._address}:{self._port}/api/schedule/student/{group_name}/")
        response.raise_for_status()

        return response.json()

    async def get_student_schedule(self, group_name: str) -> ScheduleGroup:
        schedule_info: dict = await self._get_student_schedule_info(group_name)

        return await build_schedule_group(schedule_info)
    # endregion

    # region Teacher schedule creation
    async def _get_teacher_schedule_info(self, teacher_name: str) -> Optional[dict]:
        response: Response = await self._http_client.get(f"{self._address}:{self._port}/api/schedule/teacher/{teacher_name}")
        response.raise_for_status()

        return response.json()


    async def get_teacher_schedule(self, teacher_name: str) -> Optional[ScheduleGroup]:
        schedule_info: dict = await self._get_teacher_schedule_info(teacher_name)

        return await build_schedule_group(schedule_info)

    # endregion

    async def _get_schedule_date(self) -> datetime:
        response: Response = await self._http_client.get(
            f"{self._address}:{self._port}/api/schedule/date"
        )
        data: dict = response.json()
        schedule_date_str: str = data.get("scheduleDate", "")
        schedule_date: datetime = datetime.strptime(schedule_date_str, "%Y-%m-%d")
        return schedule_date

    async def check_changed(self) -> bool:
        new_date: datetime = await self._get_schedule_date()

        if self._last_edit_datetime is None:
            self._last_edit_datetime = new_date
            return False

        changed: bool = new_date > self._last_edit_datetime
        self._last_edit_datetime = new_date
        return changed