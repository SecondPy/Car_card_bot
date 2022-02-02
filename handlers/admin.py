from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import IDFilter
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram import types, Dispatcher
from create_bot import dp, bot
from aiogram.dispatcher.filters import Text
from data_base import sqlite_db
from keyboards import admin_kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
import datetime as dt
import string


ID = {}


TUPLE_SERVICES = (
    'Масло моторное',
    'Топливный фильтр',
    'Свечи зажигания',
    'Антифриз',
    'ГРМ',
    'Масло кпп',
    'Тормозная жидкость'
    )

TUPLE_ORDER = (
    'Пробег',
    'Стоимость',
    'Дату',
    'Описание',
    'Рекоммендации'
)

SET_SERVICES = set()
for s in TUPLE_SERVICES:
    SET_SERVICES.add(s)

OLD_ORDER = {}

INPUT_ERROR = False

EDIT_STATE_TRIGGER = {}

CLIENT_EDIT = ['Телефон', 'Гос номер', 'Марка авто', 'Модель авто', 'VIN', 'Фото авто']

class FSMAdmin(StatesGroup):
    phone = State()
    car_licence_plate = State()
    car_brand = State()
    car_model = State()
    vin = State()
    first_recommendations = State()
    car_pic = State()

    #Для ввода заказ-наряда
    user_id = State()
    mileage = State()
    cash_total = State()
    date = State()
    description = State()
    recommendations_after_service = State()
    check = State()
    stop_or_continue = State()
    service_details = State()

    edit_client_card = State()
    load_new_client_card = State()
    load_new_car_photo = State()

    edit_order = State()
    edit_order_end = State()
    choice_services = State()
    change_service = State()
    change_order_check = State()


async def make_changes_command(message: types.Message):
    print('make_changes_command', message.from_user.id)
    global ID, EDIT_STATE_TRIGGER
    EDIT_STATE_TRIGGER[message.from_user.id] = 0
    ID[message.from_user.id] = 'make_changes_command'
    await bot.send_message(message.from_user.id, 'Жду команд...', reply_markup=admin_kb.add_or_edit_buttons)
    await message.delete()


async def cm_add_client_start(message : types.Message):
    try:
        if ID[message.from_user.id] == 'make_changes_command': # проверка на администратора
            await FSMAdmin.phone.set()
            await message.reply('Введите номер телефона клиента в любом формате', reply_markup=admin_kb.cancel_button)
    except: pass

async def cancel_handler(message: types.Message, state: FSMContext):
    try:
        if ID[message.from_user.id] == 'make_changes_command':
            current_state = await state.get_state()
            global EDIT_STATE_TRIGGER
            if current_state is None:
                await message.reply('ок', reply_markup=admin_kb.add_or_edit_buttons)
            else:
                await state.finish()
                await message.reply('OK', reply_markup=admin_kb.add_or_edit_buttons)
            EDIT_STATE_TRIGGER[message.from_user.id] = 0
    except: pass

    
