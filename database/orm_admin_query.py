from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import sessionmaker
from database.engine import session_maker

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession


from database.models import AdminIds, AdminMenu, Client, ClientRequest, Order


async def orm_add_inline_message_id(session: AsyncSession, tg_id: int, inline_message_id: str):
    query = select(AdminMenu.inline_message_id).where(tg_id==tg_id)
    result = await session.execute(query)
    id = result.scalar()
    if not id:
        obj = AdminMenu(
            tg_id=tg_id,
            inline_message_id=inline_message_id
        )
        session.add(obj)
        await session.commit()
    elif id != inline_message_id:
        query = update(AdminMenu).where(AdminMenu.tg_id==tg_id).values(inline_message_id=inline_message_id)
        result = await session.execute(query)
        await session.commit()

async def get_inline_message_id(session: AsyncSession, tg_id: int):
    print(f'\n\nsession = {session}\n\n')
    query = select(AdminMenu.inline_message_id).where(tg_id==tg_id)
    result = await session.execute(query)
    id = result.scalar()
    return id

async def get_client_request_with_id(session: AsyncSession, id_request: int):
    query = select(ClientRequest).where(ClientRequest.id_request==id_request)
    result = await session.execute(query)
    return result.scalar()

async def add_new_client_with_phone(session: AsyncSession, phone: str):
    obj = Client(phone_client=phone)
    session.add(obj)
    await session.commit()
    query = select(Client).where(Client.phone_client==phone)
    result = await session.execute(query)
    return result.scalar()

async def add_phone_to_client_with_tg_id(session: AsyncSession, tg_id: int, phone: str):
    query = select(Client.id_client).where(Client.phone_client==phone)
    result = await session.execute(query)
    id_client = result.scalar()
    if id_client:
        query = select(Client.id_client).where(Client.id_telegram==tg_id)
        result = await session.execute(query)
        old_id = result.scalar()
        if old_id:
            query = update(Client).where(Client.id_client==old_id).values(id_telegram=tg_id*1000)
            result = await session.execute(query)
            await session.commit()
        query = update(Client).where(Client.id_client==id_client).values(id_telegram=tg_id)
        result = await session.execute(query)
        await session.commit()
    else:
        query = select(Client.id_client).where(Client.id_telegram==tg_id)
        result = await session.execute(query)
        id_client = result.scalar()
        query = update(Client).where(Client.id_client==id_client).values(phone_client=phone)
        result = await session.execute(query)
        await session.commit()
    query = select(Client).where(Client.phone_client==phone)
    result = await session.execute(query)
    return result.scalar()



async def get_client_with_phone(session: AsyncSession, phone: str):
    query = select(Client).where(Client.phone_client==phone)
    result = await session.execute(query)
    client = result.scalar()
    return client


async def get_client_with_id(session: AsyncSession, id_client: int):
    query = select(Client).where(Client.id_client==id_client)
    result = await session.execute(query)
    client = result.scalar()
    return client


async def get_client_with_tg_id(session: AsyncSession, tg_client: int):
    query = select(Client).where(Client.id_telegram==tg_client)
    result = await session.execute(query)
    client = result.scalar()
    return client


async def orm_get_order_with_date(session: AsyncSession, date: datetime, status='actual') -> str:
    query = select(Order).where(Order.status==status).filter(Order.begins>=date, Order.begins<date+timedelta(days=1)).order_by(Order.begins)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_order_with_date_and_place(session: AsyncSession, ask_date: datetime, place: int, status='actual') -> str:
    query = select(Order).where(
        (Order.begins==ask_date),
        (Order.status==status),
        (Order.place==place)
    )
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_order_with_date_time(session: AsyncSession, date_time_order: datetime, status='actual'):
    if not session: session = session_maker()
    query = select(Order).where(Order.status==status).filter(Order.begins<=date_time_order, Order.ends>date_time_order)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_order_with_date_time_and_place(session: AsyncSession, date_time_order: datetime, place: int, status='actual'):
    query = select(Order).where(Order.status==status, Order.place==place).filter(Order.begins<=date_time_order, Order.ends>date_time_order)
    result = await session.execute(query)
    return result.scalars().all()


async def get_orders_with_client_id(session: AsyncSession, id_client: int, status='finished'):
    query = select(Order).where(Order.id_client==id_client, Order.status==status)
    result = await session.execute(query)
    return result.scalars().all()

async def orm_get_order_with_id(session: AsyncSession, id_order: int):
    query = select(Order).where(Order.id_order==id_order)
    result = await session.execute(query)
    return result.scalar()


async def cancel_order_with_id(session: AsyncSession, id_order: int) -> str:
    query = update(Order).where(Order.id_order==id_order).values(status='cancelled')
    await session.execute(query)
    await session.commit()
    return 'success'


async def orm_make_weekend(session:AsyncSession, date):
    begins, ends = datetime.combine(date, time(9, 0)), datetime.combine(date, time(18, 0))
    order = Order(
        begins=begins,
        ends=ends,
        place=1,
        description='Выходной',
        status='actual'
    )
    session.add(order)
    await session.commit()
    query = select(Order.status).where(Order.begins==date)
    result = await session.execute(query)
    order_status = result.scalar()
    if order_status == 'actual':
        return 'success'
    else:
        return 'error - orm_make_weekend не удалось проверить успех записи выходного в бд'
    

