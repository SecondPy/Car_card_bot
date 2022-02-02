from aiogram import types, Dispatcher
from create_bot import dp, bot
from keyboards import kb_client, kb_reg, kb_permission, kb_cancel_state, kb_cancel_or_skip
from data_base import sqlite_db
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
import datetime as dt
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import IDFilter
from aiogram.dispatcher.filters.state import State, StatesGroup

WELCOME_MESSAGE = \
'Здравствуйте! 👋\n\nБот для поддержки клиентов автосервиса 700SHIN в г.Волжском (переулок Складской, 3а).\n\n\
С его помощью Вы можете просматривать свои случаи ремонтов, следить за прохождением ТО и быстро записываться на сервис.\n\n\
Чтобы авторизоваться, нажмите на кнопку внизу \n⬇️⬇️⬇️'

SUCCESSFUL_REGISTRATION_MESSAGE = 'Успешная регистрация.\n\nРазрешить боту присылать напоминания о подходе ТО? (Всегда можно поменять)'

MY_CAR_MESSAGE = 'В базе за Вами числится автомобиль {}\n{}'
MY_RECOMMENDATIONS_MESSAGE = 'Последние рекоммендации:\n{}'
SEND_ORDER_MESSAGE = 'Клиент желает записаться!\nТел: {}\nАвто: {}\nVIN: {}'

ID_STATE = {}
STRANGERS_PHONES = {}

class FSMAdmin(StatesGroup):
    get_permission = State()
    change_photo = State()

    get_order = State()

async def state_cancel_handler(message: types.Message, state: FSMContext):
    global ID_STATE
    client_id = str(message.from_user.id)
    if ID_STATE[client_id] == 'change_photo':
        await bot.send_message(478032098, f'Клиент {client_id} отменил загрузку фото авто')
    current_state = await state.get_state()
    if ID_STATE[client_id] != 'get_order_from_stranger':
        ID_STATE[client_id] = False
        if current_state is None:
            await message.reply('Ок', reply_markup=kb_client)
        else:
            await state.finish()
            await message.reply('Oк', reply_markup=kb_client)
    else:
        ID_STATE[client_id] = False
        if current_state is None:
            await message.reply('Ок', reply_markup=kb_reg)
        else:
            await state.finish()
            await message.reply('Oк', reply_markup=kb_reg)
    
async def command_start(message : types.Message):
    try:
        user = message.from_user.id 
        check_user = await sqlite_db.check_user(user)
        if check_user == []:
            await bot.send_message(user, WELCOME_MESSAGE, reply_markup=kb_reg)
            await message.delete()
        else:
            await bot.send_message(message.from_user.id, 'Бот жив и готов к работе', reply_markup=kb_client)
    except Exception as e:
        await message.reply('Общение с ботом через ЛС, напишите ему: \nhttp://t.me/Car_Card_bot')
        print(e)

async def handler(contact: types.Contact):
    user_id = contact['contact']['user_id']
    user_phone = contact['contact']['phone_number'].replace('+', '')[1:]
    try:
        if await sqlite_db.client_registration(user_id, user_phone) == 'Nope':
            await bot.send_message(user_id, 'Вашего номера телефона пока нет в истории обслуживания СТО', reply_markup=InlineKeyboardMarkup().\
                add(InlineKeyboardButton('Записаться на сервис/шиномонтаж/схождение', callback_data=f'get_order {user_phone}')))
        else: 
            await bot.send_message(user_id, SUCCESSFUL_REGISTRATION_MESSAGE, reply_markup=kb_permission)
            global ID_STATE
            await FSMAdmin.get_permission.set()
            ID_STATE[user_id] = 'get_permission'
        await contact.delete()
    except Exception as e:
        print(e)
        await bot.send_message(user_id, 'Произошла ошибка. Обратитесь к менеджерам в магазине.')

async def get_permission(message: types.Message, state: FSMContext):
    global ID_STATE
    if ID_STATE[message.from_user.id] == 'get_permission':
        if message.text == 'Разрешить':
            permission = True
        elif message.text == 'Запретить':
            permission = False
        id = message.from_user.id
        await sqlite_db.load_permission(id, permission)
        await message.reply('Ок.\nДля управления ботом используйте кнопки внизу', reply_markup=kb_client)
        await state.finish()
        ID_STATE[message.from_user.id] = False

