
from sqlalchemy.ext.asyncio import AsyncSession

from const_values import ABBREVIATED_WEEK_DAYS, ADMIN_GREETING, CLIENT_EMOJI, CLIENT_GREETING
from database import orm_client_query as client_orm
from utils.datetime_formatter import DateFormatter




async def main_menu_client_constructor(session: AsyncSession, tg_id: int) -> list:
    text = f'🛢 Адрес <b>ОйлЦентр</b>: Волжский, пл. Труда, 4а.\n📱 Тел: +78443210102 (9:00-18:00)\n'
    btns_data, sizes = dict(), list()
    btns_data['header withoud_data'] = '⬇️ Выберите действие ⬇️'
    sizes.append(1)
    btns_data['get_client_calendar'] = '🔧 Записаться 🔧'
    btns_data[f'get_client_history {tg_id}'] = '📜 История 📜'
    sizes.append(2)
    actual_orders = await client_orm.find_orders_with_tg_id(session=session, tg_id=tg_id, status='actual')
    if actual_orders:
        for order in actual_orders:
            text += f"\n-👨🏼‍🏭Ждём Вас на обслуживание {DateFormatter(order.begins).message_format}"
    else:
        text += f'\n-👨🏼‍🏭 записей о предстоящем обслуживании не найдено'

    return [text, btns_data, sizes]