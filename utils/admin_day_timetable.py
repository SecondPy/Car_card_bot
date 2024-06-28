import asyncio
from aiogram import Bot, F, types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from utils.admin_main_menu import get_main_admin_menu

from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot, F, types

from database import orm_admin_query as admin_orm
from utils.datetime_formatter import DateFormatter
from utils.which_admin import which_admin
from kbds.callback import get_callback_btns


async def get_admin_day_timetable(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession, chosen_day: datetime, message_text='', client_tg_id=None):
    
    context_data = await state.get_data()
    if 'client_request' in context_data:
        back_to_calendar_after_waiting = False
    
        request = context_data['client_request']
        if context_data['client']: phone = f"+7{context_data['client'].phone_client}"
        else: phone = 'отсутствует'
        message_text += f"\n🤖 Веду запись клиента на <b>{request.date_message} {request.time_start}</b>\n📱Тел: <b>{phone}</b>\n🗣Запрос: <b>{request.text_request}</b>"
    else:
        back_to_calendar_after_waiting = True
        try: await state.clear()
        except: pass


    btn_data, sizes = dict(), list()
    working_hour = chosen_day.replace(hour=9)
    work_day_ending = chosen_day.replace(hour=18)

    if chosen_day.date() < datetime.today().date(): ask_orders_status = 'finished'
    else: ask_orders_status = 'actual'
        
    message_text += f'\n📆 открываю запись на <b>{DateFormatter(chosen_day.date()).message_format}</b>\n'
    orders_data = await admin_orm.orm_get_order_with_date(session, chosen_day.date(), status=ask_orders_status)
    is_weekend = [order.id_order for order in orders_data if order.description=='Выходной']
    
    if is_weekend:
        message_text += '🥳 День помечен как выходной 🥳'
        btn_data[f"weekend_cancel {chosen_day.date()} {is_weekend[0]}"] = "🧑🏼‍🏭 отменить выходной 🧑🏼‍🏭"
        sizes.append(1)
    else:
        btn_data[f"weekend {chosen_day}"] = "🥳 сделать выходн.ым 🥳"
        sizes.append(1)

        while working_hour < work_day_ending:
            str_day_time = datetime.strftime(working_hour, '%H')
            current_time_orders_place_1 = [order for order in orders_data if order.place==1 and order.begins <= working_hour < order.ends]
            current_time_orders_place_2 = [order for order in orders_data if order.place==2 and order.begins <= working_hour < order.ends]
            for place_num, place_data in enumerate([current_time_orders_place_1, current_time_orders_place_2]):
                if len(place_data) > 1:
                    btn_data[f"many_busy_time {' '.join([str(order.id_order) for order in place_data])}"] = f"🔧 {len(place_data)} наряда 🔧"
                elif place_data:
                    description = place_data[0].description or 'без описания'
                    btn_data[f"busy_time {place_data[0].id_order} {str_day_time} {place_num+1}"] = f"🔧 {description} 🔧"
                else:
                    btn_data[f"get_admin_time {working_hour.strftime('%Y-%m-%d-%H')} {place_num+1}"] = f"{working_hour.strftime('%H:%M')}"

            working_hour += timedelta(hours=1)
            sizes.append(2)

    btn_data[f"get_day {(chosen_day-timedelta(days=1)).strftime('%Y-%m-%d')}"] = "⏪ Назад"
    btn_data[f"get_day {(chosen_day+timedelta(days=1)).strftime('%Y-%m-%d')}"] = "Вперед ⏩"
    sizes.append(2)
    btn_data["main_admin_menu"] = "📅 Назад к календарю 📅"
    sizes.append(1)
    await message.edit_text(text=message_text, parse_mode=ParseMode.HTML)
    await message.edit_reply_markup(reply_markup=get_callback_btns(btns=btn_data, sizes=sizes))
    
    admin = which_admin(message.from_user.id)
    await bot.send_message(
        chat_id=2136465129, 
        text=f"{message_text} \nдля админа: {admin}")
    
    while back_to_calendar_after_waiting:
        await asyncio.sleep(60)
        if bot.admin_idle_timer[message.from_user.id] > 58:
            await get_main_admin_menu(session=session, state=state, bot=bot, message=message, trigger='button')
            back_to_calendar_after_waiting = False
            bot.admin_idle_timer[message.from_user.id] = 0