async def load_phone(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['id'] = None  #Затычка для удобной записи словаря в бд
            data['user_id'] = None  #Затычка для удобной записи словаря в бд
            if len(message.text) > 10:
                phone = message.text.translate(str.maketrans('', '', string.punctuation)).replace(' ', '')
                data['phone'] = phone[len(phone)-10:]
            else:
                data['phone'] = message.text
        await FSMAdmin.next()
        await message.reply('Теперь введи гос номер, напирмер х001хх34')

async def load_car_licence_plate(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['car_licence_plate'] = message.text
        await FSMAdmin.next()
        await message.reply('Марка авто?')

async def load_car_brand(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['car_brand'] = message.text
        await FSMAdmin.next()
        await message.reply('Модель авто?')

async def load_car_model(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['car_model'] = message.text
        await FSMAdmin.next()
        await message.reply('VIN')

async def load_vin(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['VIN'] = message.text.upper()
        await FSMAdmin.next()
        await message.reply('Введи рекоммендации для следующего ремонта, если нет - жми "пропустить"', \
                             reply_markup=admin_kb.skip_or_cancel_button)


async def load_recommendations(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            if 'пропустить' in message.text.lower():
                data['recommendations'] = 'Рекоммендаций к следующему ремонту нет'
            else: data['recommendations'] = message.text
        await FSMAdmin.next()
        await message.reply('Фото авто. Можно с интернетов')


async def load_car_pic(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['photo'] = message.photo[0].file_id
            data['responsibility'] = message.from_user.id
            data['permission'] = False
            await FSMAdmin.next()
        await message.reply('Клиент добавлен!', reply_markup=admin_kb.add_or_edit_buttons)
        await sqlite_db.sql_add_user(state)
        await state.finish()



async def cm_add_order_start(message: types.Message):
    try:
        if ID[message.from_user.id] == 'make_changes_command':
            await FSMAdmin.user_id.set()
            await message.reply('Введите номер телефона клиента в любом формате', reply_markup=admin_kb.cancel_button)
            if 'карточку' in message.text:
                global EDIT_STATE_TRIGGER
                EDIT_STATE_TRIGGER[message.from_user.id] = 1  #Состояние для старта изменений карточки
            elif 'Редактировать_наряд' in message.text:
                EDIT_STATE_TRIGGER[message.from_user.id] = 2  #Состояние для внесения изменений в наряд
    except: pass


async def check_phone(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        try:
            if len(message.text) > 10:
                phone = message.text.translate(str.maketrans('', '', string.punctuation)).replace(' ', '')
                phone = phone[len(phone)-10:]
                print(phone)
            else:
                phone = message.text
            user_id = await sqlite_db.find_user_id(phone)
            if user_id:
                async with state.proxy() as data:
                    if EDIT_STATE_TRIGGER[message.from_user.id] == 1:  #Меняем карточку клиента
                        client_data = await sqlite_db.sql_read_client(phone)
                        c_d = client_data[0]
                        await message.reply(f'Что будем менять?\n\nТелефон: {c_d[2]}\nГос номер: {c_d[3]}\nМарка авто: {c_d[4]}\nМодель авто: {c_d[5]}\n'
                                            f'VIN: {c_d[6]}', reply_markup=admin_kb.edit_client)
                        await bot.send_photo(message.from_user.id, c_d[8])
                        data['old_client_card'] = c_d
                        await FSMAdmin.edit_client_card.set()

                    elif EDIT_STATE_TRIGGER[message.from_user.id] == 2:  # Меняем наряд клиента
                        client_orders_data = await sqlite_db.sql_read_orders(phone)
                        await message.reply('Какой будем менять?')
                        for order in client_orders_data:
                            i = 0 # итерация по значению кортежа TUPLE_SERVICES
                            values = ''
                            for value in order[9:16]:
                                if value:
                                    values += TUPLE_SERVICES[i] + ', '
                                    i += 1
                                else: i += 1
                            await bot.send_photo(message.from_user.id, order[8], f'От {order[5]} на сумму {order[4]}\nОПИСАНИЕ: {order[6]}\n'
                                                                                 f'РЕКОММЕНДАЦИИ: {order[7]}\nМЕНЯЛОСЬ: {values[:len(values)-2]}')
                            await bot.send_message(message.from_user.id, text='^^^', reply_markup=InlineKeyboardMarkup().\
                                                   add(InlineKeyboardButton(f'Изменить наряд', callback_data=f'Изменить наряд {order[0]}')))
                        await state.finish()
                    
                    else:
                        user_id = await sqlite_db.find_user_id(phone)
                        data['id'] = None
                        data['user_id'] = user_id[0][0]
                        data['phone'] = phone
                        await FSMAdmin.next()
                        await message.reply('Пробег на момент ремонта в км (только цифры, например: 125900)')
            else:
                await message.reply('Нет такого телефона в базе клиентов! Давай сначала')
                await FSMAdmin.user_id.set()
        
                    
        except Exception as e:
            await state.finish()
            await message.reply('Нет такого телефона в базе клиентов! Давай сначала')
            print('ОООШИИБОЧКАА', e)
            await FSMAdmin.user_id.set()
        
        

async def load_mileage(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['mileage'] = message.text
        await FSMAdmin.next()
        await message.reply('Сумма заказ-наряда с запчастями и работой (только цифры, например: 29900')

async def load_cash_total(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['cash_total'] = message.text
        await FSMAdmin.next()
        await message.reply('Теперь дата. Если сегодня - нажми кнопку, иначе в формате: день-мес-год', reply_markup=admin_kb.b_today_or_cancel)

async def load_date(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            if 'сегодня' in message.text.lower():
                data['date'] = dt.date.today().strftime("%d-%m-%Y")
            else: data['date'] = message.text
        await FSMAdmin.next()
        await message.reply('Краткое описание своими словами. Например: замена сайлентблоков передних рычагов', reply_markup=admin_kb.cancel_button)

async def load_description(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['description'] = message.text
        await FSMAdmin.next()
        await message.reply('Рекоммендации клиенту:', reply_markup=admin_kb.skip_or_cancel_button)

async def load_recommendations_after_service(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            if 'пропустить' in message.text.lower():
                data['recommendations'] = ' Рекоммендаций к следующему ремонту нет'
            else:
                data['recommendations'] = message.text
        await FSMAdmin.next()
        await message.reply('Загрузи скриншот заказ-наряда', reply_markup=types.ReplyKeyboardRemove())

async def load_check(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            data['check'] = message.photo[0].file_id
        await FSMAdmin.next()
        await message.reply('Менялось что-нибудь связанное с ТО? (масла, тормозуха, антифриз, грм, фильтра или свечи?)', reply_markup=admin_kb.yes_or_no_buttons)

async def stop_or_continue(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            for service in TUPLE_SERVICES:
                data[service] = False
            data['admin_id'] = message.from_user.id

        if 'Да' in message.text or INPUT_ERROR:
            await FSMAdmin.next()
            await message.reply('Используй кнопки чтобы выбрать что менялось. ', reply_markup=admin_kb.service_buttons)
        elif 'Нет' in message.text:
            await FSMAdmin.next()
            await message.reply('Запись добавлена', reply_markup=admin_kb.add_or_edit_buttons) 
            await sqlite_db.sql_add_order(state)
            await state.finish()
            
async def load_service_details(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        global INPUT_ERROR
        async with state.proxy() as data:
            text = message.text
            if text in SET_SERVICES:
                data[text] = True
                await message.reply('ок')
            elif text == 'Готово':
                await FSMAdmin.next()
                await message.reply('Запись добавлена', reply_markup=admin_kb.add_or_edit_buttons)
                await sqlite_db.sql_add_order(state)
                await state.finish()
                INPUT_ERROR = False



async def edit_client_card(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        global CLIENT_EDIT
        try:
            async with state.proxy() as data:
                if 'Готово' in message.text:
                    await message.reply('Ок', reply_markup=admin_kb.add_or_edit_buttons)
                    await state.finish()
                    global EDIT_STATE_TRIGGER
                    EDIT_STATE_TRIGGER[message.from_user.id] = 0
                elif message.text in CLIENT_EDIT and message.text != 'Фото авто':
                    value_num = CLIENT_EDIT.index(message.text) + 2
                    data['selected_value'] = value_num
                    if value_num < 7:
                        await message.reply('На что будем менять?')
                        await FSMAdmin.load_new_client_card.set()
                elif message.text == 'Фото авто':
                    await message.reply('Загрузи новое фото авто')
                    data['id'] = data['old_client_card'][0]
                    await FSMAdmin.load_new_car_photo.set()

        except Exception as e:
            print(f'Ошибка в edit_client_card - {e}, пользователь - {message.from_user.id}, текст - {message.text}, {dt.datetime.now()}')
            await message.reply('Неизвесная команда')

async def load_new_client_card(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            old_data = data['old_client_card']
            new_data = []
            i = 0
            for old_value in old_data:
                if data['selected_value'] != i:
                    new_data.append(old_data[i])
                    i += 1
                else:
                    new_data.append(message.text)
                    i += 1
            new_data[9] = message.from_user.id
            await sqlite_db.sql_add_user(new_data)
            c_d = await sqlite_db.sql_read_client(old_data[2])
            data['old_client_card'] = tuple(new_data)
            await bot.send_message(message.from_user.id, 'Изменено успешно. Что-нибудь еще? если нет - жми готово')
            await FSMAdmin.edit_client_card.set()

async def load_new_car_photo(message: types.Message, state: FSMContext):

     if ID[message.from_user.id] == 'make_changes_command':
         async with state.proxy() as data:
             data['photo'] = message.photo[0].file_id
             await sqlite_db.sql_load_new_car_photo(data['id'], data['photo'])
             await bot.send_message(message.from_user.id, 'Фото загружено. Что-нибудь еще? если нет - жми готово')
             await FSMAdmin.edit_client_card.set()


async def edit_order_start(callback_query: types.CallbackQuery):
        await FSMAdmin.edit_order.set()
        order_id = callback_query.data.replace('Изменить наряд ', '')
        old_order = await sqlite_db.sql_read_orders(None, order_id)
        admin_id = callback_query['from']['id']
        await callback_query.answer(show_alert=False)
        await bot.send_message(admin_id, 'Что будем менять?', reply_markup=admin_kb.edit_order)
        global OLD_ORDER
        OLD_ORDER[admin_id] = []
        for value in old_order:
            OLD_ORDER[admin_id].append(value)
        OLD_ORDER[admin_id][16] = admin_id
        
async def back_to_order_edit(message: types.Message, state: FSMContext):
    try:
        if ID[message.from_user.id] == 'make_changes_command':
            current_state = await state.get_state()
            if current_state is None:
                return 
            await message.reply('ок', reply_markup=admin_kb.edit_order)
            await FSMAdmin.edit_order.set()
    except: pass


async def edit_order(message: types.Message, state: FSMContext):
    global OLD_ORDER, EDIT_STATE_TRIGGER
    if ID[message.from_user.id] == 'make_changes_command':
        if message.text in TUPLE_ORDER:
            async with state.proxy() as data:
                i = 3
                for value in TUPLE_ORDER:
                    if message.text == value:
                        data['value_order'] = i
                        await message.reply('На что будем менять?') 
                    else: i += 1
                await FSMAdmin.edit_order_end.set()

        elif message.text == 'ТО (масла, фильтра...)':
            await message.reply('Что будем изменять?', reply_markup=admin_kb.edit_service_buttons)
            await FSMAdmin.choice_services.set()

        elif 'Фото наряда' in message.text:
            await message.reply('Загрузи новое фото наряда', reply_markup=admin_kb.back_or_cancel)
            await FSMAdmin.change_order_check.set()
    
        elif 'Готово' in message.text:
                await sqlite_db.edit_order(OLD_ORDER[message.from_user.id])
                await message.reply('Запись изменена', reply_markup=admin_kb.add_or_edit_buttons)
                await state.finish()
                OLD_ORDER[message.from_user.id] = []
                EDIT_STATE_TRIGGER[message.from_user.id] = 0

async def edit_order_end(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        global OLD_ORDER
        async with state.proxy() as data:
            OLD_ORDER[message.from_user.id][data['value_order']] = message.text
            await message.reply('Изменено. Что-нибудь еще? если нет - жми готово', reply_markup=admin_kb.edit_order)
            await FSMAdmin.edit_order.set()


async def choice_services(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        global OLD_ORDER, EDIT_STATE_TRIGGER
        if message.text in TUPLE_SERVICES:
            i = 9
            for service in TUPLE_SERVICES:
                if service == message.text:
                    async with state.proxy() as data:
                        data['service'] = i
                else: i += 1
            await message.reply('Меняли?', reply_markup=admin_kb.yes_or_no_buttons)
            await FSMAdmin.change_service.set()

        elif 'Предыдущее меню' in message.text:
            await message.reply('ок', reply_markup=admin_kb.edit_order)
            await FSMAdmin.edit_order.set()
        
        elif 'Готово' in message.text:
            OLD_ORDER[message.from_user.id][16] = message.from_user.id
            await sqlite_db.edit_order(OLD_ORDER[message.from_user.id])
            await message.reply('Запись изменена', reply_markup=admin_kb.add_or_edit_buttons)
            await state.finish()
            OLD_ORDER[message.from_user.id] = []
            EDIT_STATE_TRIGGER[message.from_user.id] = 0        
            
        

async def change_service(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        async with state.proxy() as data:
            global OLD_ORDER
            if 'Да' in message.text:
                OLD_ORDER[message.from_user.id][data['service']] = True
            elif 'Нет' in message.text:
                OLD_ORDER[message.from_user.id][data['service']] = False
            await message.reply('Изменено. Что-нибудь еще? если нет - жми готово', reply_markup=admin_kb.edit_service_buttons)
            await FSMAdmin.choice_services.set()

async def change_order_check(message: types.Message, state: FSMContext):
    if ID[message.from_user.id] == 'make_changes_command':
        global OLD_ORDER
        OLD_ORDER[message.from_user.id][8] = message.photo[0].file_id
        await message.reply('Фото изменено. Что-нибудь еще?', reply_markup=admin_kb.edit_order)
        await FSMAdmin.edit_order.set()


#Регистриуем хэндлеры
def register_handlers_admin(dp : Dispatcher):
    dp.register_message_handler(make_changes_command, commands=['am_i_admin'], is_chat_admin=True)
    dp.register_message_handler(cm_add_client_start, commands=['Создать_карточку_клиента'], state=None)
    dp.register_message_handler(cancel_handler, state="*", commands='Отмена')
    dp.register_message_handler(back_to_order_edit, state=FSMAdmin.change_order_check, commands='Назад')
    dp.register_message_handler(load_phone, content_types=['text'], state=FSMAdmin.phone)
    dp.register_message_handler(load_car_licence_plate, state=FSMAdmin.car_licence_plate)
    dp.register_message_handler(load_car_brand, state=FSMAdmin.car_brand)
    dp.register_message_handler(load_car_model, state=FSMAdmin.car_model)
    dp.register_message_handler(load_vin, state=FSMAdmin.vin)
    dp.register_message_handler(load_recommendations, state=FSMAdmin.first_recommendations)
    dp.register_message_handler(load_car_pic, content_types=['photo'], state=FSMAdmin.car_pic)
    dp.register_message_handler(cm_add_order_start, commands=['Добавить_заказ_наряд', 'Редактировать_карточку_клиента', 'Редактировать_наряд_клиента'], state=None)
    dp.register_message_handler(check_phone, content_types=['text'], state=FSMAdmin.user_id)
    dp.register_message_handler(load_mileage, state=FSMAdmin.mileage)
    dp.register_message_handler(load_cash_total, state=FSMAdmin.cash_total)
    dp.register_message_handler(load_date, state=FSMAdmin.date)
    dp.register_message_handler(load_description, state=FSMAdmin.description)
    dp.register_message_handler(load_recommendations_after_service, state=FSMAdmin.recommendations_after_service)
    dp.register_message_handler(load_check, content_types=['photo'], state=FSMAdmin.check)
    dp.register_message_handler(stop_or_continue, state=FSMAdmin.stop_or_continue)
    dp.register_message_handler(load_service_details, state=FSMAdmin.service_details)
    dp.register_message_handler(edit_client_card, state=FSMAdmin.edit_client_card)
    dp.register_message_handler(load_new_client_card, state=FSMAdmin.load_new_client_card)
    dp.register_message_handler(load_new_car_photo, content_types=['photo'], state=FSMAdmin.load_new_car_photo)
    

    dp.register_callback_query_handler(edit_order_start, lambda x: x.data and x.data.startswith('Изменить наряд '))
    dp.register_message_handler(edit_order, state=FSMAdmin.edit_order)
    dp.register_message_handler(edit_order_end, state=FSMAdmin.edit_order_end)
    dp.register_message_handler(change_order_check, content_types=['photo'], state=FSMAdmin.change_order_check)

    dp.register_message_handler(choice_services, state=FSMAdmin.choice_services)
    dp.register_message_handler(change_service, state=FSMAdmin.change_service)

