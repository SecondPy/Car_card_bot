from datetime import date, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


from database.models import AdminIds, Client, Order, ClientMenu, ClientRequest


async def orm_add_inline_message_id(session: AsyncSession, tg_id: int, inline_message_id: str):
    query = select(ClientMenu.inline_message_id).where(tg_id==tg_id)
    result = await session.execute(query)
    id = result.scalar()
    if not id:
        obj = ClientMenu(
            tg_id=tg_id,
            inline_message_id=inline_message_id
        )
        session.add(obj)
        await session.commit()
    elif id != inline_message_id:
        query = update(ClientMenu).where(ClientMenu.tg_id==tg_id).values(inline_message_id=inline_message_id)
        result = await session.execute(query)
        await session.commit()

    

async def add_client_with_tg_id(session: AsyncSession, tg_id: int):
    query = select(Client.id_client).where(Client.id_telegram==tg_id)
    result = await session.execute(query)
    id_client = result.scalar()
    if not id_client:
        obj = Client(id_telegram=tg_id)
        session.add(obj)
        await session.commit()


async def add_inline_message_id(session: AsyncSession, tg_id: int, inline_message_id: str):
    query = select(ClientMenu.inline_message_id).where(tg_id==tg_id)
    result = await session.execute(query)
    id = result.scalar()
    if not id:
        obj = ClientMenu(
            tg_id=tg_id,
            inline_message_id=inline_message_id
        )
        session.add(obj)
        await session.commit()
    elif id != inline_message_id:
        query = update(ClientMenu).where(ClientMenu.tg_id==tg_id).values(inline_message_id=inline_message_id)
        result = await session.execute(query)
        await session.commit()


async def get_inline_message_id(session: AsyncSession, tg_id: int):
    query = select(ClientMenu.inline_message_id).where(tg_id==tg_id)
    result = await session.execute(query)
    id = result.scalar()
    return id



async def orm_add_product(session: AsyncSession, data: dict):
    obj = Client(
        name=data['name'],
        phone = '9965109077',
        date_of_birth = '25-10-1993'
    )
    session.add(obj)
    await session.commit()


async def orm_get_order_with_date(session: AsyncSession, date: date):
    query = select(Order).where(
        (Order.begins==date),
        (Order.status=='actual')
    )
    result = await session.execute(query)
    return result.scalars().all()
    

async def find_client_with_tg_id(session: AsyncSession, tg_id: int):
    query = select(Client).where(Client.id_telegram==tg_id)
    result = await session.execute(query)
    return result.scalar()


async def find_orders_with_tg_id(session: AsyncSession, tg_id: int, status: str):
    query = select(Client.id_client).where(Client.id_telegram==tg_id)
    result = await session.execute(query)
    id_client = result.scalar()
    if id_client:
        query = select(Order).where(Order.id_client==id_client, Order.status==status)
        result = await session.execute(query)
        return result.scalars().all()
    else:
        obj = (Client(id_telegram=tg_id))
        session.add(obj)
        await session.commit()
        await find_orders_with_tg_id(session, tg_id, status)


async def add_client_request(session: AsyncSession, tg_id: int, date_message: str, time_start: str, message_request: str):
    obj = ClientRequest(
        id_telegram=tg_id,
        date_message=date_message,
        time_start=f'{time_start}:00',
        text_request=message_request
    )
    session.add(obj)
    await session.commit()
    query = select(ClientRequest).where(ClientRequest.id_telegram==tg_id, ClientRequest.text_request==message_request)
    result = await session.execute(query)
    requests = result.scalars().all()
    return requests[-1]



async def get_order_with_id(session: AsyncSession, id_order: int):
    query = select(Order).where(Order.id_order==id_order)
    result = await session.execute(query)
    return result.scalar()


#session, message.from_user.id, message_date, context_data['time'], message.text


