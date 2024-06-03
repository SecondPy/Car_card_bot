from datetime import date, datetime, timedelta
import random

from aiogram import Bot, F, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
#from database.models import Student
#from database.orm_admin_query import orm_add_product
from const_values import ABBREVIATED_WEEK_DAYS, ADMIN_GREETINGS
from sqlalchemy.ext.asyncio import AsyncSession


from database import orm_admin_query as admin_orm

from kbds.callback import get_callback_btns



async def get_main_admin_menu(session: AsyncSession, state: FSMContext, bot: Bot, message: types.Message, trigger, text='', today=date.today()) -> None:
    calendar_data = {}
    current_date = today - timedelta(days=(today.weekday()))
    last_date = current_date + timedelta(days=28)
    text += '⬇️ Актуальное расписание'

    for _ in range(7):
        calendar_data[f'{ABBREVIATED_WEEK_DAYS[_]}'] = f"|{ABBREVIATED_WEEK_DAYS[_]}|"
    while current_date < last_date:
        if current_date < date.today() or current_date > (date.today()+timedelta(days=28)):
            calendar_data[f"get_day {current_date.strftime('%Y-%m-%d')}"] = f"{current_date.strftime('%d.%m')}"
        else:
            orders_data = await admin_orm.orm_get_order_with_date(session, current_date)
            if orders_data and 'Выходной' not in {order.description for order in orders_data}:
                hours = 0
                for order in orders_data:
                    hours += (order.ends - order.begins).total_seconds() // 3600
                if hours < 4: inline_smile = '🟢'
                elif hours < 9: inline_smile = '🟡'
                elif hours < 17: inline_smile = '🟠'
                else: inline_smile = '🔴'
                text_button = f"{current_date.strftime('%d')}{inline_smile}"
            elif orders_data and 'Выходной' in {order.description for order in orders_data}:
                text_button = f"{current_date.strftime('%d')}🥳"
            else: text_button = f"{current_date.strftime('%d')}🟢"
            calendar_data[f"get_day {current_date.strftime('%Y-%m-%d')}"] = text_button
        current_date += timedelta(days=1)
    calendar_data[f"flip_month {today} back"] = f'⏪ назад'
    if today != date.today(): calendar_data[f"main_admin_menu"] = f'⏺'
    calendar_data[f"flip_month {today} next"] = f'вперед ⏩'
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
    
    try: await state.clear()
    except: pass