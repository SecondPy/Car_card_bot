import asyncio
from aiogram import Bot, F, types, Router
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from datetime import date, datetime, timedelta
from utils.client_main_menu import get_main_client_menu



from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot, F, types, Router


from database import orm_admin_query as admin_orm
from utils.datetime_formatter import DateFormatter
from kbds.callback import get_callback_btns



async def show_client_order(session: AsyncSession, state: FSMContext, bot: Bot, message, order, answer_text=''):
    services = [order.oil_m, order.grm, order.oil_kpp, order.spark_plugs, order.power_steer, order.coolant, order.break_fluid, order.fuel_filter]
    btn_inline_services = [
        {'oil_m':'масло моторное'}, 
        {'grm':'ГРМ'}, 
        {'oil_kpp':'масло кпп'}, 
        {'spark_plugs':'cвечи зажигания'}, 
        {'power_steer':'масло ГУР'}, 
        {'coolant':'антифриз'}, 
        {'break_fluid':'тормозную жидкость'}, 
        {'fuel_filter':'фильтр топливный'}
    ]

    btns_data, sizes = dict(), list()
    
    if order.mileage: answer_text += f'\n-🏃🏼‍♂️ <b>Пробег</b>: {order.mileage}\n'
    if order.advice: answer_text += f'-🗣 <b>рекомендации</b>: {order.advice}\n\n'
    

    if {service for service in services if service}:
        answer_text += '\n<b>Заменили:</b>\n'
        for tab, service in enumerate(services):
            if service:
                answer_text += f"-🛢{''.join((btn_inline_services[tab].values()))}\n"
    
    if order.repair_photo and order.repair_photo != ' ':
        count_images = len(order.repair_photo.split())
        btns_data[f"show_client_repair_photo {order.id_order} {count_images}"] = f"📷 Показать добавленные фото({count_images}) 📷"
        sizes.append(1)

    if answer_text == 'В истории пока только 1 наряд': answer_text += '\n🤷‍♂️ Никакой информации по нему внесено не было. Обратитесь в сервис за подробностями +78443210102'
    btns_data[f"main_menu_client"] = '🏠 Вернуться в главное меню 🏠'
    sizes.append(1)

    await message.edit_text(text=answer_text, parse_mode=ParseMode.HTML)
    await message.edit_reply_markup(reply_markup=get_callback_btns(btns=btns_data, sizes=[1]*9+[2]+[1]))

