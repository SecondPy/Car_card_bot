import asyncio
from datetime import date, datetime, timedelta

from aiogram import Bot, F, types, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
#from database.models import Student
#from database.orm_admin_query import orm_add_product
from const_values import ABBREVIATED_WEEK_DAYS, CLIENT_CALENDAR_HEAD
from sqlalchemy.ext.asyncio import AsyncSession


from database import orm_client_query as client_orm
from database import orm_admin_query as admin_orm

from kbds.callback import get_callback_btns
from utils.client_start_menu import main_menu_client_constructor


async def get_main_client_menu(session: AsyncSession, state: FSMContext, bot: Bot, message: types.Message, trigger) -> None:
    calendar_data = {}
    today = date.today()
    current_date = today - timedelta(days=(today.weekday()))
    last_date = current_date + timedelta(days=28)
    month_orders_data = await admin_orm.get_month_orders(session, current_date)
    current_hour = datetime.now().hour
    text = CLIENT_CALENDAR_HEAD
    for _ in range(7):
        calendar_data[f'{ABBREVIATED_WEEK_DAYS[_]}'] = f"|{ABBREVIATED_WEEK_DAYS[_]}|"
    while current_date < last_date:
        if current_date < today:
            calendar_data[f"get_client_day {current_date.strftime('%Y-%m-%d')}"] = f"{current_date.strftime('%d.%m')}"
            text_button = f"{current_date.strftime('%d')}"
        else:
            day_orders_data = [order for order in month_orders_data if order.begins.date()==current_date]
            text_button = f"{current_date.strftime('%d')}"
            if current_date == today and current_hour >= 9: hours = (current_hour - 9) * 2
            else: hours = 0

            if day_orders_data := [order for order in month_orders_data if order.begins.date()==current_date]:
                if 'Выходной' in {order.description for order in day_orders_data}: text_button += '🥳'
                else:
                    if current_date == today and current_hour >= 9: hours = (current_hour - 9) * 2
                    hours += sum([(order.ends - order.begins).total_seconds() for order in day_orders_data]) // 3600
                
            inline_smile = (
                '🟢' if hours < 4 else
                '🟡' if hours < 9 else
                '🟠' if hours < 16 else
                '🔴'
            )
            text_button += inline_smile
            

            calendar_data[f"get_client_day {current_date.strftime('%Y-%m-%d')}"] = text_button
        current_date += timedelta(days=1)

    calendar_data[f"main_menu_client"] = '🏠 Вернутьсяn m  в главное меню 🏠'
    if trigger == 'cancel':
        main_client_kb = await message.answer(text=f'Все сброшено 👌\n\n{text}', reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]), parse_mode=ParseMode.HTML)
        bot.main_client_menu_ids[message.from_user.id] = main_client_kb.message_id
        await client_orm.add_inline_message_id(session, message.from_user.id, bot.main_client_menu_ids[message.from_user.id])
    else:
        await message.edit_text(text=text, parse_mode=ParseMode.HTML)
        await message.edit_reply_markup(reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]))

    try: await state.clear()
    except: pass

    await asyncio.sleep(60)
    try:
        if bot.client_idle_timer[message.from_user.id] > 59:
            text, btns_data, sizes = await main_menu_client_constructor(session=session, tg_id=message.from_user.id)
            await message.edit_text(text=text, parse_mode=ParseMode.HTML)
            await message.edit_reply_markup(reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
    except Exception as e: await bot.send_message(2136465129, text=f'Ошибка при автовозврате в стартовое меню клиента\n{e}')
        