#import sqlite3 as sq
#from create_bot import dp, bot
#from keyboards import inline_admin_kb
#import time
#from datetime import timedelta, date, datetime
#import pandas as pd
#from const_values import ADMIN_DAY_TIMES, ORDER_DETAILS
#
#
#ORDER_COLUMNS = [
#    'id_order', 'id_car', 'description', 'longterm', 'mileage', 'advice', 
#    'grm', 'oil_m', 'oil_kpp', 'oil_red', 'fuel_filter', 'coolant', 
#    'break_fluid', 'spark_plug', 'ended', 'sum', 'photo', 'id_client', 'create_date'
#]
#
#ORDER_DATA = [None] * 18
#
#DAYS = [None] * 15
#
#
## Подключение к БД
#def sql_start():
#    global base, cur
#    base = sq.connect('notes.db')
#    cur = base.cursor()
#    if base:
#        print('БД Avtosklad34_service подключена успешно')
#
## Читаем переданную дату в записи
#
#
#def chosen_day(date):
#    cur.execute('SELECT * FROM days WHERE date = ?', (date, ))
#    selected_data = cur.fetchall()
#    # Если такой день есть - возвращаем его данные, она же занятость, с нарядами
#    if len(selected_data) >= 1:
#        return selected_data[0]
#    # Иначе, если такой день еще не создан в БД, то создаем его. А затем возвращаем данные пустого дня
#    else:
#        cur.execute(
#            'INSERT INTO days VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (date, *DAYS))
#        base.commit()
#        return (date, *DAYS)
#
#
## Функция принимает номер телефона, новый номер телефона (для замены), и новый ник клиента.
## Создавёт новую запись о клиенте, если номера в бд не было
## Либо редактирует существующий, меняя номер телефона или псевдоним клиента
## В случае успешной работы возвращает обновленный кортеж данных клиента
## В случае ошибки, возвращает строку с описанием ошибки
#def edit_client(phone=None, phone_changed=None, nickname=None, id=None):
#    is_new_client = None
#    if phone:
#        cur.execute('SELECT * FROM clients WHERE client_phone = ?', (phone,))
#        is_phone_in_db = cur.fetchone()
#    else: is_phone_in_db = None
#    if id: cur.execute('SELECT * FROM clients WHERE id_client = ?', (id,))
#    elif is_phone_in_db and (not phone_changed):
#        if nickname:
#            cur.execute(
#                'UPDATE clients SET nickname = ? WHERE client_phone = ?', (nickname.lower(), phone))
#            base.commit()
#        cur.execute('SELECT * FROM clients WHERE client_phone = ?', (phone,))
#    elif is_phone_in_db and phone_changed:
#        cur.execute('SELECT * FROM clients WHERE client_phone = ?', (phone,))
#        is_changed_phone_in_db = cur.fetchone()[0]
#        if is_changed_phone_in_db:
#            cur.execute(
#                'SELECT nickname FROM clients WHERE client_phone = ?', (phone,))
#            new_nickname = nickname or cur.fetchone()[0] or 'отсутствует'
#            cur.execute('Update clients SET client_phone = ?, nickname = ? WHERE client_phone = ?',
#                        (phone_changed, new_nickname, phone))
#        else:
#            return (f'Не могу поменять на новый номер, так как он уже есть в базе. Псевдоним - {new_nickname}')
#    elif not phone and nickname:
#        cur.execute('SELECT * FROM clients WHERE nickname = ?', (nickname,))
#        client_data = cur.fetchone()
#        if not client_data: return (f'Такого псевдонима {nickname} пока нет в базе')
#        else:
#            client_data = list(client_data)
#            client_data.append('old_client')
#            return client_data
#    elif phone and nickname:
#        cur.execute('UPDATE clients SET nickname = ? WHERE client_phone = ?', (nickname, phone))
#        base.commit()
#        cur.execute('SELECT * FROM clients WHERE client_phone = ?', (phone,))
#    elif phone and (not is_phone_in_db):
#        cur.execute('INSERT INTO clients VALUES (?, ?, ?, ?)',
#                    (None, phone, None, nickname))
#        base.commit()
#        cur.execute('SELECT * FROM clients WHERE client_phone = ?', (phone,))
#        is_new_client = True
#    else:
#        return (f'Не определено действия функции под такой случай:\nphone: {phone}\nphone_Changed: {phone_changed}\nnickname: {nickname}')
#    base.commit()
#    if phone_changed:
#        cur.execute('SELECT * FROM clients WHERE client_phone = ?',
#                    (phone_changed, ))
#    elif phone:
#        cur.execute('SELECT * FROM clients WHERE client_phone = ?', (phone, ))
#    
#    try: client_data = list(cur.fetchone())
#    except TypeError: return 'Ошибка при получении данных с БД!'
#    
#    if is_new_client: client_data.append('new_client')
#    else: client_data.append('old_client')
#    return client_data
#
#
## Сюда будет спрашивать функция get_finish_order_main_data
#
#
#def get_client_data(id_client):
#    cur.execute('SELECT * FROM clients WHERE id_client = ?', (id_client, ))
#    client_data = cur.fetchone()
#    client_data = list(client_data) + ['old_client'] if client_data else (None*4, 'invalid')
#    return client_data   
#
#def get_client_orders(id_client):
#    cur.execute('SELECT * FROM orders WHERE id_client = ?', (id_client,))
#    return cur.fetchall()
#
#
#def get_client_phone(client_telegram_id):
#    cur.execute(
#        'SELECT client_phone FROM clients WHERE telegram_id = ?', (client_telegram_id,))
#    client_phone = cur.fetchone()
#    return client_phone
#
#
#def edit_client_nickname(id, nickname):
#    cur.execute('UPDATE clients SET nickname = ? WHERE id_client = ?',
#                (nickname.lower(), id))
#    base.commit()
#
#
#def edit_client_phone(phone, nickname, id):
#    cur.execute('UPDATE clients SET client_phone = ?, telegram_id = ?, nickname = ? WHERE id_client = ?',
#                (phone, None, nickname.lower(), int(id)))
#    base.commit()
#
#
## Переменная view_details в случае, если нужны кнопки для нескольких нарядов. id_order - будет списком. id_order должен быть Int
#def ask_for_order_data(id_order, view_details=False):
#    if view_details:
#        data = []
#        for id in id_order:
#            cur.execute(
#                'SELECT id_order, description, id_client, create_date FROM orders WHERE id_order = ?', (id, ))
#            data.append(cur.fetchone())
#        # Надо собрать максмально полную инфу для каждого ордера
#        order_and_client_data = []
#        # Так что для каждго ордера соберем инфу из таблицы с клиентами. Там могут быть номера телефонов и имена
#        for order in data:
#            order = list(order)
#            if order[2]:
#                cur.execute(
#                    'SELECT * FROM clients WHERE id_client = ?', (order[2], ))
#                client_data = cur.fetchall()[0]
#                client_data = [i for i in client_data[1::2] if i]
#                if client_data:
#                    # Удаляем id клиента, ибо он не нужен для вывода
#                    del order[2]
#                    order_and_client_data.append(order[:3]+list(client_data))
#            else:
#                # Удаляем id клиента, ибо он не нужен для вывода
#                del order[2]
#                order_and_client_data.append(order[:3])
#        return order_and_client_data
#    else:
#        cur.execute('SELECT * FROM orders WHERE id_order = ?', (int(id_order), ))
#        data = cur.fetchone()[1:]
#        return data
#
#
#def is_non_working_day(date):
#    day_data = chosen_day(date)
#    morning_orders = day_data[4]
#    if not morning_orders:
#        return False
#    else:
#        morning_orders = morning_orders.split()
#        for id_order in morning_orders:
#            order_data = ask_for_order_data(int(id_order))
#            if order_data[1] == 'Выходной' and order_data[13] not in {0, 1}:
#                return True
#    
#    
#
#def add_new_order(data, order_hours, is_longterm=None):
#    order_data = ORDER_DATA.copy()
#    print(f'data = {data}')
#    order_data[17] = datetime.today().strftime("%d-%m-%Y %H:%M")
#    if is_longterm:
#        order_data[2] = 1
#        # Долговременные наряды нет смысла держать в расписании.
#        order_hours.clear()
#    if 'description' in data:
#        order_data[1] = data['description']
#    if 'client' in data:
#        order_data[16] = data['client'].id
#    if 'id_car' in data:
#        order_data[0] = data['id_car']
#
#    cur.execute('INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
#                (None, *order_data))  # Добавляем пустой наряд в БД
#    base.commit()
#    # Нам понадобится сгенерированный автоинкрементом id только что созданного наряда
#    cur.execute('SELECT id_order FROM orders')
#    # Получим ID наряда в формате строки
#    str_id_order = str(max(cur.fetchall())[0])
#    for day, hours in order_hours.items():
#        for hour in hours:
#            hour = '_' + hour[:2]  # Форматирование для записи в БД
#            cur.execute(f'SELECT {hour} FROM days WHERE date = ?', (day,))
#            try:  # Если запись уже присутствует, то выполнится следующий блок кода:
#                order_on_time_start_ = cur.fetchall()[0][0]
#                # Произведем конкатенацию строк, чтобы в 1 ячейке фигурировало 2 наряда
#                order_on_time_start_ = order_on_time_start_ + ' ' + str_id_order
#                # Запишем итоговую строку в строку БД
#                cur.execute(
#                    f'UPDATE days SET {hour} = ? WHERE date = ?', (order_on_time_start_, day))
#            except:  # Если ячейка на это время свободная то выполнится следующая строка:
#                # Просто пишем строку в бд с последним добавленным ID наряда
#                cur.execute(
#                    f'UPDATE days SET {hour} = ? WHERE date = ?', (str_id_order, day))
#            base.commit()
#    cur.execute('SELECT id_order FROM orders')
#    return max([i[0] for i in cur.fetchall()])  # возвращаем id созданного наряда
#
#
#def get_description(id_order):
#    cur.execute(
#        f'SELECT description FROM orders WHERE id_order = ?', (id_order,))
#    description = cur.fetchone()
#    return description
#
#
#def edit_active_order(id, data):
#    cur.execute('''UPDATE orders SET
#                id_car = ?,
#                description = ?,
#                longterm = ?,
#                mileage = ?,
#                advice = ?,
#                grm = ?,
#                oil_m = ?,
#                oil_kpp = ?,
#                oil_red = ?,
#                fuel_filter = ?,
#                coolant = ?,
#                break_fluid = ?,
#                spark_plugs = ?,
#                ended = ?,
#                sum = ?,
#                photo = ?,
#                id_client = ?,
#                create_date = ?
#                WHERE id_order = ?''', (*data, id))
#    base.commit()
#
#
#def client_registration(client_telegram_id, client_phone):
#    cur.execute(
#        'SELECT client_phone FROM clients WHERE client_phone = ?', (client_phone, ))
#    if len(cur.fetchall()):
#        cur.execute('UPDATE clients SET telegram_id = ? WHERE client_phone = ?',
#                    (client_telegram_id, client_phone))
#    else:
#        cur.execute('INSERT INTO clients VALUES (?, ?, ?, ?) ',
#                    (None, client_phone, client_telegram_id, 'отсутствует'))
#    base.commit()
#
## Вызывает только функция history_client из файла client.py
#def client_history_by_tg_id(telegram_id_client):
#    cur.execute('SELECT id_client FROM clients WHERE telegram_id = ?', (telegram_id_client,))
#    id_client = cur.fetchone()[0]
#    cur.execute('SELECT * FROM orders WHERE id_client = ? AND ended = ?', (id_client, 1))
#    data = cur.fetchall()
#    return data
#
#def client_orders_by_db_id(id_client):
#    cur.execute('SELECT * FROM orders WHERE id_client = ? AND ended = ?', (id_client, 1))
#    data = cur.fetchall()
#    return data
#
#def client_cars_by_db_id(id_client):
#    cur.execute('SELECT * FROM cars WHERE car_status IS TRUE AND id_client = ?', (id_client,))
#    client_garage = cur.fetchall()
#    return client_garage
#
#def find_active_orders_by_tg_id(telegram_id_client):
#    cur.execute('SELECT id_client FROM clients WHERE telegram_id = ?', (telegram_id_client,))
#    id_client = cur.fetchone()[0]
#    cur.execute('SELECT * FROM orders WHERE id_client = ? AND ended IS NULL', (id_client,))
#    data = cur.fetchall()
#    client_orders_df = pd.DataFrame(data, columns=ORDER_COLUMNS)
#    client_orders_df['create_date'] = pd.to_datetime(client_orders_df['create_date'], format='%d-%m-%Y %H:%M')
#    return tuple(client_orders_df.values.tolist())
#
#
#def get_date_time_order(id_order):
#    query = 'SELECT * FROM days'
#    df_days = pd.read_sql_query(query, base)
#    goal_days = df_days[df_days.applymap(lambda x: str(id_order) in x.split() if isinstance(x, str) else False).any(axis=1)]
#    for row in goal_days.itertuples(index=False):
#        for index, column in enumerate(tuple(row)):
#            if column:
#                if str(id_order) in column:
#                    return [row[0], ADMIN_DAY_TIMES[index-1], id_order]
#                
#
#def find_service_details(id_client, id_car=None):
#    if not id_car:
#        cur.execute('SELECT * FROM orders WHERE id_client = ?', (id_client,))
#    else:
#        cur.execute('SELECT * FROM orders WHERE id_client = ? AND id_car = ?', (id_client, id_car))
#    client_orders = cur.fetchall()
#    client_orders_df = pd.DataFrame(client_orders, columns=ORDER_COLUMNS)
#    client_service_data = []
#    for index, column in enumerate(ORDER_COLUMNS[6:14]):
#        column_services_df = client_orders_df[client_orders_df[column]==1]
#        if not column_services_df.empty:
#            actual_line_id_service = column_services_df['id_order'].max()
#            actual_data_column_df = column_services_df[column_services_df['id_order']==actual_line_id_service]
#            actual_service_list = actual_data_column_df.values.tolist()[0]
#            actual_service_list[18] = get_date_time_order(int(actual_service_list[0]))[0]
#            actual_service_list = [actual_service_list[0], actual_service_list[4], actual_service_list[18]]
#            actual_service_list.append(ORDER_DETAILS[index])
#            client_service_data.append(actual_service_list)
#    set_orders_id = set([i[0] for i in client_service_data])
#    actual_client_service_data = []
#    for id in set_orders_id:
#        order_services = [i[3] for i in client_service_data if i[0] == id]
#        for order in client_service_data:
#            if order[0] == id:
#                order_services = order[:3] + order_services
#                break
#        actual_client_service_data.append(order_services)
#    return actual_client_service_data
#            
#            
#
#def add_client_car(id_client, car_model, car_vin_number=None):
#    cur.execute('INSERT INTO cars VALUES (?, ?, ?, ?, ?, ?)', (None, id_client, car_model, None, car_vin_number, True))
#    base.commit()
#    cur.execute('SELECT * FROM cars WHERE id_client = ? AND car_model = ?', (id_client, car_model))
#    car_data = cur.fetchone()
#    return car_data
#
#def get_client_car_data(id_car):
#    cur.execute('SELECT * FROM cars WHERE id_car = ?', (id_car,))
#    car_data = list(cur.fetchone())
#    print(car_data)
#    return car_data
#
#def edit_client_car(car_id, car_model, car_vin):
#    cur.execute('UPDATE cars SET car_model = ?, car_VIN = ? WHERE id_car = ?', (car_model, car_vin, car_id))
#    base.commit
#    
#def del_car(car_id):
#    cur.execute('UPDATE cars SET car_status = FALSE WHERE id_car = ?', (car_id,))
#    base.commit()
#
#def add_notice(telegram_id_client, id_order, datetime_order, datetime_notice):
#    cur.execute('INSERT INTO notices VALUES (?, ?, ?, ?, ?, ?)', (None, False, telegram_id_client, id_order, datetime_order, datetime_notice))
#    base.commit()
#    return 'Success!'
#
#def get_notices_data():
#    cur.execute('SELECT * FROM notices WHERE status IS FALSE')
#    unsended_notices_data = cur.fetchall()
#    return unsended_notices_data
#
#def get_notice_data(id_order):
#    cur.execute('SELECT * FROM notices WHERE id_order = ?', (int(id_order),))
#    notice_data = cur.fetchone()
#    return notice_data
#
#def edit_notice_data(id_notice, datetime_notice):
#    cur.execute('UPDATE notices SET datetime_notice = ?, status = FALSE WHERE id_notice = ?', (datetime_notice, int(id_notice)))
#    base.commit()
#
#def end_notice(id_notice):
#    cur.execute('UPDATE notices SET status = ? WHERE id_notice = ?', (True, int(id_notice)))
#    base.commit()
#
#
#
#def finish_old_orders():
#    cur.execute('SELECT * FROM days WHERE NOT date = ?', ('2024-03-09',))
#    data = cur.fetchall()
#    orders = []
#    for day in data:
#        print(day[0])
#        if len(day[0]) > 4 and datetime.today() > (datetime.strptime(day[0], '%Y-%m-%d')):
#            for order in day[1:]:
#                if order != None:
#                    orders += order.split()
#    
#    orders = list({int(i) for i in orders})
#    for order in orders:
#        cur.execute('UPDATE orders SET ended = ? WHERE id_order = ? AND ended IS NULL', (1, order))
#        base.commit()
#    return 'Проверяй'
#        
#sql_start()