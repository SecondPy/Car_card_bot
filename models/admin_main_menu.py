#from datetime import date, datetime, timedelta
#import random#

#from aiogram import Bot, F, types, Router
#from aiogram.fsm.context import FSMContext
##from database.models import Student
##from database.orm_admin_query import orm_add_product
#from const_values import ABBREVIATED_WEEK_DAYS, ADMIN_GREETINGS
#from sqlalchemy.ext.asyncio import AsyncSession#
#

#from database import orm_admin_query as admin_orm#

#from kbds.callback import get_callback_btns#
#
#

#async def get_main_admin_menu(session: AsyncSession, state: FSMContext, message: types.Message, trigger) -> None:
#    calendar_data = {}
#    today = date.today()
#    current_date = today - timedelta(days=(today.weekday()))
#    last_date = current_date + timedelta(days=28)
#    for _ in range(7):
#        calendar_data[f'{ABBREVIATED_WEEK_DAYS[_]}'] = f"|{ABBREVIATED_WEEK_DAYS[_]}|"
#    while current_date < last_date:
#        if current_date < today:
#            calendar_data[f"get_day {current_date.strftime('%Y-%m-%d')}"] = f"{current_date.strftime('%d')}"
#        else:
#            orders_data = await admin_orm.orm_get_order_with_date(session, current_date)
#            if orders_data and 'Выходной' not in {order.description for order in orders_data}:
#                hours = []
#                for order in orders_data:
#                    if ' ' in order.hours: hours += order.hours.split()
#                    else: hours.append(order.hours)
#                hours_count = len(set(hours)) 
#                if hours_count < 3: inline_smile = '🟢'
#                elif hours_count < 6: inline_smile = '🟡'
#                elif hours_count < 10: inline_smile = '🟠'
#                else: inline_smile = '🔴'
#                text_button = f"{current_date.strftime('%d')}{inline_smile}"
#            elif orders_data and 'Выходной' in {order.description for order in orders_data}:
#                text_button = f"{current_date.strftime('%d')} 🥳"
#            else: text_button = f"{current_date.strftime('%d')} 🟢"
#            calendar_data[f"get_day {current_date.strftime('%Y-%m-%d')}"] = text_button
#        current_date += timedelta(days=1)
#    if trigger == 'cancel':
#        main_admin_kb = await message.answer(text=f'Все сброшено 👌\n\n⬇️ Актуальное расписание ⬇️', reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]))
#        Bot.main_admin_menu_id = str(main_admin_kb.message_id)
#        await admin_orm.orm_add_inline_message_id(session, message.from_user.id, Bot.main_admin_menu_id)
#    else:
#        try:
#            await message.edit_text(inline_message_id=Bot.main_admin_menu_id, text='⬇️ Актуальное расписание ⬇️')
#            await message.edit_reply_markup(inline_message_id=Bot.main_admin_menu_id, reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]))
#        except Exception as e: # На случай если сообщение не может быть отредактировано
#            try:
#                Bot.main_admin_menu_id = await admin_orm.get_inline_message_id(session, message.from_user.id)
#                await message.edit_text(inline_message_id=Bot.main_admin_menu_id, text='⬇️ Актуальное расписание ⬇️')
#                await message.edit_reply_markup(inline_message_id=Bot.main_admin_menu_id, reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]))
#            except Exception as e:
#                print(f'oshibka>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<>>>>>>>>>>>> {e}')
#                main_admin_kb = await message.answer(text=f'{random.choice(ADMIN_GREETINGS)}\n\n⬇️ Актуальное расписание ⬇️', reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]))
#                Bot.main_admin_menu_id = str(main_admin_kb.message_id)
#                await admin_orm.orm_add_inline_message_id(session, message.from_user.id, Bot.main_admin_menu_id)
#    
#    try: await state.clear()
#    except: pass