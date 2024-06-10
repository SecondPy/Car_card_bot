import asyncio
import os
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot, Dispatcher, types
from database import orm_admin_query as admin_orm
from datetime import datetime, date, time, timedelta
#from dotenv import find_dotenv, load_dotenv
#load_dotenv(find_dotenv())



from handlers.user_private import client_private_router  # импорт роутера
from handlers.admin_private import admin_private_router

from database.engine import create_db, drop_db, session_maker
# from common.bot_cmds_list import private - для кнопки menu
from middlewares.db import DataBaseSession


from database.orm_admin_query import get_inline_message_id
from const_values import ABBREVIATED_WEEK_DAYS
from kbds.callback import get_callback_btns


ALLOWED_UPDATES = ['message, edited_message']

# 6191676658:AAG65LUtn8c7kvpmUNbiuvC-8Qmi9J9H24o - avtoservice_34
# 6506294620:AAGbP2Bi8VKLSC0UCobcFRKOE3SnxUVD2-k чайная
# 2102094577:AAHKWVSqsvbU86GC0yvH2CGIZ7s9xY_kp2c - carcardbot
bot = Bot(token='2102094577:AAHKWVSqsvbU86GC0yvH2CGIZ7s9xY_kp2c')
bot.admins_list = [] # 2136465129 - мой 9965109078

bot.admin_idle_timer, bot.client_idle_timer = dict(), dict()
bot.main_admin_menu_ids, bot.main_client_menu_ids = dict(), dict()

dp = Dispatcher()

dp.include_routers(admin_private_router, client_private_router)


async def update_menu():
    session, finished_orders_count, admins_menu = await admin_orm.finish_old_orders()
    try:
        delete = await bot.send_message(2136465129, text=f'Автоматически завершено {finished_orders_count} ордеров')
        calendar_data = {}
        today = date.today()
        current_date = today - timedelta(days=(today.weekday()))
        last_date = current_date + timedelta(days=28)
        text = '\n⬇️ Актуальное расписание'
        if orders_data := await admin_orm.orm_get_order_with_date(session, datetime.combine(today, time(0, 0))):
            text += '🗓 Наряды на сегодня:\n-'
            text += '\n-'.join([(f"<b>{order.begins.hour}:00</b> {order.description}") for order in orders_data])
        else: text += '🗓 Наряды на сегодня отсутствуют\n'
        for _ in range(7):
            calendar_data[f'{ABBREVIATED_WEEK_DAYS[_]}'] = f"|{ABBREVIATED_WEEK_DAYS[_]}|"
        while current_date < last_date:
            if current_date < today or current_date > (today+timedelta(days=28)):
                calendar_data[f"get_day {current_date.strftime('%Y-%m-%d')}"] = f"{current_date.strftime('%d.%m')}"
            else:
                orders_data = await admin_orm.orm_get_order_with_date(session, current_date)
                if orders_data and 'Выходной' not in {order.description for order in orders_data}:
                    if current_date != today or datetime.now().hour < 9: hours = 0
                    else: hours = (datetime.now().hour - 9) * 2
                    for order in orders_data:
                        hours += (order.ends - order.begins).total_seconds() // 3600
                    if hours < 4: inline_smile = '🟢'
                    elif hours < 12: inline_smile = '🟡'
                    elif hours < 17: inline_smile = '🟠'
                    else: inline_smile = '🔴'
                    text_button = f"{current_date.strftime('%d')}{inline_smile}"
                elif orders_data and 'Выходной' in {order.description for order in orders_data}:
                    text_button = f"{current_date.strftime('%d')}🥳"
                else: text_button = f"{current_date.strftime('%d')}🟢"
                calendar_data[f"get_day {current_date.strftime('%Y-%m-%d')}"] = text_button
            current_date += timedelta(days=1)
        calendar_data[f"flip_month {today} back"] = f'⏪ назад'
        calendar_data[f"flip_month {today} next"] = f'вперед ⏩'
        for admin_menu in admins_menu:
            await bot.edit_message_text(text=text, chat_id=admin_menu.tg_id, message_id=admin_menu.inline_message_id, parse_mode=ParseMode.HTML)
            await bot.edit_message_reply_markup(chat_id=admin_menu.tg_id, message_id=admin_menu.inline_message_id, reply_markup=get_callback_btns(btns=calendar_data, sizes=[7]))
        await asyncio.sleep(600)
        await delete.delete()
        await session.close()
    except Exception as e:
        await bot.send_message(2136465129, text=f'Ошибка при выполнении кода: \n{e}')
        try: await session.close()
        except: pass


async def start_utils() -> list[int]:
    date_finished_orders = datetime(1900, 1, 1).date()
    answered_hour = 0
    while True:
        await asyncio.sleep(5)
        if bot.admin_idle_timer:
            for id_admin in bot.admin_idle_timer.keys():
                bot.admin_idle_timer[id_admin] += 5
        if bot.client_idle_timer:
            for id_client in bot.client_idle_timer.keys():
                bot.client_idle_timer[id_client] += 5
        if date_finished_orders < date.today():
            now_time = datetime.now().time()
            if now_time > time(0, 15): date_finished_orders = date.today()
            if now_time > time(0, 10) and now_time < time(0, 15) and len(bot.admin_idle_timer.keys())==len([bot.admin_idle_timer[key] for key in bot.admin_idle_timer.keys() if bot.admin_idle_timer[key] > 30]):
               await update_menu()
               date_finished_orders = date.today()
        
        now = datetime.now()
        
        if 7 < now.hour < 18 and now.minute == 0 and now.second < 15 and answered_hour != now.hour:
            if nearest_orders := await admin_orm.get_nearest_orders(date_time=datetime.combine(now.date(), time(now.hour, 0))):
                admin_ids = await admin_orm.get_admins_ids(session=None)
                btn, sizes = dict(), [1]
                btn['delete_selected_message'] = '✅ Ок'
                answered_hour = now.hour
                await bot.send_message(2136465129, text=f"{' '.join([order for order in nearest_orders])}")
                for order in nearest_orders:
                    for id in admin_ids:
                        await bot.send_message(
                            chat_id=id,
                            text=f'Через час прибудет машина: {order.description}\nДолжна быть готова к {order.ends.hour}:00',
                            reply_markup=get_callback_btns(btns=btn, sizes=sizes)
                        )

        
async def on_startup(bot):

    run_param = False
    if run_param:
        await drop_db()

    await create_db()


async def main() -> None:
    print('Bot has been planted ...')
    dp.startup.register(on_startup)
    #dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    await bot.delete_webhook(drop_pending_updates=True)
    #await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    loop = asyncio.get_event_loop()
    loop.create_task(start_utils())
    #await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)
    
    
    

asyncio.run(main())