import asyncio
from aiogram import Bot, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from datetime import date, datetime, time, timedelta
from utils.client_main_menu import get_main_client_menu

from sqlalchemy.ext.asyncio import AsyncSession

from database import orm_admin_query as admin_orm
from utils.datetime_formatter import DateFormatter
from kbds.callback import get_callback_btns


async def get_client_day_timetable(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession, chosen_day: date, message_text=''):
    
    message_text += f'\n🤖 <b>Открываю запись на {DateFormatter(chosen_day).message_format}</b>\n'
    btn_data = {}
    start_time = datetime.combine(chosen_day, time(9, 0))
    day_orders_data = await admin_orm.orm_get_order_with_date(session, chosen_day)

    while start_time < datetime.combine(chosen_day, time(18, 0)):
        time_orders_data = [order for order in day_orders_data if order.begins <= start_time < order.ends]
        place_closed = len([order.place for order in time_orders_data])
        str_start_time = datetime.strftime(start_time, '%H')
        if chosen_day == date.today() and start_time.hour <= datetime.now().hour: btn_data[f"closed_time not_order {str_start_time}"] = f"🔓 Недоступно для записи 🔓"
        elif place_closed == 2: btn_data[f"closed_time {datetime.now().microsecond} {str_start_time}"] = f"🔓 Недоступно для записи 🔓"
        else: btn_data[f"get_client_time {chosen_day.strftime('%Y-%m-%d')} {datetime.strftime(start_time, '%H')}"] = f"{start_time.strftime('%H:%M')}"

        start_time += timedelta(hours=1)
    
    btn_data[f"get_client_day {(chosen_day-timedelta(days=1)).strftime('%Y-%m-%d')}"] = "⏪ Назад"
    btn_data[f"get_client_day {(chosen_day+timedelta(days=1)).strftime('%Y-%m-%d')}"] = "Вперед ⏩"
    btn_data["client_main_menu"] = "📅 Назад к календарю 📅"
    await message.edit_text(text=message_text, parse_mode=ParseMode.HTML)
    await message.edit_reply_markup(reply_markup=get_callback_btns(btns=btn_data, sizes=[1]*9+[2]+[1]))
    
    try: await state.clear()
    except: pass
    
    await asyncio.sleep(30)
    if bot.client_idle_timer[message.from_user.id] > 29:
        await get_main_client_menu(session=session, state=state, bot=bot, message=message, trigger='button')





#async def get_client_past_day_timetable(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession, chosen_day: date, message_text=''):
#    message_text += f'\n🤖 Открываю {DateFormatter(chosen_day).message_format}\n'
#    btn_data = {}
#    start_time = datetime.strptime('09:00', '%H:%M')
#    
#    orders_data = await admin_orm.orm_get_order_with_date(session, chosen_day)
#    #is_weekend = [order.id_order for order in orders_data if order.description=='Выходной']
#    #if is_weekend: btn_data[f"weekend_cancel {chosen_day} {is_weekend[0]}"] = "🧑🏼‍🏭 отменить выходной 🧑🏼‍🏭"
#    #else: btn_data[f"weekend {chosen_day}"] = "🥳 сделать выходным 🥳"
#
#    while start_time < datetime.strptime('18:00', '%H:%M'):
#        str_start_time = datetime.strftime(start_time, '%H')
#        int_start_time = int(str_start_time)
#        current_time_orders = [order for order in orders_data if int_start_time in [int(hour) for hour in order.hours.split()]]
#        if current_time_orders:
#            btn_data[f"closed_time {current_time_orders[0].id_order} {str_start_time}"] = f"🔓 Недоступно для записи 🔓"
#        else:
#            btn_data[f"get_client_time {chosen_day.strftime('%Y-%m-%d')} {datetime.strftime(start_time, '%H')}"] = f"{start_time.strftime('%H:%M')}"
#
#        start_time += timedelta(hours=1)
#    
#    btn_data[f"get_client_day {(chosen_day-timedelta(days=1)).strftime('%Y-%m-%d')}"] = "⏪ Назад"
#    btn_data[f"get_client_day {(chosen_day+timedelta(days=1)).strftime('%Y-%m-%d')}"] = "Вперед ⏩"
#    btn_data["client_main_menu"] = "📅 Назад к календарю 📅"
#    await message.edit_text(text=message_text, parse_mode=ParseMode.HTML)
#    await message.edit_reply_markup(reply_markup=get_callback_btns(btns=btn_data, sizes=[1]*9+[2]+[1]))
#    
#    try: await state.clear()
#    except: pass
#    
#    await asyncio.sleep(30)
#    if bot.client_idle_timer > 29:
#        await get_main_client_menu(session, state, message, trigger='button')