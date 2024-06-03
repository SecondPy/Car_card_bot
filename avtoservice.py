import asyncio
import os
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

ALLOWED_UPDATES = ['message, edited_message']

# 6191676658:AAG65LUtn8c7kvpmUNbiuvC-8Qmi9J9H24o - avtoservice_34
# 6506294620:AAGbP2Bi8VKLSC0UCobcFRKOE3SnxUVD2-k чайная
bot = Bot(token='6191676658:AAG65LUtn8c7kvpmUNbiuvC-8Qmi9J9H24o')
bot.admins_list = [] # 2136465129 - мой 9965109078

bot.admin_idle_timer, bot.client_idle_timer = dict(), dict()
bot.main_admin_menu_ids, bot.main_client_menu_ids = dict(), dict()

dp = Dispatcher()

dp.include_routers(admin_private_router, client_private_router)


async def start_utils() -> list[int]:
    date_finished_orders = datetime(1900, 1, 1).date()
    while True:
        await asyncio.sleep(5)
        if bot.admin_idle_timer:
            for id_admin in bot.admin_idle_timer.keys():
                bot.admin_idle_timer[id_admin] += 1
        if bot.client_idle_timer:
            for id_client in bot.client_idle_timer.keys():
                bot.client_idle_timer[id_client] += 1
        try:
            if date_finished_orders < date.today():
               now = datetime.now().time()
               if now > time(0, 15): date_finished_orders = date.today()
               if now > time(0, 10) and now < time(0, 15) and len(bot.admin_idle_timer.keys())==len([bot.admin_idle_timer[key] for key in bot.admin_idle_timer.keys() if bot.admin_idle_timer[key] > 30]):
                   result = await admin_orm.finish_old_orders()
                   date_finished_orders = date.today()
                   delete = await bot.send_message(2136465129, text=f'Автоматически завершено {result} ордеров')
                   await asyncio.sleep(600)
                   await bot.delete_message(delete.message_id)
        except Exception as e: await bot.send_message(2136465129, text=f'Ошибка при выполнении кода: \n{e}')
        
        
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