async def change_photo(message: types.Message, state: FSMContext):
    global ID_STATE
    client_id = str(message.from_user.id)
    if ID_STATE[client_id] == 'change_photo':
        photo = message.photo[0].file_id
        await sqlite_db.sql_load_new_car_photo_2(client_id, photo)
        car = await sqlite_db.find_client_car(client_id)
        if car[2] == True:
            permission = '✅ Уведомления о ТО включены'
        else: permission = '❌ Уведомления о ТО выключены'
        await bot.send_photo(client_id, car[1], MY_CAR_MESSAGE.format(car[0], permission), reply_markup=InlineKeyboardMarkup().\
            add(InlineKeyboardButton('✉️ Вкл\выкл уведомления', callback_data=f'change_permission {client_id}')).\
                add(InlineKeyboardButton('📷 Загрузить другое фото', callback_data = f'change_photo {client_id}')))
        ID_STATE['client_id'] = False
        await state.finish()
        await message.delete()
        await bot.send_message(client_id, 'Новое фото успешно загружено 👌', reply_markup=kb_client)
        await bot.send_photo(478032098, photo, f'Клиент {client_id} успешно загрузил новое фото', )

async def get_order(message: types.Message, state: FSMContext):
    global ID_STATE
    client_id = str(message.from_user.id)
    if ID_STATE[client_id] == 'get_order':
        client_car = await sqlite_db.find_client_car(client_id)
        if message.text.lower() == 'пропустить':
            await bot.send_message(-631794921, SEND_ORDER_MESSAGE.format(client_car[4], client_car[0], client_car[3]))
        else:
            await bot.send_message(-631794921, f'{SEND_ORDER_MESSAGE.format(client_car[4], client_car[0], client_car[3])} и комментарием:\n{message.text}')
        await message.reply('Запрос отправлен. Менеджеры свяжутся с вами в ближайшее время', reply_markup=kb_client)
            
    elif ID_STATE[client_id] == 'get_order_from_stranger':
        if message.text.lower() == 'пропустить':
            await bot.send_message(-631794921, f'Клиент c номером телефона: {STRANGERS_PHONES[client_id]}\n(не зарегистрирован в базе) желает записаться')
        else:
            await bot.send_message(-631794921, f'Клиент c номером телефона: {STRANGERS_PHONES[client_id]}\n(не зарегистрирован в базе) желает записаться\nC комментарием:\n"{message.text}"')
        await message.reply('Запрос отправлен. Менеджеры свяжутся с вами в ближайшее время', reply_markup=kb_reg)
        
    await state.finish()
    ID_STATE['client_id'] = False
            

async def answer(message : types.Message):
    client_id = message.from_user.id
    text = message.text
    cl_phone = await sqlite_db.find_client_car(client_id) # Короче, обращения к базе это настоящий венегрет. Этот процесс надо будет переделывать
    cl_phone = cl_phone[4]
    with open('log.txt', 'a+') as log:
        log.write(f'{dt.datetime.now().strftime("%d-%m-%Y %H:%M")}, {client_id}, Телефон: {cl_phone}, {text}\n')
        await bot.send_message(478032098, f'{dt.datetime.now().strftime("%d-%m-%Y %H:%M")}, {client_id}, Телефон: {cl_phone}, "{text}"')
    if message.text.lower() == 'мой автомобиль':
        car = await sqlite_db.find_client_car(client_id)
        if car[2] == True:
            permission = '✅ Уведомления о ТО включены'
        else: permission = '❌ Уведомления о ТО выключены'
        await bot.send_photo(client_id, car[1], MY_CAR_MESSAGE.format(car[0], permission), reply_markup=InlineKeyboardMarkup().\
            add(InlineKeyboardButton('📩 Вкл\выкл уведомления', callback_data=f'change_permission {client_id}')).\
                add(InlineKeyboardButton('📷 Загрузить другое фото', callback_data = f'change_photo {client_id}')))

    elif message.text.lower() == 'рекоммендации':
        recommendations = await sqlite_db.sql_select_recommendations(client_id)
        if 'следующему ремонту нет' in recommendations:
            await bot.send_message(client_id, recommendations)
        else:
            await bot.send_message(client_id, MY_RECOMMENDATIONS_MESSAGE.format(recommendations))

    elif 'записаться' in message.text.lower():
        await message.reply('Напишите в чат повод для записи (напр "шиномонтаж") или жмите "пропустить" если хотели бы обсудить с менеджером напрямую', reply_markup=kb_cancel_or_skip)
        await FSMAdmin.get_order.set()
        global ID_STATE
        ID_STATE[str(client_id)] = 'get_order'

    elif message.text.lower() == 'мои заказ-наряды':
        try:
            orders = await sqlite_db.sql_select_orders(client_id)
            inline_kb = InlineKeyboardMarkup(resize_keyboard=True)
            for o in orders:
                inline_kb = inline_kb.add(InlineKeyboardButton(f'🧾 {o[5]} на сумму: {o[4]} рублей.\n{o[6]}', callback_data=f'show {o[0]}'))
            await bot.send_message(client_id, 'Выберите заказ-наряд из списка:', reply_markup=inline_kb)
        except Exception as e:
            await message.reply('На ваш автомобиль ни одного заказ-наряда не выполнено')
            print(e)


