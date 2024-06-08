import asyncio
from datetime import date, datetime, timedelta

from aiogram import Bot, F, types, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
#from database.models import Student
#from database.orm_admin_query import orm_add_product
from const_values import ABBREVIATED_WEEK_DAYS, ADMIN_GREETINGS
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
    text = f'🗓 Выберите удобную дату в этом интерактивном календаре \n📲 Или запишитесь по телефону: +78443210102 (9:00-18:00)\n\n🔴 - день полность расписан\n🟠 - высокая загрузка\n🟡 - средняя загрузка\n🟢 - низкая загрузка\n\n🛢 Адрес <b>ОйлЦентр</b>: Волжский, пл Труда, 4а.\n\n⬇️ Актуальное расписание'
    for _ in range(7):
        calendar_data[f'{ABBREVIATED_WEEK_DAYS[_]}'] = f"|{ABBREVIATED_WEEK_DAYS[_]}|"
    while current_date < last_date:
        if current_date < today:
            calendar_data[f"get_client_day {current_date.strftime('%Y-%m-%d')}"] = f"{current_date.strftime('%d.%m')}"
            text_button = f"{current_date.strftime('%d')}"
        else:
            orders_data = await admin_orm.orm_get_order_with_date(session, current_date)
            if orders_data and 'Выходной' not in {order.description for order in orders_data}:
                if current_date != today or datetime.now().hour < 9: hours = 0
                else: hours = (datetime.now().hour - 9) * 2
                for order in orders_data:
                    hours += (order.ends - order.begins).total_seconds() // 3600
                free_hours = 18 - hours
                if free_hours > 5: inline_smile = '🟢'
                elif free_hours > 2: inline_smile = '🟡'
                elif free_hours > 0: inline_smile = '🟠'
                else: inline_smile = '🔴'
                text_button = f"{current_date.strftime('%d')}{inline_smile}"
            else: text_button = f"{current_date.strftime('%d')}🟢"
        calendar_data[f"get_client_day {current_date.strftime('%Y-%m-%d')}"] = text_button
        current_date += timedelta(days=1)

    calendar_data[f"main_menu_client"] = '🏠 Вернуться в главное меню 🏠'
    if trigger == 'cancel':
        main_client_kb = await message.answer(text=f'Все сброшено 👌\n\n{text}', reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]), parse_mode=ParseMode.HTML)
        bot.main_client_menu_ids[message.from_user.id] = main_client_kb.message_id
        await client_orm.add_inline_message_id(session, message.from_user.id, bot.main_client_menu_ids[message.from_user.id])
    else:
        try:
            await message.edit_text(inline_message_id=bot.main_client_menu_ids[message.from_user.id], text=text, parse_mode=ParseMode.HTML)
            await message.edit_reply_markup(inline_message_id=bot.main_client_menu_ids[message.from_user.id], reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]), parse_mode=ParseMode.HTML)
        except Exception as e: # На случай если сообщение не может быть отредактировано
            try:
                bot.main_client_menu_ids[message.from_user.id] = await client_orm.get_inline_message_id(session, message.from_user.id)
                await message.edit_text(inline_message_id=bot.main_client_menu_ids[message.from_user.id], text=text, parse_mode=ParseMode.HTML)
                await message.edit_reply_markup(inline_message_id=bot.main_client_menu_ids[message.from_user.id], reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]), parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f'oshibka>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<>>>>>>>>>>>> {e}')
                main_client_kb = await message.answer(text=text, reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]), parse_mode=ParseMode.HTML)
                bot.main_client_menu_ids[message.from_user.id] = main_client_kb.message_id
                await client_orm.add_inline_message_id(session, message.from_user.id, bot.main_client_menu_ids[message.from_user.id])
    
    try: await state.clear()
    except: pass

    await asyncio.sleep(60)
    try:
        if bot.client_idle_timer[message.from_user.id] > 59:
            text, btns_data, sizes = await main_menu_client_constructor(session=session, tg_id=message.from_user.id)
            await message.edit_text(text=text, parse_mode=ParseMode.HTML)
            await message.edit_reply_markup(reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
    except Exception as e: await bot.send_message(2136465129, text=f'Ошибка при автовозврате в стартовое меню клиента\n{e}')
        