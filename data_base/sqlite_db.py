import sqlite3 as sq
from create_bot import dp, bot
import datetime as dt


def sql_start():
    global base, cur
    base = sq.connect('Car_Cards.db')
    cur = base.cursor()
    if base:
        print('Data base connected OK!')

async def load_permission(id, permission):
    cur.execute('UPDATE users SET permission_to_prompt = ? WHERE user_id = ?', (permission, id))
    base.commit()

async def check_user(user):
    cur.execute('SELECT user_phone FROM users WHERE user_id == ?', (user,))
    phone_from_user_id = cur.fetchall()
    return phone_from_user_id

async def find_user_id(phone, need_id=False):
    try:
        if need_id == False:
            cur.execute ('SELECT user_id FROM users WHERE user_phone = ?', (phone,))
            id_from_user_phone = cur.fetchall()
            return id_from_user_phone
        else:
            cur.execute ('SELECT user_phone FROM users WHERE user_phone = ?', (phone,))
            return cur.fetchall()
    except: return None

async def find_client_car(client_id):
    cur.execute('SELECT car_brand, car_model, car_pic, permission_to_prompt, VIN, user_phone FROM users WHERE user_id = ?', (client_id,))
    car_data = cur.fetchall()[0]
    client_car = str(car_data[0]) + ' ' + str(car_data[1])
    return client_car, car_data[2], car_data[3], car_data[4], car_data[5]

async def client_registration(id, phone):
    print(phone)
    cur.execute('UPDATE users SET user_id = ? WHERE user_phone = ?', (id, phone))
    base.commit()
    cur.execute('UPDATE orders SET user_id = ? WHERE user_phone = ?',(id, phone))
    base.commit()
    cur.execute('SELECT user_phone FROM users WHERE user_id = ?', (id,))
    e = cur.fetchall()
    print(e)
    if e == []:
        return 'Nope'

async def sql_add_user(data):
    try:
        async with data.proxy() as data:
            cur.execute('INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', tuple(data.values()))
            base.commit()
    except:
        cur.execute('SELECT user_phone FROM users WHERE id = ?', (data[0],))
        old_phone = cur.fetchall()[0][0]
        if old_phone != data[2]:
            cur.execute('UPDATE orders SET user_phone = ? WHERE user_phone = ?', (data[2], old_phone))
            base.commit
        set_data = data[2:]
        set_data.append(data[0])
        cur.execute('''UPDATE users SET 
                       user_phone = ?,
                       car_licence_plate = ?,
                       car_brand = ?,
                       car_model = ?,
                       VIN = ?,
                       recommendations = ?,
                       car_pic = ?,
                       responsible = ?,
                       permission_to_prompt = ?
                       WHERE id = ? ''', tuple(set_data, ))
        base.commit()

async def sql_add_order(data):
    async with data.proxy() as data:
        data_tuple = tuple(data.values())
        try:
            cur.execute('INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data_tuple)
            base.commit()
            cur.execute('UPDATE users SET recommendations = ? WHERE user_phone = ?', (data_tuple[7], data_tuple[2]))
            base.commit()
        except Exception as e:
            print('ошибка при записи заказ-наряда в базу: ', e,  'Время -', dt.date.today().strftime("%d-%m-%Y"))

async def edit_order(data):
    print(data)
    id = data.pop(0)
    user_id = data.pop(0)
    phone = data.pop(0)
    data.append(id)
    cur.execute('''UPDATE orders SET
                   mileage = ?,
                   cash_total = ?,
                   date = ?,
                   description = ?,
                   recommendations = ?,
                   order_check = ?,
                   engine_oil_service = ?,
                   fuel_filter_service = ?,
                   spark_plug_service = ?,
                   coolant_service = ?,
                   camshaft_service = ?,
                   gear_box_service = ?,
                   brake_fluid_service = ?,
                   responsible = ?
                   WHERE id = ?''', tuple(data,))
    base.commit()
    

async def sql_select_recommendations(user_id):
    cur.execute('SELECT recommendations from users WHERE user_id = ?', (user_id,))
    return cur.fetchall()[0][0]

async def sql_select_orders(client_id):  #для клиентской части
    cur.execute('SELECT * FROM orders WHERE user_id = ?', (client_id,))
    return cur.fetchall()
async def sql_read_orders(phone, id=None):  # для админской части (редактирование ордеров)
    if id:
        cur.execute('SELECT * FROM orders WHERE id = ?', (id,))
        return cur.fetchall()[0]
    cur.execute('SELECT * FROM orders WHERE user_phone = ?', (phone,))
    return cur.fetchall()

async def sql_read_client(phone):
    for ret in cur.execute('SELECT * FROM users').fetchall():
        cur.execute('SELECT * from users WHERE user_phone = ?', (phone,))
        return cur.fetchall()

async def sql_load_new_car_photo_2(client_id, photo_id): #В клиентской части для загрузки клиентом своего фото. Пока так, потом исправлю..
    cur.execute('UPDATE users SET car_pic = ? WHERE user_id = ?', (photo_id, client_id))
    base.commit

async def sql_load_new_car_photo(client_id, photo_id): # По-хоршему надо будет объединить с верхней функцией
    cur.execute('UPDATE users SET car_pic = ? WHERE id = ?', (photo_id, client_id))
    base.commit

async def sql_read2():
    return cur.execute('SELECT * FROM ').fetchall()

async def sql_find_check(id_order):
    cur.execute('SELECT order_check, user_id FROM orders WHERE id = ?', (id_order,))
    data = cur.fetchall()
    return data

async def sql_delete_command(data):
    cur.execute('DELETE FROM menu WHERE name == ?', (data,))
    base.commit()