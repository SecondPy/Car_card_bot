from datetime import date, datetime, time, timedelta
import random
from aiogram import Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
#from database.models import Student
#from database.orm_admin_query import orm_add_product
from const_values import ABBREVIATED_WEEK_DAYS, ABBREVIATED_WEEK_DAYS_BTNS, ADMIN_GREETINGS
from sqlalchemy.ext.asyncio import AsyncSession


from database import orm_admin_query as admin_orm

from kbds.callback import get_callback_btns
from utils.datetime_formatter import DateFormatter


async def get_main_admin_menu(session: AsyncSession, state: FSMContext, bot: Bot, message: types.Message, trigger, text='', date_start=date.today()) -> None:
    try: 
        if state.get_data(): await state.clear()
    except: pass
    calendar_data = ABBREVIATED_WEEK_DAYS_BTNS.copy()
    current_date = date_start - timedelta(days=(date_start.weekday()))
    last_date = current_date + timedelta(days=28)
    today = date.today()
    actual_days = today + timedelta(days=28)
    current_hour = datetime.now().hour
    month_orders_data = await admin_orm.get_month_orders(session, current_date)
    orders_data = await admin_orm.orm_get_order_with_date(session, datetime.combine(today, time(0, 0)))
    if orders_data:
        text += '🗓 Наряды на сегодня:\n-'
        text += '\n-'.join([(f"<b>{DateFormatter(order.begins).message_format[-5:]}</b> {order.description}") for order in orders_data])
    else: text += '🗓 Наряды на сегодня отсутствуют\n'
    
    text += '\n⬇️ Актуальное расписание'

    while current_date < last_date:
        if not today <= current_date < actual_days:
            calendar_data[f"get_day {current_date.strftime('%Y-%m-%d')}"] = f"{current_date.strftime('%d.%m')}"
        else:
            text_button = f"{current_date.strftime('%d')}"
            if day_orders_data := [order for order in month_orders_data if order.begins.date()==current_date]:
                if 'Выходной' in {order.description for order in day_orders_data}: text_button += '🥳'
                else:
                    hours = 0
                    if current_date == today and current_hour >= 9: hours = (current_hour - 9) * 2
                    hours += sum([(order.ends - order.begins).total_seconds() for order in day_orders_data]) // 3600
                    
                    inline_smile = (
                        '🟢' if hours < 4 else
                        '🟡' if hours < 9 else
                        '🟠' if hours < 17 else
                        '🔴'
                    )
                    text_button += inline_smile
            else: text_button += '🟢'

            calendar_data[f"get_day {current_date.strftime('%Y-%m-%d')}"] = text_button
        current_date += timedelta(days=1)
    
    calendar_data[f"flip_month {date_start} back"] = f'⏪ назад'
    if date_start != today: calendar_data[f"main_admin_menu"] = f'⏺'
    calendar_data[f"flip_month {date_start} next"] = f'вперед ⏩'

    if trigger == 'cancel':
        main_admin_kb = await message.answer(text=f'Все сброшено 👌\n\n{text}', reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]), parse_mode=ParseMode.HTML)
        bot.main_admin_menu_ids[message.from_user.id] = main_admin_kb.message_id
        await admin_orm.orm_add_inline_message_id(session, message.from_user.id, bot.main_admin_menu_ids[message.from_user.id])
    else:
        try:
            await message.edit_text(inline_message_id=bot.main_admin_menu_ids[message.from_user.id], text=text, parse_mode=ParseMode.HTML)
            await message.edit_reply_markup(inline_message_id=bot.main_admin_menu_ids[message.from_user.id], reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]), parse_mode=ParseMode.HTML)
        except Exception as e: # На случай если сообщение не может быть отредактировано
            try:
                bot.main_admin_menu_ids[message.from_user.id] = await admin_orm.get_inline_message_id(session, message.from_user.id)
                await message.edit_text(inline_message_id=bot.main_admin_menu_ids[message.from_user.id], text=text, parse_mode=ParseMode.HTML)
                await message.edit_reply_markup(inline_message_id=bot.main_admin_menu_ids[message.from_user.id], reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]), parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f'oshibka>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<>>>>>>>>>>>> {e}')
                text = f'{random.choice(ADMIN_GREETINGS)}\n\n{text}' if message.from_user.id == 2136465129 else text
                main_admin_kb = await message.answer(text=text, reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]), parse_mode=ParseMode.HTML)
                bot.main_admin_menu_ids[message.from_user.id] = main_admin_kb.message_id
                await admin_orm.orm_add_inline_message_id(session, message.from_user.id, bot.main_admin_menu_ids[message.from_user.id])

    

    
    