async def change_permission(callback_query: types.CallbackQuery):
    global ID_STATE
    client_id = callback_query.data.replace('change_permission ', '')
    permission = await sqlite_db.find_client_car(client_id)
    permission = permission[2]
    if permission == True:
        await sqlite_db.load_permission(client_id, False)
        await callback_query.answer('Уведомления выключены')
        await bot.send_message(478032098, f'Клиент {client_id} выключил уведомления')
    else:
        await callback_query.answer('Уведомления включены')
        await sqlite_db.load_permission(client_id, True)
        await bot.send_message(478032098, f'Клиент {client_id} включил уведомления')
    car = await sqlite_db.find_client_car(client_id)
    if car[2] == True:
        permission = '✅ Уведомления о ТО включены'
    else: permission = '❌ Уведомления о ТО выключены'
    await bot.send_photo(client_id, car[1], MY_CAR_MESSAGE.format(car[0], permission), reply_markup=InlineKeyboardMarkup().\
            add(InlineKeyboardButton('📩 Вкл\выкл уведомления', callback_data=f'change_permission {client_id}')).\
                add(InlineKeyboardButton('📷 Загрузить другое фото', callback_data = f'change_photo {client_id}')))

async def change_photo_query(callback_query: types.CallbackQuery):
    global ID_STATE
    id_client = callback_query.data.replace('change_photo ', '')
    ID_STATE[id_client] = 'change_photo'
    await FSMAdmin.change_photo.set()
    await bot.send_message(id_client, 'Загрузите новое фото или нажмите "Выход"', reply_markup=kb_cancel_state)
    await bot.send_message(478032098, f'Клиент {id_client} загружает новое фото')


async def show_callback_run(callback_query: types.CallbackQuery):
    order_data = await sqlite_db.sql_find_check(callback_query.data.replace('show ', ''))
    order_check = order_data[0][0]
    user_id = order_data[0][1]
    await callback_query.answer(show_alert=False)
    await bot.send_photo(user_id, order_check)

async def get_order_from_stranger(callback_query: types.CallbackQuery):
    global ID_STATE, STRANGERS_PHONES
    client_id = str(callback_query['from']['id'])
    await callback_query.answer(show_alert=False)
    await FSMAdmin.get_order.set()
    await bot.send_message(client_id, 'Назовите повод для записи (напр "шиномонтаж")', reply_markup=kb_cancel_or_skip)
    ID_STATE[client_id] = 'get_order_from_stranger'
    STRANGERS_PHONES[client_id] = callback_query.data.replace('get_order ', '')

def register_handlers_client(dp : Dispatcher):
    dp.register_message_handler(command_start, commands = ['start', 'help'])
    dp.register_message_handler(handler, content_types=['contact'])
    dp.register_message_handler(answer, content_types=['text'])
    dp.register_message_handler(state_cancel_handler, state="*", commands='Выход')
    dp.register_message_handler(get_permission, state=FSMAdmin.get_permission)
    dp.register_message_handler(change_photo, content_types=['photo'], state=FSMAdmin.change_photo)
    dp.register_message_handler(get_order, state=FSMAdmin.get_order)

    dp.register_callback_query_handler(show_callback_run, lambda x: x.data and x.data.startswith('show '))
    dp.register_callback_query_handler(change_permission, lambda x: x.data and x.data.startswith('change_permission '))
    dp.register_callback_query_handler(change_photo_query, lambda x: x.data and x.data.startswith('change_photo '))
    dp.register_callback_query_handler(get_order_from_stranger, lambda x: x.data and x.data.startswith('get_order '))