async def orm_unmake_weekend(session:AsyncSession, id_order):
    query = update(Order).where(Order.id_order==id_order).values(status='cancelled')
    await session.execute(query)
    await session.commit()
    return 'success'

async def push_new_order(session:AsyncSession, order_data):
    
    # две затычки из-за кривого кода, которые я обазательно когда-нибудь исправлю
    if 'client' in order_data: id_client = order_data['client'].id_client 
    else: id_client = 0
    today = datetime.today().date()
    if order_data['begins'].date() < today: status = 'finished'
    else: status = 'actual'
    
    order = Order(
        begins=order_data['begins'],
        ends=order_data['ends'],
        place=order_data['place'],
        id_car=0,
        description=order_data['description'],
        status=status,
        id_client=id_client,
        by_admin=True
    )
    
    session.add(order)
    await session.commit()
    return 'success'


async def change_inline_service(session: AsyncSession, id_order: int, services: list):
    query = update(Order).where(Order.id_order==id_order).values(
        oil_m = services[0],
        grm = services[1],
        oil_kpp = services[2],
        spark_plugs = services[3],
        power_steer = services[4],
        coolant = services[5],
        break_fluid = services[6],
        fuel_filter = services[7]
    )
    await session.execute(query)
    await session.commit()



async def push_new_advice(session: AsyncSession, id_order: int, advice: str):
    query = update(Order).where(Order.id_order==id_order).values(advice=advice)
    await session.execute(query)
    await session.commit()

async def push_new_mileage(session: AsyncSession, id_order: int, mileage: str):
    query = update(Order).where(Order.id_order==id_order).values(mileage=mileage)
    await session.execute(query)
    await session.commit()

async def push_new_phone(session: AsyncSession, id_order: int, phone: str):
    query = select(Client).where(Client.phone_client==phone)
    result = await session.execute(query)
    client = result.scalar()
    if not client: client = await add_new_client_with_phone(session, phone)
    query = update(Order).where(Order.id_order==id_order).values(id_client=client.id_client)
    await session.execute(query)
    await session.commit()
    return client

async def push_new_description(session: AsyncSession, id_order :int, description: str):
    query = update(Order).where(Order.id_order==id_order).values(description=description)
    await session.execute(query)
    await session.commit()


async def finish_order_with_id(session: AsyncSession, id_order: int):
    query = update(Order).where(Order.id_order==id_order).values(status='finished')
    await session.execute(query)
    await session.commit()


async def add_new_photo(session: AsyncSession, id_order, photo_id):
    query = select(Order.repair_photo).where(Order.id_order==id_order)
    result = await session.execute(query)
    photo_data = result.scalar()
    if photo_data and photo_id not in photo_data: photo_data = str(photo_data) + f' {photo_id}'
    elif not photo_data: photo_data = photo_id
    query = update(Order).where(Order.id_order==id_order).values(repair_photo=photo_data)
    await session.execute(query)
    await session.commit()


async def delete_repair_photo(session: AsyncSession, id_order: int, clice_id_photo: str):
    query = select(Order.repair_photo).where(Order.id_order==id_order)
    result = await session.execute(query)
    photo_data = result.scalar()
    list_photo = photo_data.split(' ')
    if len(list_photo) == 1:
        query = update(Order).where(Order.id_order==id_order).values(repair_photo='')
    else:
        photo_to_delete = [photo_id for photo_id in list_photo if clice_id_photo in photo_id]
        if len(photo_to_delete) == 1:
            list_photo.remove(photo_to_delete[0])
            query = update(Order).where(Order.id_order==id_order).values(repair_photo=' '.join(list_photo))
        else: return 'error'
    await session.execute(query)
    await session.commit()
    return 'success'


async def change_order_duration(session:AsyncSession, context_data: dict):
    query = update(Order).where(Order.id_order==context_data['order_data'].id_order).values(ends=context_data['order_data'].ends)
    await session.execute(query)
    await session.commit()



async def add_admin_id(session: AsyncSession, tg_id: int):
    query = select(AdminIds.tg_id).where(AdminIds.tg_id==tg_id)
    result = await session.execute(query)
    id = result.scalar()
    if not id:
        obj = AdminIds(tg_id=tg_id)
        session.add(obj)
        await session.commit()


async def get_admins_ids(session: AsyncSession):
    if not session: session = session_maker()
    query = select(AdminIds.tg_id)
    result = await session.execute(query)
    ids = result.scalars().all()
    return ids

async def finish_old_orders():
    session = session_maker()
    today = datetime.combine(date.today(), time(0, 0))
    query = select(Order).where(Order.status=='actual').filter(Order.begins>today, Order.begins<today+timedelta(days=1))
    result = await session.execute(query)
    orders_to_finish = result.scalars().all()
    query = select(AdminMenu)
    result = await session.execute(query)
    admins_menu = result.scalars().all()
    if len(orders_to_finish) > 0:
        for order in orders_to_finish:
            query = update(Order).where(Order.id_order==order.id_order).values(status='finished')
            await session.execute(query)
            await session.commit()
    return session, len(orders_to_finish), admins_menu


async def get_nearest_orders(date_time: datetime):
    session = session_maker()
    query = select(Order).where(Order.begins==date_time+timedelta(hours=1), Order.status=='actual')
    result = await session.execute(query)
    return result.scalars().all()