from datetime import date, datetime
import time as t
import random
import asyncio

from aiogram import Bot, F, types, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, or_f, StateFilter   #commanstart Обрабатывает только команду старт
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
#from database.models import Student
#from database.orm_admin_query import orm_add_product
from const_values import ABBREVIATED_WEEK_DAYS, ADMIN_GREETING, CLIENT_EMOJI, CLIENT_GREETING
from sqlalchemy.ext.asyncio import AsyncSession


from database import orm_client_query as client_orm
from database import orm_admin_query as admin_orm
from utils.client_start_menu import main_menu_client_constructor
from utils.find_phone import find_phone
from utils.datetime_formatter import DateFormatter
from filters.chat_types import ChatTypeFilter
from utils.client_main_menu import get_main_client_menu
from utils.client_day_timetable import get_client_day_timetable
from kbds.reply import get_keyboard
from kbds.callback import get_callback_btns
from utils.admin_main_menu import get_main_admin_menu
from utils.show_client_order import show_client_order


client_private_router = Router()
client_private_router.message.filter(ChatTypeFilter(['private']))


class SendOrder(StatesGroup):
    get_order_info = State()
    phone = State()


#async def main_menu_client_constructor(session: AsyncSession, tg_id: int) -> list:
#    text = f'🛢 Адрес <b>ОйлЦентр</b>: Волжский, пл. Труда, 4а.\n📱 Тел: +78443210102 (9:00-18:00)\n'
#    btns_data, sizes = dict(), list()
#    btns_data['header withoud_data'] = '⬇️ Выберите действие ⬇️'
#    sizes.append(1)
#    btns_data['get_client_calendar'] = '🔧 Записаться 🔧'
#    btns_data[f'get_client_history {tg_id}'] = '📜 История 📜'
#    sizes.append(2)
#    actual_orders = await client_orm.find_orders_with_tg_id(session=session, tg_id=tg_id, status='actual')
#    if actual_orders:
#        for order in actual_orders:
#            text += f"\n-👨🏼‍🏭Ждём Вас на обслуживание {DateFormatter(order.begins).message_format}"
#    else:
#        text += f'\n-👨🏼‍🏭 записей о предстоящем обслуживании не найдено'
#
#    return [text, btns_data, sizes]


@client_private_router.callback_query(StateFilter("*"), F.data.startswith('client_cancel'))
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession) -> None:
    bot.client_idle_timer[callback.message.from_user.id] = 0
    
    await state.clear()
    await callback.answer('👌 Отправка запроса отменена', show_alert=True)
    await callback.message.delete()


@client_private_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession, bot: Bot, state: FSMContext) -> None:
    await message.answer(CLIENT_GREETING)
    await message.delete()
    text, btns_data, sizes = await main_menu_client_constructor(session, message.from_user.id)
    main_message = await message.answer(text=text, reply_markup=get_callback_btns(btns=btns_data, sizes=sizes), parse_mode=ParseMode.HTML)
    await client_orm.add_inline_message_id(session, message.from_user.id, main_message.message_id)
    bot.main_client_menu_ids[message.from_user.id] = main_message.message_id
    await client_orm.add_client_with_tg_id(session, message.from_user.id)


@client_private_router.callback_query(F.data.startswith('main_menu_client'))
async def main_menu_client(callback: types.CallbackQuery, session: AsyncSession, bot: Bot, state: FSMContext):
    bot.client_idle_timer[callback.message.from_user.id] = 0

    text, btns_data, sizes = await main_menu_client_constructor(session, callback.from_user.id)
    await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id, text=text, parse_mode=ParseMode.HTML)
    await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))

@client_private_router.callback_query(F.data.startswith('get_client_calendar'))
async def get_client_calendar(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session=AsyncSession) -> None:
    bot.client_idle_timer[callback.message.from_user.id] = 0
    
    await get_main_client_menu(session=session, state=state, bot=bot, message=callback.message, trigger='button')


