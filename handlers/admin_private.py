from datetime import date, datetime, time, timedelta
import time as t
import random
import locale
import asyncio

from aiogram import Bot, F, types, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, or_f, StateFilter   #commanstart Обрабатывает только команду старт
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
#from database.models import Student
#from database.orm_admin_query import orm_add_product
from const_values import ABBREVIATED_WEEK_DAYS, CLIENT_EMOJI
from sqlalchemy.ext.asyncio import AsyncSession


from database import orm_admin_query as admin_orm
from handlers.user_private import main_menu_client_constructor
from utils.find_phone import find_phone
from utils.datetime_formatter import DateFormatter
from filters.chat_types import ChatTypeFilter, IsAdmin
from utils.admin_main_menu import get_main_admin_menu
from utils.admin_day_timetable import get_admin_day_timetable
from kbds.reply import get_keyboard
from kbds.callback import get_callback_btns



admin_private_router = Router()
admin_private_router.message.filter(ChatTypeFilter(['private']), IsAdmin())


class FSMAdminNewOrder(StatesGroup):
    get_new_order_data = State()


class FSMAdminFinishOrder(StatesGroup):
    finish_order = State()
    


async def new_order_menu_constructor(session: AsyncSession, data: dict) -> tuple:
    #(text, buttons_data, sizes)
    answer_text = f"-🤖 Собираю данные для наряда на <b>{data['message_date']}:</b>\n\n"
    answer_text += f"-🕰 Начало в <b>{data['begins'].hour}:00</b>. Машина будет готова к <b>{data['ends'].hour}:00</b>\n"
    if 'client' in data: 
        answer_text += f"\n-{random.choice(CLIENT_EMOJI)} наряд будет привязан к клиенту: <b>+7{data['client'].phone_client or data['client'].id_telegram}</b>"
        if data['car'] != 0:
            car = await admin_orm.get_car_with_id(session, data['car'])



    if 'description' in data: answer_text += f"\n-📝Описание есть: <b>{data['description']}</b>\n"
    else: answer_text += '\n\n🤖 ожидаю описание'
    new_order_buttons, sizes = dict(), list()
    if data['begins'].hour < 17:
        #time_callback = int(data['hours'].split()[0])
        hour_delta_start = 2 if (data['ends']-data['begins']).total_seconds() == 3600 else 1
        work_day_ends = 19
        for _ in range(hour_delta_start, work_day_ends-data['begins'].hour):
            if _ == 1: hours = 'час'
            else: hours = 'часа' if _ < 5 else 'часов'
            orders_data = await admin_orm.orm_get_order_with_date_time_and_place(session, data['begins']+timedelta(hours=_-1), place=data['place'])
            if orders_data: new_order_buttons[f'new_order_duration {_}'] = f'💢 {_} {hours}'
            else: new_order_buttons[f'new_order_duration {_}'] = f'⏳ {_} {hours}'
        if len(new_order_buttons) % 3 == 2: sizes = [3]*(len(new_order_buttons)//3) + [2]
        elif len(new_order_buttons) % 3 == 1: sizes = [3]*(len(new_order_buttons)//3) + [1]
        else: sizes = [3]*(len(new_order_buttons)//3)
    if 'client' in data:
        orders_history = await admin_orm.get_orders_with_client_id(session, data['client'].id_client)
        if len(orders_history) > 0:
            new_order_buttons[f"show_admin_history {' '.join([str(order.id_order) for order in orders_history])}"] = f'📖 показать историю 📖 ({len(orders_history)})'
            sizes.append(1)

    if data['state_order'] == 'create_new_order':
        new_order_buttons[f"cancel {datetime.strftime(data['begins'], '%Y-%m-%d')}"] = '❎ отмена ❎'
        new_order_buttons[f'push_new_order'] = '✅ Создать наряд ✅'
        sizes.append(2)
    elif data['state_order'] == 'update_order':
        str_day_time = datetime.strftime(data['order_data'].begins, '%H')
        new_order_buttons[f"busy_time {data['order_data'].id_order} {str_day_time} {data['order_data'].place}"] = '✅ готово ✅'

    return [answer_text, new_order_buttons, sizes]


async def edit_order_menu_constructor(session: AsyncSession, id_order: int, callback: str, state: FSMContext):
    order_data = await admin_orm.orm_get_order_with_id(session, id_order)
    await state.update_data(order_data=order_data, new_photo_ids=[])
    services = [order_data.oil_m, order_data.grm, order_data.oil_kpp, order_data.spark_plugs, order_data.power_steer, order_data.coolant, order_data.break_fluid, order_data.fuel_filter]
    btn_inline_services = [{'oil_m':'масло моторное'}, {'grm':'ГРМ'}, {'oil_kpp':'масло кпп'}, {'spark_plugs':'свечи'}, {'power_steer':'масло ГУР'}, {'coolant':'антифриз'}, {'break_fluid':'тормозная ж.'}, {'fuel_filter':'фильтр топл'}]
    btn_text_services = {'advice':'рекомендации', 'mileage':'пробег', 'phone':'телефон клиента', 'car':'марку и модель автомобиля'}
    btns_data, sizes = dict(), list()

    if callback in {''.join(service.keys()) for service in btn_inline_services}:
        index_service = [''.join(item.keys()) for item in btn_inline_services].index(callback)
        services[index_service] = not services[index_service]
        await admin_orm.change_inline_service(session, id_order, services)  
      
    description = order_data.description or 'не добавлялось'
    if callback == 'add_photo': answer_text = f"<b>-📸Фото успешно добавлено</b>\n\n-📃Описание: {description}\n"
    else: answer_text = f"-📃Описание: <b>{description}</b>\n"
    answer_text += f"-🕰 Начало в <b>{order_data.begins.hour}:00</b>. Машина будет готова к <b>{order_data.ends.hour}:00</b>\n"

    if order_data.id_client:
        client = await admin_orm.get_client_with_id(session, order_data.id_client)
        if client.phone_client:
            client_message_data = f"клиент с тел: <b>+7{client.phone_client}</b>"
        else: client_message_data = f"клиент с tg_id: <b>{client.id_telegram}</b>"
        answer_text += f"-{random.choice(CLIENT_EMOJI)} <b>к наряду привязан {client_message_data}</b>\n"
        orders_history = await admin_orm.get_orders_with_client_id(session, order_data.id_client)
        orders_history = [order for order in orders_history if order.status=='finished']
        if len(orders_history) != 0:
            btns_data[f"show_admin_history {' '.join([str(order.id_order) for order in orders_history])}"] = f'📖 показать историю 📖 ({len(orders_history)})'
            sizes.append(1)

    if order_data.mileage: 
        btn_mileage = '✅ пробег'
        answer_text += f'-🏃🏼‍♂️ <b>Пробег: {order_data.mileage}</b>\n'
    else: btn_mileage = 'пробег'
    if order_data.advice:
        btn_advice = '✅ рекомендации'
        answer_text += f'-🗣 <b>рекомендации: {order_data.advice}</b>\n\n'
    else: btn_advice = 'рекомендации'
    
    if {service for service in services if service}:
        answer_text += '\nЗаменили:\n'
    
    for tab, service in enumerate(services):
        if service:
            answer_text += f"-🛢{''.join((btn_inline_services[tab].values()))}\n"
            btn_inline_services[tab][''.join(btn_inline_services[tab].keys())] = f"✅ {''.join((btn_inline_services[tab].values()))}"

    
    # Текстом: рекомендации, пробег, телефон, авто
    if callback not in 'advice mileage phone car':
        if order_data.repair_photo and order_data.repair_photo != ' ':
            btns_data[f"show_repair_photo {id_order}"] = f"📷 Показать добавленные фото({len(order_data.repair_photo.split())}) 📷"
            sizes.append(1)

        btns_data[f"calling_nothing add_text_options"] = '🖊______________    ⬇Добавить сведения⬇    ______________🖊'
        sizes.append(1)
        btns_data[f'busy_time {order_data.id_order} advice'] = btn_advice
        btns_data[f'busy_time {order_data.id_order} mileage'] = btn_mileage
        btns_data[f'busy_time {order_data.id_order} phone'] = 'добавить телефон' if not order_data.id_client else '✅ изменить телефон'
        btns_data[f'busy_time {order_data.id_order} car'] = 'добавить авто' if not order_data.id_car else '✅ изменить авто'
        sizes += [2]*2

        btns_data[f"calling_nothing add_inline_options"] = '🛢____________________    ⬇Опции ТО⬇    ____________________🛢'
        sizes.append(1)

        for btn in btn_inline_services:
            btns_data[f"busy_time {order_data.id_order} {''.join(btn.keys())}"] = ''.join(btn.values())
        sizes += [2]*4

        btns_data[f"calling_nothing manage_order"] = '👨‍💼____________    ⬇Навигация и управлениe⬇    ___________👨‍💼'
        sizes.append(1)
        
        btns_data[f'chose_duration'] = '⏳ длительность ⏳'
        btns_data[f"get_admin_time {order_data.begins.strftime('%Y-%m-%d-%H')} {order_data.place}"] = f"❗️ Записать поверх ❗️"
        sizes.append(2)

        btns_data[f'finish_order {id_order}'] = '✅ Завершить наряд ✅'
        btns_data[f'delete_order {id_order} {order_data.begins}'] = '🙅🏼 Удалить запись🙅🏼 '
        sizes.append(2)
        btns_data["main_admin_menu"] = "📅 К календарю 📅"
        btns_data[f"get_day {order_data.begins}"] = '↩️ Вернуться'
        sizes.append(2)

        answer_text += '\n-🤖 <b>можно отправить фото с процесса ремонта или фото заказ-наряда. Оно будет доступно в истории и при необходимости можно будет удалить. \n❗️Возможны ошибки при множественной загрузке сразу нескольких фото❗️</b>'
    
    else:
        answer_text += f'\n-🤖 <b>напиши {btn_text_services[callback]}</b>'
        btns_data["main_admin_menu"] = "📅 К календарю 📅"
        #btns_data[f"get_day {order_data.begins}"] = '↩️ Вернуться'
        btns_data[f"busy_time {order_data.id_order} {order_data.begins}"] = '↩️ Назад'
        await state.update_data(state=callback)
    
    await state.update_data(order_data=order_data)
    return [answer_text, btns_data, sizes]
    
    # Кнопкой опции ТО: ГРМ, ОЖ, Свечи, М Моторное, М Коробки, М мосты, фильтр топл , тормозуха, назад
    # Перманентные кнопки : завершить, отмена

# отмена клавой    
@admin_private_router.message(StateFilter("*"), F.text.lower().contains('отмена'))
async def cancel_handler(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    await state.clear()
    try: 
        await bot.delete_message(message.from_user.id, bot.main_admin_menu_ids[message.from_user.id])
        await get_main_admin_menu(session=session, state=state, bot=bot, message=message, trigger='cancel')
        await bot.delete_message(message.from_user.id, message.message_id)
    except: 
        reply = await message.answer('Нечего отменять 💁‍♂️')
        await asyncio.sleep(5)
        try:
            await bot.delete_message(message.from_user.id, reply.message_id)
            await bot.delete_message(message.from_user.id, message.message_id)
        except: pass

@admin_private_router.callback_query(StateFilter("*"), F.data=='delete_selected_message')
async def delete_selected_message(callback: types.CallbackQuery) -> None:
    message = callback.message
    await message.delete()


# отмена кнопкой  
@admin_private_router.callback_query(StateFilter("*"), F.data.startswith('cancel'))
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    bot.admin_idle_timer[callback.message.from_user.id] = 0
    
    await state.clear()
    open_day = datetime.strptime(callback.data[7:], '%Y-%m-%d')
    await get_admin_day_timetable(callback.message, state, bot, session, open_day, message_text='Наряд сброшен 👌 Записать на другое время?')
    

@admin_private_router.message(or_f(F.text.lower().contains('admin'), F.text.lower().contains('админ'), F.text.lower().contains('календарь')))
async def get_admins_powers(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[message.from_user.id] = 0
    
    await bot.delete_message(message.from_user.id, message.message_id)
    try: await bot.delete_message(message.from_user.id, bot.main_admin_menu_ids[message.from_user.id]) 
    except: pass
    await get_main_admin_menu(session=session, state=state, bot=bot, message=message, trigger='admin')


@admin_private_router.callback_query(F.data=='main_admin_menu')
async def show_calendar_by_callback(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0
    
    await get_main_admin_menu(session=session, state=state, bot=bot, message=callback.message, trigger='button', date_start=date.today())
    await admin_orm.orm_add_inline_message_id(session, callback.from_user.id, callback.message.message_id)


@admin_private_router.callback_query(F.data.startswith('flip_month'))
async def show_calendar_by_callback(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0
    
    callback_data = callback.data.split()
    date_start = datetime.strptime(callback_data[1], '%Y-%m-%d').date()
    direction = callback_data[2]
    if direction =='back': date_start = date_start - timedelta(days=28)
    elif direction == 'next': date_start = date_start + timedelta(days=28)
    await get_main_admin_menu(session=session, state=state, bot=bot, message=callback.message, trigger='button', date_start=date_start)


@admin_private_router.callback_query(F.data.startswith('get_day'))
async def get_admin_daytimes(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session=AsyncSession) -> None:
    bot.admin_idle_timer[callback.message.from_user.id] = 0

    callback_data = callback.data.split()
    if len(callback_data) > 3:
        client_request = await admin_orm.get_client_request_with_id(session, int(callback_data[2]))
        client = await admin_orm.get_client_with_tg_id(session, client_request.id_telegram)
        await state.update_data(client_request=client_request, client=client, description=client_request.text_request, delete_client_message_id=callback_data[3])

    chosen_day = datetime.strptime(callback.data.split()[1], '%Y-%m-%d')
    await get_admin_day_timetable(callback.message, state, bot, session, chosen_day)


@admin_private_router.callback_query(F.data.startswith('weekend'))
async def weekends(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session=AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0
    
    callback_data = callback.data.split()
    callback_day = datetime.strptime(callback_data[1], '%Y-%m-%d')
    
    if 'cancel' in callback_data[0]:
        callback_id_order = int(callback_data[2])
        await admin_orm.orm_unmake_weekend(session, callback_id_order)    
    else: await admin_orm.orm_make_weekend(session, callback_day)
        
    await get_admin_day_timetable(callback.message, state, bot, session, callback_day)


@admin_private_router.callback_query(F.data.startswith('get_admin_time'))
async def add_new_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0

    callback_data = callback.data.split()   # Получаем данные кнопки
    message = callback.message  # Для упрощения кода создаем переменную с объектом message
    date_time_callback = datetime.strptime(callback_data[1], '%Y-%m-%d-%H') # Дата в формате DateTime
    message_date_callback_message_format = DateFormatter(date_time_callback).message_format    # форматируем дату в человекояз
    order_place = int(callback_data[2]) 

    await state.update_data(
        begins=date_time_callback,
        ends=date_time_callback+timedelta(hours=1),
        car=0,
        place=order_place,
        message_date=message_date_callback_message_format,
        message_id=message.message_id,
        state_order='create_new_order'
    )
    
    context_data = await state.get_data()
    
    answer_text, btns_data, sizes = await new_order_menu_constructor(session, context_data)

    await message.edit_text(text=answer_text, parse_mode=ParseMode.HTML)
    await message.edit_reply_markup(reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))

    await state.set_state(FSMAdminNewOrder.get_new_order_data)


@admin_private_router.message(FSMAdminNewOrder.get_new_order_data, F.text)
async def get_new_order_data(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession):
    bot.admin_idle_timer[message.from_user.id] = 0

    await state.update_data(description=message.text)
    context_data = await state.get_data()

    is_phone = await find_phone(message.text)
    if is_phone:
        if 'client_request' not in context_data:
            client = await admin_orm.get_client_with_phone(session, is_phone) or await admin_orm.add_new_client_with_phone(session, is_phone)
        elif 'client_request' in context_data:
            client = await admin_orm.add_phone_to_client_with_tg_id(session, context_data['client_request'].id_telegram, is_phone)
        if client_cars := await admin_orm.get_client_cars(session, client.id_client):
            await state.update_data(car=client_cars[0].id_car)
        
        await state.update_data(client=client)
        context_data = await state.get_data()
    
    
    answer_text, btns_data, sizes = await new_order_menu_constructor(session, context_data)
    await bot.edit_message_text(chat_id=message.from_user.id, message_id=context_data['message_id'], text=answer_text, parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=context_data['message_id'], reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
    
    await asyncio.sleep(10)
    await message.delete()


@admin_private_router.callback_query(F.data.startswith('new_order_duration'))
async def get_new_order_hours(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0
    
    order_duration = int(callback.data.split()[1])
    context_data = await state.get_data()
    if context_data['state_order'] == 'create_new_order': 
        order_ends = context_data['begins'] + timedelta(hours=order_duration)
        await state.update_data(ends=order_ends)
        
    elif context_data['state_order'] == 'update_order': 
        context_data['order_data'].ends = context_data['order_data'].begins + timedelta(hours=order_duration)
        await admin_orm.change_order_duration(session, context_data)
    

    context_data = await state.get_data()
    inline_message_id = context_data['message_id']
    answer_text, btns_data, sizes = await new_order_menu_constructor(session, context_data)

    await bot.edit_message_text(chat_id=callback.from_user.id, message_id=inline_message_id, text=answer_text, parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=inline_message_id, reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))


@admin_private_router.callback_query(FSMAdminNewOrder.get_new_order_data, F.data=='push_new_order')
async def push_new_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0

    context_data = await state.get_data()
    if 'description' not in context_data:    # Надо как-то по умнее этот блок сделать
        await state.update_data(description='')
        context_data = await state.get_data()

    if callback.from_user.id != 2136465129:
        await bot.send_message(
        chat_id=2136465129, 
        text=f"Добавлен новый ордер админом: {callback.from_user.id}\nОписание - {context_data['description'] or 'без описания'}\nНа {context_data['begins']}")
    
    await admin_orm.push_new_order(session, context_data)

    if 'client_request' in context_data:
        client_tg_id = context_data['client_request'].id_telegram
        await bot.send_message(
            chat_id=client_tg_id, 
            text=f"👌 мастер записал Вас на ремонт на {context_data['message_date']} {context_data['begins'].hour}:00"
        )
        text, btns_data, sizes = await main_menu_client_constructor(session, client_tg_id)
        await bot.edit_message_text(
            chat_id=client_tg_id,
            message_id=bot.main_client_menu_ids[client_tg_id],
            text=text,
            parse_mode=ParseMode.HTML
        )
        
        await bot.edit_message_reply_markup(
            chat_id=client_tg_id, 
            message_id=bot.main_client_menu_ids[client_tg_id], 
            reply_markup=get_callback_btns(btns=btns_data, sizes=sizes)
        )
        
        await bot.delete_message(client_tg_id, context_data['delete_client_message_id'])
        await callback.answer('✅Наряд успешно добавлен. Клиент будет уведомлён', show_alert=True)
        await bot.delete_message(callback.from_user.id, callback.message.message_id)
        await state.clear()   
    
    
    else: 
        await state.clear()
        day = context_data['begins'] - timedelta(hours=context_data['begins'].hour)
        await get_admin_day_timetable(callback.message, state, bot, session, day, '✅ Наряд успешно добавлен')
    
    admin_ids = await admin_orm.get_admins_ids(session=None)
    text, btns = await get_main_admin_menu(session=session, state=state, bot=bot, message=callback.message, trigger='update_other_admins', date_start=date.today())
    for admin_menu in admin_ids:
        if admin_menu.tg_id != callback.message.from_user.id:
            try:
                await bot.edit_message_text(text=text, chat_id=admin_menu.tg_id, message_id=admin_menu.inline_message_id, parse_mode=ParseMode.HTML)
                await bot.edit_message_reply_markup(chat_id=admin_menu.tg_id, message_id=admin_menu.inline_message_id, reply_markup=get_callback_btns(btns=btns, sizes=[7]))
            except Exception as e: print(f'\n\n\nОшибка в обновлении главного меню админов: {e}\n\n\n')



@admin_private_router.callback_query(F.data.startswith('show_admin_history'))
async def edit_selected_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0
    
    await state.clear()
    callback_data = callback.data.split()
    callback_ids = [int(id) for id in ' '.join(callback_data[1:]).split()]

    btns_data, sizes = dict(), list()
    orders_data = [await admin_orm.orm_get_order_with_id(session, id) for id in callback_ids]
    for order in orders_data:
        btns_data[f"busy_time {order.id_order} {order.begins}"] = f"📗 от {order.begins}, {order.description or 'без описания'}"
        sizes.append(1)
    btns_data["main_admin_menu"] = "📅 К календарю 📅"
    
    hystory_message = await bot.send_message(callback.from_user.id, text = 'Выбери из списка', reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
    
    hystory_message_deleted = False
    while not hystory_message_deleted:
        await asyncio.sleep(14)
        if bot.admin_idle_timer[callback.message.from_user.id] > 13:
            await bot.delete_message(callback.from_user.id, hystory_message.message_id)
            hystory_message_deleted = True


@admin_private_router.callback_query(F.data.startswith('many_busy_time'))
async def edit_selected_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0

    callback_data = callback.data.split()

    ids_orders = [int(id) for id in callback_data[1:]]
    btns_data, sizes = dict(), list()
    answer_text = '-🤖<b>Выбери для редактирования</b>:'
    for id_order in ids_orders:
        order_data = await admin_orm.orm_get_order_with_id(session, id_order)
        description = order_data.description or 'описание не было добавлено'
        btns_data[f'busy_time {id_order} choice_order'] = f'-📃 {description}'

    sizes = [1] * len(ids_orders)
    btns_data[f"get_day {order_data.begins}"] = '↩️ Вернуться'

    await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id, text=answer_text, parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))


@admin_private_router.callback_query(F.data.startswith('busy_time'))
async def edit_selected_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0


    await state.update_data(message_id=callback.message.message_id, state_order='update_order')
    callback_data = callback.data.split()
    id_order = int(callback_data[1])
    order_data = await admin_orm.orm_get_order_with_id(session, id_order)

    message_date = DateFormatter(order_data.begins).message_format
    await state.update_data(
        order_data=order_data,
        place=order_data.place,
        begins=order_data.begins,
        ends=order_data.ends,
        message_date=message_date
    )

    answer_text, btns_data, sizes = await edit_order_menu_constructor(session, id_order, callback_data[2], state)

    await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id, text=answer_text, parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
    
    await state.set_state(FSMAdminFinishOrder.finish_order)


@admin_private_router.callback_query(F.data.startswith('chose_duration'))
async def edit_order_duration(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    message = callback.message
    context_data = await state.update_data()
    answer_text, btns_data, sizes = await new_order_menu_constructor(session, context_data)
    await state.set_state(FSMAdminNewOrder.get_new_order_data)
    await message.edit_text(text=answer_text, parse_mode=ParseMode.HTML)
    await message.edit_reply_markup(reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))


@admin_private_router.callback_query(F.data.startswith('finish_order'))
async def push_edited_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0

    callback_data = callback.data.split()
    id_order = int(callback_data[1])

    order_data = await admin_orm.orm_get_order_with_id(session, id_order)
    if order_data.id_client:
        client = await admin_orm.get_client_with_id(session, order_data.id_client)
        if client.id_telegram:
            await bot.send_message(client.id_telegram, text='✅ Ваша машина готова. Подробности можно узнать по телефону +78443210102')
            await callback.answer(text='👍 Клиент уведомлен о завершении наряда', show_alert=True)

    await admin_orm.finish_order_with_id(session, id_order)
    context_data = await state.get_data()
    chosen_day = context_data['order_data'].begins
    
    await callback.answer('✅Наряд завершен успешно\nМесто свободно для записи', show_alert=True)

    await get_admin_day_timetable(callback.message, state, bot, session, chosen_day)
    await state.clear()


@admin_private_router.message(FSMAdminFinishOrder.finish_order, F.text)
async def edit_selected_order(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[message.from_user.id] = 0

    context_data = await state.get_data()
    order_data = context_data['order_data']
    
    try:
        input = context_data['state']
        match input:
            case 'advice': await admin_orm.push_new_advice(session, order_data.id_order, message.text)
            case 'mileage': await admin_orm.push_new_mileage(session, order_data.id_order, message.text)
            case 'phone': 
                is_phone = await find_phone(message.text)
                if is_phone: await admin_orm.push_new_phone(session, order_data.id_order, is_phone)
                else:
                    message_answer = await message.answer('Не получается преобразовать в номер телефона, давай еще раз')
            case 'car':
                message_answer = await message.answer('Функция находится в разработке')

    except Exception as e:
        await admin_orm.push_new_description(session, order_data.id_order, message.text)
    

    answer_text, btns_data, sizes = await edit_order_menu_constructor(session, order_data.id_order, 'None', state)
    await bot.edit_message_text(chat_id=message.from_user.id, message_id=context_data['message_id'], text=answer_text, parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=context_data['message_id'], reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
        

    message_is_deleted = False
    while not message_is_deleted:
        await asyncio.sleep(10)
        try:
            await bot.delete_message(chat_id=message.from_user.id,  message_id=message.message_id)
            await bot.delete_message(chat_id=message.from_user.id, message_id=message_answer.message_id)
            message_is_deleted = True
        except: message_is_deleted = True
    
    await state.set_state(FSMAdminFinishOrder.finish_order)

    
    
    


@admin_private_router.message(FSMAdminFinishOrder.finish_order, F.photo)
async def get_order_photo(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[message.from_user.id] = 0
    context_data = await state.get_data()
    new_photo_ids = context_data['new_photo_ids']
    order_data = context_data['order_data']
    new_photo_ids.append(message.photo[0].file_id)
    nums_of_photo = 0

    for id_photo in new_photo_ids:
        nums_of_photo += 1
        await admin_orm.add_new_photo(session, order_data.id_order, id_photo)
        try: await bot.delete_message(message.from_user.id, message.message_id)
        except: pass

    answer_text, btns_data, sizes = await edit_order_menu_constructor(session, order_data.id_order, 'add_photo', state)
    if nums_of_photo > 1:
        await asyncio.sleep(1.5)
    await bot.edit_message_text(chat_id=message.from_user.id, message_id=context_data['message_id'], text=answer_text, parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=context_data['message_id'], reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
    

@admin_private_router.callback_query(F.data.startswith('show_repair_photo'))
async def show_repair_photo(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0

    context_data = await state.get_data()
    order_data = context_data['order_data']
    order_images = order_data.repair_photo.split()

    if len(order_images) == 1:
        btn_data = dict()
        btn_data[f'delete_photo {order_data.id_order} {order_images[0][22:34]}'] = f'❎'
        message_answer = await callback.message.answer_photo(order_images[0], reply_markup=get_callback_btns(btns=btn_data, sizes=[1]))
        await callback.answer()

    else:
        btn_data, sizes = dict(), list()
        btn_data[f'delete_photo {order_data.id_order} {order_images[0][22:34]}'] = f'❎'
        btn_data[f'flip_admin_photo {order_data.id_order} next 0'] = '⏩'
        sizes.append(2)
        message_answer = await callback.message.answer_photo(order_images[0], reply_markup=get_callback_btns(btns=btn_data, sizes=[2]))
        await state.update_data(message_caption_id=message_answer.message_id)
    
    
    message_is_deleted = False
    while not message_is_deleted:
        await asyncio.sleep(10)
        if bot.admin_idle_timer[callback.message.from_user.id] > 9:
            try: 
                await bot.delete_message(chat_id=callback.from_user.id, message_id=message_answer.message_id)
                message_is_deleted = True
            except: message_is_deleted = True


@admin_private_router.callback_query(F.data.startswith('flip_admin_photo'))
async def show_repair_photo(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0
    
    callback_data = callback.data.split()
    id_order = int(callback_data[1])
    order_data = await admin_orm.orm_get_order_with_id(session, id_order)
    type_flip = callback_data[2]
    current_num_photo = int(callback_data[3])
    order_images = order_data.repair_photo.split()
    context_data = await state.get_data()
    caption_id = context_data['message_caption_id']

    if type_flip == 'next':
        current_num_photo += 1
        btn_data, sizes = dict(), list()
        if len(order_images) == current_num_photo+1:
            btn_data[f'flip_admin_photo {id_order} back {current_num_photo}'] = '⏪'
            btn_data[f'delete_photo {order_data.id_order} {order_images[current_num_photo][22:34]}'] = f'❎Удалить❎'
            sizes.append(2)
        else:
            btn_data[f'flip_admin_photo {id_order} back {current_num_photo}'] = '⏪'
            btn_data[f'delete_photo {order_data.id_order} {order_images[current_num_photo][22:34]}'] = f'❎Удалить❎'
            btn_data[f'flip_admin_photo {id_order} next {current_num_photo}'] = '⏩'
            sizes.append(3)
    elif type_flip == 'back':
        current_num_photo -= 1
        btn_data, sizes = dict(), list()
        if current_num_photo == 0:
            btn_data[f'delete_photo {order_data.id_order} {order_images[current_num_photo][22:34]}'] = f'❎Удалить❎'
            btn_data[f'flip_admin_photo {id_order} next {current_num_photo}'] = '⏩'
            sizes.append(2)
        else:
            btn_data[f'flip_admin_photo {id_order} back {current_num_photo}'] = '⏪'
            btn_data[f'delete_photo {order_data.id_order} {order_images[current_num_photo][22:34]}'] = f'❎Удалить❎'
            btn_data[f'flip_admin_photo {id_order} next {current_num_photo}'] = '⏩'
            sizes.append(3)
    
    photo = types.InputMediaPhoto(media=order_images[current_num_photo])
    await bot.edit_message_media(media=photo, chat_id=callback.from_user.id, message_id=caption_id, reply_markup=get_callback_btns(btns=btn_data, sizes=sizes))

    photo_is_deleted = False
    while not photo_is_deleted:
        await asyncio.sleep(10)
        if bot.admin_idle_timer[callback.message.from_user.id] > 9:
            try: 
                await bot.delete_message(chat_id=callback.from_user.id, message_id=caption_id)
                photo_is_deleted = True
            except: photo_is_deleted = True

@admin_private_router.callback_query(F.data.startswith('delete_photo'))
async def show_repair_photo(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0

    callback_data = callback.data.split()
    id_order = int(callback_data[1])
    clice_id_photo = callback_data[2]

    context_data = await state.get_data()
    order_data = context_data['order_data']

    delete_process = await admin_orm.delete_repair_photo(session, id_order, clice_id_photo)
    if delete_process == 'success': await callback.answer('👌🏿 Фото удалено', show_alert=True)   
    else: await callback.answer('ошибка при удалении', show_alert=True)
     
    await callback.message.delete()
    answer_text, btns_data, sizes = await edit_order_menu_constructor(session, order_data.id_order, 'add_photo', state)
    
    await bot.edit_message_text(chat_id=callback.from_user.id, message_id=context_data['message_id'], text=answer_text, parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=context_data['message_id'], reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))


@admin_private_router.callback_query(F.data.startswith('delete_order'))
async def delete_selected_order(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.admin_idle_timer[callback.message.from_user.id] = 0

    callback_data = callback.data.split()
    id_order, date_order = int(callback_data[1]), datetime.strptime(callback_data[2], '%Y-%m-%d')

    if await admin_orm.cancel_order_with_id(session, id_order) == 'success': answer_text = '☑️ Выбранная запись отменена'
    else: 
        answer_text = 'Ошибка при отмене записи, админ уже в курсе (сукабля)' ##################### Добавить отправку отчета МНЕ
        await bot.send_message(
        chat_id=2136465129, 
        text=f"Ошибка при отмене записи {callback.from_user.id}")
    await get_admin_day_timetable(callback.message, state, bot, session, date_order, answer_text)
    await state.clear()



