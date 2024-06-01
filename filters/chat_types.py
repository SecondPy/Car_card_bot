from aiogram.filters import Filter
from aiogram import Bot, types
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_admin_query import get_admins_ids


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return True
    
class IsAdmin(Filter):
    def __init__(self) -> None:
        pass
    async def __call__(self, message: types.Message, bot: Bot, session: AsyncSession) -> bool:
        return message.from_user.id in await get_admins_ids(session)