@client_private_router.callback_query(F.data.startswith('get_client_history'))
async def get_client_calendar(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session=AsyncSession) -> None:
    bot.client_idle_timer[callback.message.from_user.id] = 0
    

    client = await admin_orm.get_client_with_tg_id(session, callback.from_user.id)

    if client.phone_client:
        finished_orders = await client_orm.find_orders_with_tg_id(session=session, tg_id=callback.from_user.id, status='finished')

        if finished_orders and len(finished_orders) > 1:
            btns_data, sizes = dict(), list()
            for order in finished_orders:
                btns_data[f'get_client_order {order.id_order}'] = f'📝 от {order.begins}'
                sizes.append(1)

            btns_data[f"main_menu_client"] = '🏠 Вернуться в главное меню'
            sizes.append(1)
            await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id, text='Выберите наряд из приведенного списка ↩️')
            await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))

        elif finished_orders: await show_client_order(session, state, bot, callback.message, finished_orders[0], answer_text='В истории пока только 1 наряд')
        else: await callback.answer('💁‍♂️ В истории пока не отображено ни одного заказ-наряда', show_alert=True)
    
    else: 
        await callback.answer('🤷‍♂️ Кажется, Вы еще не привязали номер телефона. Не могу знать, чью историю Вам показать 🙃', show_alert=True, parseMode=ParseMode.HTML)

        message_to_delete = await bot.send_message(chat_id=callback.from_user.id, text='📲Поделиться телефоном можно кнопкой рядом с клавиатурой⬇️', reply_markup=get_keyboard('📲Поделиться телефоном', request_contact=0))

        messege_is_deleted = False
        while not messege_is_deleted:
            await asyncio.sleep(20)
            try:
                await message_to_delete.delete()
                messege_is_deleted = True
            except: messege_is_deleted = True

@client_private_router.message(F.contact)
async def get_contact(message: types.Message, bot: Bot, session: AsyncSession):
    bot.client_idle_timer[message.from_user.id] = 0
    
    client = await client_orm.find_client_with_tg_id(session, message.from_user.id)
    if not client.phone_client:
        message_contact_data = str(message.contact).split()
        user_phone = await find_phone(message_contact_data[0])
        result_commit = await admin_orm.add_phone_to_client_with_tg_id(session, message.from_user.id, user_phone)
        if result_commit.phone_client == user_phone:
            await message.delete()
            message_to_delete = await message.answer('🥳 Отлично! теперь Вы можете просматривать свою историю и отправлять запрос на запись в интерактивном календаре')
            text, btns_data, sizes = await main_menu_client_constructor(session, message.from_user.id)
            try: client_main_menu_id = bot.main_client_menu_ids[message.from_user.id]
            except: client_main_menu_id = await client_orm.get_inline_message_id(session, message.from_user.id)
            await bot.edit_message_text(chat_id=message.from_user.id, message_id=client_main_menu_id, text=text, parse_mode=ParseMode.HTML)
            await bot.edit_message_reply_markup(chat_id=message.from_user.id, message_id=client_main_menu_id, reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
            messege_is_deleted = False
            while not messege_is_deleted:
                await asyncio.sleep(20)
                try:
                    await bot.delete_message(chat_id=message.from_user.id, message_id=message_to_delete.message_id)
                    messege_is_deleted = True
                except: messege_is_deleted = True
    
    else: await message.delete()



@client_private_router.callback_query(F.data.startswith('get_client_order'))
async def get_client_calendar(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session=AsyncSession) -> None:
    bot.client_idle_timer[callback.message.from_user.id] = 0
    
    callback_data = callback.data.split()
    order = await client_orm.get_order_with_id(session, int(callback_data[1]))
    
    await show_client_order(session, state, bot, callback.message, order)


@client_private_router.callback_query(F.data.startswith('show_client_repair_photo'))
async def show_repair_photo(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.client_idle_timer[callback.message.from_user.id] = 0

    callback_data = callback.data.split()
    id_order = int(callback_data[1])
    count_images = int(callback_data[2])
    order_data = await admin_orm.orm_get_order_with_id(session, id_order)

    photo_messages_answer = []
    list_repair_photos = order_data.repair_photo.split()
    
    if count_images == 1: 
        message_answer = await callback.message.answer_photo(list_repair_photos[0])
        await callback.answer()
    else:
        btn_data = dict()
        btn_data[f'flip_photo {id_order} next 0'] = 'следующее ⏩'
        message_answer = await callback.message.answer_photo(list_repair_photos[0], reply_markup=get_callback_btns(btns=btn_data))
        await state.update_data(message_caption_id=message_answer.message_id)
        
    
    await state.update_data(showed_photos=photo_messages_answer)
    
    await asyncio.sleep(600)
    try:
        await bot.delete_message(callback.from_user.id, message_answer.message_id)
        text, btns_data, sizes = await main_menu_client_constructor(session, callback.from_user.id)
        await bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.message_id, text=text)
        await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=callback.message.message_id, reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
    except: pass

@client_private_router.callback_query(F.data.startswith('flip_photo'))
async def show_repair_photo(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession):
    bot.client_idle_timer[callback.message.from_user.id] = 0
    
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
            btn_data[f'flip_photo {id_order} back {current_num_photo}'] = '⏪ предыдущее'
            sizes.append(1)
        else:
            btn_data[f'flip_photo {id_order} back {current_num_photo}'] = '⏪ предыдущее'
            btn_data[f'flip_photo {id_order} next {current_num_photo}'] = 'следующее ⏩'
            sizes.append(2)
    elif type_flip == 'back':
        current_num_photo -= 1
        btn_data, sizes = dict(), list()
        if current_num_photo == 0:
            btn_data[f'flip_photo {id_order} next {current_num_photo}'] = 'следующее ⏩'
            sizes.append(1)
        else:
            btn_data[f'flip_photo {id_order} back {current_num_photo}'] = '⏪ предыдущее'
            btn_data[f'flip_photo {id_order} next {current_num_photo}'] = 'следующее ⏩'
            sizes.append(2)
    

    photo = types.InputMediaPhoto(media=order_images[current_num_photo])
    await bot.edit_message_media(media=photo, chat_id=callback.from_user.id, message_id=caption_id, reply_markup=get_callback_btns(btns=btn_data, sizes=sizes))
    
    photo_is_deleted = False
    while not photo_is_deleted:
        await asyncio.sleep(10)
        if bot.client_idle_timer[callback.message.from_user.id] > 9:
            try: 
                await bot.delete_message(chat_id=callback.from_user.id, message_id=caption_id)
                photo_is_deleted = True
                text, btns_data, sizes = await main_menu_client_constructor(session, callback.from_user.id)
                await bot.edit_message_text(chat_id=callback.from_user.id, message_id=bot.main_client_menu_ids[callback.from_user.id], text=text)
                await bot.edit_message_reply_markup(chat_id=callback.from_user.id, message_id=bot.main_client_menu_ids[callback.from_user.id], reply_markup=get_callback_btns(btns=btns_data, sizes=sizes))
            except: photo_is_deleted = True


@client_private_router.callback_query(F.data.startswith('get_client_day'))
async def get_client_calendar(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session=AsyncSession) -> None:

    bot.client_idle_timer[callback.message.from_user.id] = 0

    today = date.today()
    chosen_day = datetime.strptime(callback.data.split()[1], '%Y-%m-%d').date()
    if chosen_day < today:
        delete_message = await callback.message.reply(text='Дни из прошлого недоступны для просмотра')
        await asyncio.sleep(5)
        await bot.delete_message(chat_id=callback.from_user.id, message_id=delete_message.message_id)
    else: await get_client_day_timetable(callback.message, state, bot, session, chosen_day)


@client_private_router.callback_query(F.data.startswith('client_main_menu'))
async def get_client_daytimes(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session=AsyncSession) -> None:
    bot.client_idle_timer[callback.message.from_user.id] = 0
    
    await get_main_client_menu(session=session, state=state, bot=bot, message=callback.message, trigger='button')


@client_private_router.callback_query(F.data.startswith('get_client_time'))
async def get_client_daytimes(callback: types.CallbackQuery, state: FSMContext, bot: Bot, session=AsyncSession) -> None:
    bot.client_idle_timer[callback.message.from_user.id] = 0
    
    callback_data = callback.data.split()   # Получаем данные кнопки
    date_callback, time_callback = datetime.strptime(callback_data[1], '%Y-%m-%d'), callback_data[2] # Дата в формате DateTime, время в str
    message_date_callback = DateFormatter(date_callback).message_format    # форматируем дату в человекояз
    order_begins = datetime.strptime(callback_data[1], '%Y-%m-%d').date()
    client = await client_orm.find_client_with_tg_id(session, callback.from_user.id)
    if not client.phone_client: text_callback = '✍️Напишите, пожалуйста, одним сообщением:\n-🔧что нужно будет сделать, 🚗модель авто\n-📱свой номер телефона\n\nФормат письма свободный'
    else: text_callback = '✍️Напишите, пожалуйста, что нужно будет сделать'

    await callback.answer(text=text_callback, show_alert=True)
    btn_cancel = dict()
    btn_cancel['client_cancel'] = '❎ отменить запрос ❎'
    message_to_delete = await bot.send_message(
        callback.from_user.id, 
        text=f'-🤖 Выбрано {message_date_callback} {time_callback}:00\n{text_callback} ↩️',
        reply_markup=get_callback_btns(btns=btn_cancel)
    )

    await state.update_data(
        begins=order_begins,
        from_user_id=callback.from_user.id,
        date_message=message_date_callback,
        time=time_callback,
        message_delete=[message_to_delete.message_id, callback.message.message_id],
        client=client
    )
    
    await state.set_state(SendOrder.get_order_info)


@client_private_router.message(SendOrder.get_order_info, F.text)
async def get_order_info(message: types.Message, session: AsyncSession, bot: Bot, state: FSMContext):

    context_data = await state.get_data()

    if 'description' not in context_data:
        await state.update_data(description=message.text)
        context_data = await state.get_data()

    btns_data, sizes = dict(), list()
    request = await client_orm.add_client_request(session, message.from_user.id, context_data['date_message'], context_data['time'], message.text)
    
    if not context_data['client'].phone_client:
        is_phone = await find_phone(message.text)
        if is_phone:
            await admin_orm.add_phone_to_client_with_tg_id(session, message.from_user.id, is_phone)
            context_data['client'].phone_client = is_phone
        else: 
            message_delete = await message.answer(text=f"🤖Описание задачи есть: {context_data['description']}\n 🔎Но не нашел в нём номер телефона :(\nПожалуйста, напишите Ваш номер телефона, чтобы мы могли свзяться с Вами")
            await state.update_data(delete_message=context_data['message_delete'].append(message_delete.message_id))
    if context_data['client'].phone_client:
        client_message_data = f"+7{context_data['client'].phone_client}"
        client_messege_to_delete = await message.answer(text=f"✅ Запрос на {context_data['date_message']} {context_data['time']}:00 с описанием '{context_data['description']}' отправлен успешно. Как только его подтвердят, Вам будет отправлено уведомление👌")
        client_messege_id_to_delete = client_messege_to_delete.message_id
        btns_data[f"get_day {context_data['begins']} {request.id_request} {client_messege_id_to_delete}"] = '📝Открыть день и записать📝'
        admin_ids = await admin_orm.get_admins_ids(session)
        for id in admin_ids:
            await bot.send_message(
                chat_id=id, 
                text=f"-{random.choice(CLIENT_EMOJI)} Новый запрос на запись на {context_data['date_message']} {context_data['time']}:00\n-📱 Тел клиента: {client_message_data}\n-🗣 Запрос клиента: {context_data['description']}", 
                reply_markup=get_callback_btns(btns=btns_data, sizes=sizes)
            )
        await state.update_data(delete_message=context_data['message_delete'].append(message.message_id))
        context_data = await state.get_data()
        for message_to_delete in context_data['message_delete']:
            await bot.delete_message(chat_id=message.from_user.id, message_id=message_to_delete)
        
        text, btns_data, sizes = await main_menu_client_constructor(session, message.from_user.id)
        main_message = await message.answer(text=text, reply_markup=get_callback_btns(btns=btns_data, sizes=sizes), parse_mode=ParseMode.HTML)
        await client_orm.add_inline_message_id(session, message.from_user.id, main_message.message_id)
        bot.main_client_menu_ids[message.from_user.id] = main_message.message_id
        await state.clear()
        

@client_private_router.message(F.text)
async def edit_selected_order(message: types.Message, session: AsyncSession, state:FSMContext, bot: Bot):
    if message.text.lower() == 'балонка1':
        await message.delete()
        await admin_orm.add_admin_id(session, message.from_user.id)
        await message.answer(ADMIN_GREETING, parse_mode=ParseMode.HTML)
        await get_main_admin_menu(session=session, state=state, bot=bot, message=message, trigger='admin', text='🙌 Получены права <s>доми</s>администратора\n\n')
        try: await bot.delete_message(chat_id=message.from_user.id, message_id=bot.main_client_menu_ids[message.from_user.id])
        except: pass
        bot.admins_list.append(message.from_user.id)

